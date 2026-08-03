import logging
from fastapi import APIRouter, Request, HTTPException
from langgraph.types import Command
from app.schemas import HITLApprovalRequest, HITLApprovalResponse, ReviewStatus
from app.graph.workflow import get_compiled_workflow

logger = logging.getLogger("ReviewRouter")
router = APIRouter(prefix="/api/review", tags=["Human-In-The-Loop (HITL)"])


@router.get("/{thread_id}/status")
async def get_review_status(thread_id: str, request: Request):
    """
    Inspects the current state of a LangGraph execution thread.
    Returns calculated risk score, findings, and whether it is paused for HITL review.
    """
    checkpointer = getattr(request.app.state, "checkpointer", None)
    if not checkpointer:
        raise HTTPException(status_code=503, detail="Database checkpointer is not available.")

    workflow = get_compiled_workflow(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state_snapshot = await workflow.aget_state(config)
        if not state_snapshot or not state_snapshot.values:
            raise HTTPException(status_code=404, detail=f"No workflow state found for thread_id: {thread_id}")

        values = state_snapshot.values
        next_nodes = state_snapshot.next

        return {
            "thread_id": thread_id,
            "status": values.get("status", "UNKNOWN"),
            "risk_score": values.get("risk_score", 0),
            "confidence": values.get("confidence", 0.0),
            "summary": values.get("review_summary", ""),
            "findings": values.get("findings", []),
            "is_paused_for_hitl": bool(next_nodes),
            "next_scheduled_nodes": list(next_nodes),
            "human_approved": values.get("human_approved")
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching state for {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch review status: {str(e)}")


@router.post("/{thread_id}/decide", response_model=HITLApprovalResponse)
async def submit_hitl_decision(thread_id: str, decision: HITLApprovalRequest, request: Request):
    """
    Resumes a frozen LangGraph workflow after a human reviewer approves or rejects the PR.
    Uses LangGraph 0.2+ Command(resume=...) API.
    """
    checkpointer = getattr(request.app.state, "checkpointer", None)
    db_pool = getattr(request.app.state, "db_pool", None)
    
    if not checkpointer:
        raise HTTPException(status_code=503, detail="Database checkpointer is not available.")

    workflow = get_compiled_workflow(checkpointer=checkpointer)
    config = {
        "configurable": {
            "thread_id": thread_id,
            "db_pool": db_pool
        }
    }

    try:
        state_snapshot = await workflow.aget_state(config)
        if not state_snapshot or not state_snapshot.next:
            raise HTTPException(
                status_code=400,
                detail=f"Thread {thread_id} is not paused for human review."
            )

        logger.info(
            f"[HITL Resume] Reviewer '{decision.reviewer_id}' submitted decision "
            f"-> Approved: {decision.approved} for thread {thread_id}"
        )

        resume_payload = {
            "approved": decision.approved,
            "notes": decision.reviewer_notes or ""
        }
        
        await workflow.ainvoke(
            Command(
                resume=resume_payload,
                update={"human_approved": decision.approved, "human_reviewer_notes": decision.reviewer_notes}
            ),
            config=config
        )

        new_status = ReviewStatus.APPROVED if decision.approved else ReviewStatus.REJECTED
        return HITLApprovalResponse(
            thread_id=thread_id,
            status=new_status,
            message=f"HITL review submitted successfully. PR marked as {new_status.value}."
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error submitting HITL decision for {thread_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit decision: {str(e)}")