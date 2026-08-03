import asyncio
import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Request, HTTPException
from sse_starlette.sse import EventSourceResponse
from app.graph.workflow import get_compiled_workflow

logger = logging.getLogger("StreamRouter")
router = APIRouter(prefix="/api/stream", tags=["SSE Streaming"])


async def state_event_generator(thread_id: str, request: Request) -> AsyncGenerator[dict, None]:
    """
    Async generator that polls LangGraph PostgreSQL checkpoints and emits
    real-time Server-Sent Events (SSE) as the workflow progresses.
    """
    checkpointer = getattr(request.app.state, "checkpointer", None)
    if not checkpointer:
        yield {
            "event": "error",
            "data": json.dumps({"message": "Database checkpointer is not available."})
        }
        return

    workflow = get_compiled_workflow(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    logger.info(f"[SSE Stream] Client subscribed to stream for thread_id: {thread_id}")

    yield {
        "event": "connected",
        "data": json.dumps({"thread_id": thread_id, "message": "SSE stream connected successfully."})
    }

    last_status = None
    max_retries = 60  
    retries = 0

    try:
        while retries < max_retries:
            if await request.is_disconnected():
                logger.info(f"[SSE Stream] Client disconnected from thread_id: {thread_id}")
                break

            state_snapshot = await workflow.aget_state(config)

            if state_snapshot and state_snapshot.values:
                values = state_snapshot.values
                current_status = values.get("status", "PENDING")
                next_nodes = list(state_snapshot.next) if state_snapshot.next else []
                is_paused = bool(next_nodes)

                if current_status != last_status or is_paused:
                    last_status = current_status
                    payload = {
                        "thread_id": thread_id,
                        "status": current_status,
                        "risk_score": values.get("risk_score", 0),
                        "confidence": values.get("confidence", 0.0),
                        "summary": values.get("review_summary", ""),
                        "findings": values.get("findings", []),
                        "is_paused_for_hitl": is_paused,
                        "next_scheduled_nodes": next_nodes,
                        "human_approved": values.get("human_approved")
                    }

                    if is_paused and current_status == "AWAITING_APPROVAL":
                        yield {
                            "event": "hitl_interrupt",
                            "data": json.dumps(payload)
                        }
                    else:
                        yield {
                            "event": "state_update",
                            "data": json.dumps(payload)
                        }

                if current_status in ["COMPLETED", "APPROVED", "REJECTED", "FAILED"] and not is_paused:
                    yield {
                        "event": "completed",
                        "data": json.dumps({"thread_id": thread_id, "final_status": current_status})
                    }
                    logger.info(f"[SSE Stream] Stream finished for thread_id: {thread_id}")
                    break

            retries += 1
            await asyncio.sleep(2.0)  

        if retries >= max_retries:
            yield {
                "event": "timeout",
                "data": json.dumps({"message": "SSE stream timed out after 2 minutes."})
            }

    except asyncio.CancelledError:
        logger.info(f"[SSE Stream] Connection cancelled for thread_id: {thread_id}")
    except Exception as e:
        logger.error(f"[SSE Stream Error] Thread {thread_id}: {e}", exc_info=True)
        yield {
            "event": "error",
            "data": json.dumps({"message": f"Stream error: {str(e)}"})
        }


@router.get("/{thread_id}")
async def stream_pr_review_events(thread_id: str, request: Request):
    """
    Server-Sent Events (SSE) endpoint.
    Frontend React clients subscribe to GET /api/stream/{thread_id} to receive real-time updates.
    """
    return EventSourceResponse(
        state_event_generator(thread_id, request),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  
        }
    )