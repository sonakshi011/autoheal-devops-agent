from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from ai_engine.models.failure import FailureSeverity


class GeminiDiagnosisOutput(BaseModel):
    """Schema sent to Gemini API to enforce strict, deterministic output."""

    root_cause: str = Field(
        ..., description="Concise explanation of the exact failure based on logs."
    )
    severity: FailureSeverity = Field(..., description="Severity assessment of the failure.")
    remediation_steps: List[str] = Field(
        ..., description="Step-by-step actionable instructions to fix the issue."
    )
    code_suggestion: Optional[str] = Field(
        None,
        description="INFORMATIONAL ONLY. Potential shell commands or code fixes. Never executed autonomously.",
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score from 0 to 100 indicating certainty of diagnosis.",
    )


class AIDiagnosisResponse(GeminiDiagnosisOutput):
    """Final operational payload enriched with AI metadata."""

    model_used: str = Field(..., description="The AI model that generated this diagnosis.")
    diagnosis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of diagnosis generation.",
    )
