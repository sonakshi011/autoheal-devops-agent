from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class ReviewSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SECURITY = "security"


class PRReviewComment(BaseModel):
    """Schema for an individual inline comment on a Pull Request."""

    path: str = Field(..., description="The file path being reviewed.")
    line: int = Field(..., description="The line number in the file where the comment applies.")
    body: str = Field(..., description="The markdown body of the review comment.")
    severity: ReviewSeverity = Field(
        default=ReviewSeverity.INFO, description="The severity level of the finding."
    )


class PRReviewResponse(BaseModel):
    """Schema for a complete AI-generated PR review."""

    summary: str = Field(..., description="A high-level summary of the PR review.")
    comments: List[PRReviewComment] = Field(
        default_factory=list, description="List of inline comments."
    )
    overall_status: str = Field(
        ..., description="A status indicator (e.g., 'approve', 'request_changes', 'comment')."
    )
