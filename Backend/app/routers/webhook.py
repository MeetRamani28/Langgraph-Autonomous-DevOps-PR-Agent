import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.schemas import GitHubWebhookPayload, WebhookIngestResponse, PullRequestDetails, RepositoryInfo
from app.graph.workflow import get_compiled_workflow
from app.graph.state import PRReviewState

logger = logging.getLogger("WebhookRouter")
router = APIRouter(prefix="/api/webhook", tags=["Webhook Ingestion"])


async def run_pr_review_pipeline(state: PRReviewState, thread_id: str, app_state):
    """
    Background task that executes the compiled LangGraph workflow.
    """
    logger.info(f"[Pipeline] Launching workflow for thread_id: {thread_id}...")
    try:
        checkpointer = getattr(app_state, "checkpointer", None)
        db_pool = getattr(app_state, "db_pool", None)
        
        workflow = get_compiled_workflow(checkpointer=checkpointer)
        config = {
            "configurable": {
                "thread_id": thread_id,
                "db_pool": db_pool
            }
        }
        
        # Execute the workflow
        final_state = await workflow.ainvoke(state, config=config)
        logger.info(f"[Pipeline Complete] Thread {thread_id} ended with status: {final_state.get('status')}")
    except Exception as e:
        logger.error(f"[Pipeline Error] Thread {thread_id} failed: {e}", exc_info=True)


@router.post("/github", response_model=WebhookIngestResponse)
async def github_webhook_endpoint(
    payload: GitHubWebhookPayload,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Production GitHub Webhook endpoint.
    Triggers when a PR is opened, synchronized, or reopened.
    """
    # Only process relevant PR actions
    if payload.action not in ["opened", "synchronize", "reopened"]:
        return WebhookIngestResponse(
            status="ignored",
            thread_id="N/A",
            repo=payload.repository.full_name,
            pr_number=payload.pull_request.number,
            message=f"Action '{payload.action}' ignored."
        )

    repo_name = payload.repository.full_name
    pr_num = payload.pull_request.number
    thread_id = f"pr-{repo_name.replace('/', '-')}-{pr_num}"

    initial_state: PRReviewState = {
        "repo_name": repo_name,
        "pr_number": pr_num,
        "pr_title": payload.pull_request.title,
        "pr_body": payload.pull_request.body or "",
        "author": payload.pull_request.author,
        "head_branch": payload.pull_request.head_branch,
        "base_branch": payload.pull_request.base_branch,
        "pr_diff": "",
        "jira_requirements": "",
        "rag_context": [],
        "risk_score": 0,
        "confidence": 0.0,
        "review_summary": "",
        "findings": [],
        "requires_human_review": False,
        "status": "PENDING",
        "human_approved": None,
        "human_reviewer_notes": None,
        "error": None
    }

    background_tasks.add_task(run_pr_review_pipeline, initial_state, thread_id, request.app.state)

    return WebhookIngestResponse(
        status="queued",
        thread_id=thread_id,
        repo=repo_name,
        pr_number=pr_num,
        message="Pull Request security review pipeline queued successfully."
    )


@router.post("/test", response_model=WebhookIngestResponse)
async def test_webhook_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Convenience endpoint to test the AI review pipeline locally without GitHub webhooks.
    Simulates a PR containing a SQL Injection vulnerability.
    """
    repo_name = "owner/repo"
    pr_num = 101
    thread_id = f"pr-{repo_name.replace('/', '-')}-{pr_num}"

    initial_state: PRReviewState = {
        "repo_name": repo_name,
        "pr_number": pr_num,
        "pr_title": "feat: add user login endpoint [DEV-101]",
        "pr_body": "Implements basic authentication login query.",
        "author": "local_dev",
        "head_branch": "feat/DEV-101-login",
        "base_branch": "main",
        "pr_diff": "",  
        "jira_requirements": "",
        "rag_context": [],
        "risk_score": 0,
        "confidence": 0.0,
        "review_summary": "",
        "findings": [],
        "requires_human_review": False,
        "status": "PENDING",
        "human_approved": None,
        "human_reviewer_notes": None,
        "error": None
    }

    background_tasks.add_task(run_pr_review_pipeline, initial_state, thread_id, request.app.state)

    return WebhookIngestResponse(
        status="queued",
        thread_id=thread_id,
        repo=repo_name,
        pr_number=pr_num,
        message="Local simulation workflow queued! Check server terminal logs for progress."
    )