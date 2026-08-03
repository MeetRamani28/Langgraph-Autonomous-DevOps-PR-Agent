import logging
from langgraph.types import interrupt
from app.graph.state import PRReviewState

logger = logging.getLogger("GraphEdges")


def should_require_human_review(state: PRReviewState) -> str:
    """
    Conditional routing edge function:
    - If risk score < 50 AND confidence >= 85.0 -> Route to 'post_github_comment_node' (Auto-merge/comment).
    - Otherwise -> Trigger LangGraph interrupt for Human-In-The-Loop (HITL) review.
    """
    risk_score = state.get("risk_score", 0)
    confidence = state.get("confidence", 100.0)
    
    logger.info(f"[Edge Router] Evaluating thresholds -> Risk Score: {risk_score}/100, Confidence: {confidence}%")

    if confidence >= 85.0 and risk_score < 50:
        logger.info("[Edge Router] PR meets safety criteria. Routing to auto-comment/approval.")
        return "auto_approve"
    
    logger.warning(
        f"[Edge Router] High risk ({risk_score}) or low confidence ({confidence}%). "
        "Freezing execution for Human-In-The-Loop (HITL) review."
    )
    
    interrupt({
        "reason": "High risk score or low confidence detected by AI Security Agent.",
        "risk_score": risk_score,
        "confidence": confidence,
        "summary": state.get("review_summary", ""),
        "findings": state.get("findings", [])
    })
    
    return "human_approved"