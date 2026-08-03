import logging
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.config import settings
from app.graph.state import PRReviewState
from app.schemas import SecurityReviewDecision
from app.tools.github_tool import fetch_pr_diff, post_github_comment
from app.tools.jira_tool import fetch_jira_requirements
from app.tools.rag_tool import retrieve_security_guidelines

logger = logging.getLogger("GraphNodes")

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.1,  
    max_retries=2
)

structured_llm = llm.with_structured_output(SecurityReviewDecision)

REVIEW_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert Senior DevOps & Application Security Architect.
Your job is to review a GitHub Pull Request diff against Jira acceptance criteria and internal security guidelines.

Analyze the code diff carefully for:
1. SQL Injections, Hardcoded Secrets, API keys, or plain-text passwords.
2. Missing rate limiting or poor authentication/authorization practices.
3. Violations of the provided Jira requirements or internal RAG architectural guidelines.

Calculate:
- risk_score: 0 to 100 (0 = completely safe, 50+ = moderate risk/requires human approval, 80+ = critical vulnerability).
- confidence: 0.0 to 100.0 (your confidence in this assessment).

You MUST return your answer strictly formatted according to the SecurityReviewDecision schema."""
    ),
    (
        "human",
        """--- PR METADATA ---
Repository: {repo_name}
PR #{pr_number}: {pr_title}
Author: {author}
Branch: {head_branch} -> {base_branch}

--- JIRA ACCEPTANCE CRITERIA ---
{jira_requirements}

--- INTERNAL RAG SECURITY GUIDELINES ---
{rag_context}

--- RAW PULL REQUEST DIFF ---
{pr_diff}
"""
    )
])


async def fetch_pr_diff_node(state: PRReviewState) -> Dict[str, Any]:
    """Node 1: Retrieves the code diff from GitHub."""
    logger.info(f"[Node: fetch_pr_diff_node] Fetching diff for PR #{state['pr_number']}...")
    try:
        diff = await fetch_pr_diff(state["repo_name"], state["pr_number"])
        return {"pr_diff": diff, "status": "ANALYZING"}
    except Exception as e:
        logger.error(f"Error in fetch_pr_diff_node: {e}")
        return {"error": str(e), "status": "FAILED"}


async def fetch_jira_specs_node(state: PRReviewState) -> Dict[str, Any]:
    """Node 2: Retrieves linked Jira acceptance criteria."""
    logger.info("[Node: fetch_jira_specs_node] Extracting Jira requirements...")
    try:
        specs = await fetch_jira_requirements(state["head_branch"], state["pr_title"])
        return {"jira_requirements": specs}
    except Exception as e:
        logger.error(f"Error in fetch_jira_specs_node: {e}")
        return {"jira_requirements": "Standard Security Policy applies."}


async def retrieve_docs_node(state: PRReviewState, config: RunnableConfig) -> Dict[str, Any]:
    """Node 3: Retrieves internal security guidelines from pgvector RAG database."""
    logger.info("[Node: retrieve_docs_node] Querying pgvector RAG guidelines...")
    try:
        pool = config.get("configurable", {}).get("db_pool")
        
        query = f"{state['pr_title']} {state.get('pr_diff', '')[:200]}"
        if pool:
            docs = await retrieve_security_guidelines(pool, query_text=query, top_k=2)
        else:
            logger.warning("No db_pool found in config. Using fallback standard guidelines.")
            docs = [
                "[Standard Security]: Use parameterized SQL queries.",
                "[Standard Security]: Do not commit hardcoded API keys."
            ]
        return {"rag_context": docs}
    except Exception as e:
        logger.error(f"Error in retrieve_docs_node: {e}")
        return {"rag_context": ["[Fallback Policy]: Prevent SQL injection and secret exposure."]}


async def security_review_node(state: PRReviewState) -> Dict[str, Any]:
    """
    Node 4: The Cognitive Core.
    Invokes Groq LLM to review code and produce a structured SecurityReviewDecision.
    """
    logger.info("[Node: security_review_node] Performing AI Security Analysis via Groq...")
    try:
        prompt_val = await REVIEW_PROMPT.ainvoke({
            "repo_name": state["repo_name"],
            "pr_number": state["pr_number"],
            "pr_title": state["pr_title"],
            "author": state["author"],
            "head_branch": state["head_branch"],
            "base_branch": state["base_branch"],
            "jira_requirements": state["jira_requirements"],
            "rag_context": "\n".join(state["rag_context"]),
            "pr_diff": state["pr_diff"]
        })

        decision: SecurityReviewDecision = await structured_llm.ainvoke(prompt_val)

        logger.info(
            f"[Security Review Complete] Risk Score: {decision.risk_score}/100 | "
            f"Confidence: {decision.confidence}% | "
            f"Requires HITL Approval: {decision.requires_human_review}"
        )

        findings_list = [f.model_dump() for f in decision.findings]

        return {
            "risk_score": decision.risk_score,
            "confidence": decision.confidence,
            "review_summary": decision.summary,
            "findings": findings_list,
            "requires_human_review": decision.requires_human_review,
            "status": "AWAITING_APPROVAL" if decision.requires_human_review else "APPROVED"
        }
    except Exception as e:
        logger.error(f"Fatal LLM error in security_review_node: {e}", exc_info=True)
        return {
            "error": f"LLM Review Failed: {str(e)}",
            "risk_score": 100,
            "confidence": 0.0,
            "requires_human_review": True,
            "status": "NEEDS_HUMAN_REVIEW"
        }


async def post_github_comment_node(state: PRReviewState) -> Dict[str, Any]:
    """
    Node 5: Formats AI findings into clean Markdown and posts to GitHub PR.
    """
    logger.info("[Node: post_github_comment_node] Preparing markdown comment...")
    try:
        md_lines = [
            f"## 🤖 LangGraph Autonomous DevOps & PR Security Review",
            f"**Risk Score:** `{state['risk_score']} / 100` | **Confidence:** `{state['confidence']}%`",
            f"**Status:** `{state['status']}`\n",
            f"### 📋 Executive Summary",
            f"{state.get('review_summary', 'No summary provided.')}\n"
        ]

        if state.get("findings"):
            md_lines.append("### 🚨 Detected Security & Architectural Findings")
            for f in state["findings"]:
                md_lines.extend([
                    f"- **[{f['severity']}] {f['title']}** (`{f['file_path']}` Line ~`{f.get('line_number', 'N/A')}`)",
                    f"  - *Description:* {f['description']}",
                    f"  - *Recommendation:* {f['recommendation']}\n"
                ])
        else:
            md_lines.append("✅ **No critical security vulnerabilities or specification violations detected.**")

        if state.get("human_approved") is not None:
            md_lines.append(f"\n*HITL Decision: Human Reviewer marked this PR as **{'APPROVED' if state['human_approved'] else 'REJECTED'}**.*")

        full_comment = "\n".join(md_lines)
        await post_github_comment(state["repo_name"], state["pr_number"], full_comment)

        return {"status": "COMPLETED"}
    except Exception as e:
        logger.error(f"Error in post_github_comment_node: {e}")
        return {"error": str(e), "status": "FAILED"}