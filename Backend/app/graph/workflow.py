import logging
from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.graph.state import PRReviewState
from app.graph.nodes import (
    fetch_pr_diff_node,
    fetch_jira_specs_node,
    retrieve_docs_node,
    security_review_node,
    post_github_comment_node,
)
from app.graph.edges import should_require_human_review

logger = logging.getLogger("GraphWorkflow")


def build_pr_review_graph() -> StateGraph:
    """
    Constructs the uncompiled LangGraph StateGraph connecting nodes and edges.
    """
    logger.info("Building PR Review LangGraph StateGraph...")
    builder = StateGraph(PRReviewState)

    builder.add_node("fetch_pr_diff_node", fetch_pr_diff_node)
    builder.add_node("fetch_jira_specs_node", fetch_jira_specs_node)
    builder.add_node("retrieve_docs_node", retrieve_docs_node)
    builder.add_node("security_review_node", security_review_node)
    builder.add_node("post_github_comment_node", post_github_comment_node)

    builder.add_edge(START, "fetch_pr_diff_node")
    builder.add_edge("fetch_pr_diff_node", "fetch_jira_specs_node")
    builder.add_edge("fetch_jira_specs_node", "retrieve_docs_node")
    builder.add_edge("retrieve_docs_node", "security_review_node")

    builder.add_conditional_edges(
        "security_review_node",
        should_require_human_review,
        {
            "auto_approve": "post_github_comment_node",
            "human_approved": "post_github_comment_node",
        }
    )

    builder.add_edge("post_github_comment_node", END)

    return builder


def get_compiled_workflow(checkpointer: Optional[AsyncPostgresSaver] = None):
    """
    Compiles the StateGraph into an executable LangGraph workflow.
    Injects the PostgreSQL checkpointer for state persistence and HITL interrupts.
    """
    builder = build_pr_review_graph()
    
    if checkpointer:
        logger.info("Compiling workflow WITH PostgreSQL checkpointer (HITL & Persistence enabled).")
        return builder.compile(checkpointer=checkpointer)
    
    logger.warning("Compiling workflow WITHOUT checkpointer (In-memory mode only).")
    return builder.compile()