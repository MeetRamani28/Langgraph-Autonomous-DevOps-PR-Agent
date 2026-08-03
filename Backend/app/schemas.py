from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class RepositoryInfo(BaseModel):
    """Details about the target GitHub repository."""
    full_name: str = Field(..., example="owner/repo-name", description="Repository full name")
    name: str = Field(..., example="repo-name")
    owner: str = Field(..., example="owner-username")


class PullRequestDetails(BaseModel):
    """Extracted Pull Request information from the webhook payload."""
    number: int = Field(..., description="PR Number")
    title: str = Field(..., description="PR Title")
    body: Optional[str] = Field(default="", description="PR Description/Body")
    head_branch: str = Field(..., description="Source branch name")
    base_branch: str = Field(..., description="Target branch name")
    author: str = Field(..., description="PR Author GitHub handle")
    diff_url: Optional[str] = Field(default=None, description="URL to raw diff")


class GitHubWebhookPayload(BaseModel):
    """Incoming GitHub Pull Request Webhook event payload."""
    action: str = Field(..., example="opened", description="Event action: opened, synchronize, reopened")
    pull_request: PullRequestDetails = Field(..., description="Pull Request metadata")
    repository: RepositoryInfo = Field(..., description="Repository metadata")


class Finding(BaseModel):
    """An individual code issue or security finding identified by the AI Agent."""
    severity: FindingSeverity = Field(..., description="Severity level of the finding")
    file_path: str = Field(..., description="Relative path of the affected file")
    line_number: Optional[int] = Field(default=None, description="Approximate line number")
    title: str = Field(..., description="Short summary of the issue")
    description: str = Field(..., description="Detailed explanation of the issue")
    recommendation: str = Field(..., description="How to fix or remediate the issue")


class SecurityReviewDecision(BaseModel):
    """
    Structured output extracted directly from LLM response.
    Enforces risk score calculation and confidence ratings.
    """
    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Calculated risk score between 0 (Safe) and 100 (Critical Hazard)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Agent confidence level (0.0 to 100.0)"
    )
    summary: str = Field(..., description="High-level executive summary of the review")
    findings: List[Finding] = Field(
        default_factory=list,
        description="List of security/architectural findings detected"
    )
    requires_human_review: bool = Field(
        default=False,
        description="Flag set to True if risk score >= 50 or confidence < 85%"
    )

    @field_validator("requires_human_review", mode="before")
    @classmethod
    def set_human_review_flag(cls, v, values):
        """Auto-calculate if human review is required if not explicitly set."""
        risk_score = values.data.get("risk_score", 0)
        confidence = values.data.get("confidence", 100.0)
        if risk_score >= 50 or confidence < 85.0:
            return True
        return v


class HITLApprovalRequest(BaseModel):
    """Payload sent by human reviewer when approving or rejecting a pending review state."""
    approved: bool = Field(..., description="True if human approves merging/posting, False if rejected")
    reviewer_notes: Optional[str] = Field(default="", description="Optional feedback or notes from the human reviewer")
    reviewer_id: str = Field(default="admin", description="ID or username of the human reviewer")


class HITLApprovalResponse(BaseModel):
    """Response returned after processing a HITL approval/rejection decision."""
    thread_id: str = Field(..., description="LangGraph execution thread identifier")
    status: ReviewStatus = Field(..., description="Updated status after human decision")
    message: str = Field(..., description="Human-readable status summary")


class WebhookIngestResponse(BaseModel):
    """Response returned upon successfully receiving and starting the workflow for a webhook."""
    status: str = Field(default="queued")
    thread_id: str = Field(..., description="LangGraph thread_id allocated for tracking")
    repo: str = Field(..., description="Target repository")
    pr_number: int = Field(..., description="Target PR number")
    message: str = Field(default="PR Review Workflow kicked off successfully")