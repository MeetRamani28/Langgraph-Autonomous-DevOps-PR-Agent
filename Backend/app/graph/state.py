from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas import Finding, ReviewStatus


class PRReviewState(BaseModel):
    """
    The central state object passed across all nodes in the LangGraph workflow.
    Stores raw input data, retrieved context, AI analysis results, and execution flags.
    Uses Pydantic for runtime validation and type safety.
    """

    repo_name: str
    pr_number: int
    pr_title: str
    pr_body: Optional[str] = ""
    author: str
    head_branch: str
    base_branch: str

    pr_diff: Optional[str] = None
    jira_requirements: Optional[str] = None
    rag_context: List[str] = Field(default_factory=list)

    risk_score: Optional[int] = None
    confidence: Optional[float] = None
    review_summary: Optional[str] = None
    findings: List[Finding] = Field(default_factory=list)

    requires_human_review: bool = False
    status: ReviewStatus = ReviewStatus.PENDING
    human_approved: Optional[bool] = None
    human_reviewer_notes: Optional[str] = None

    error: Optional[str] = None