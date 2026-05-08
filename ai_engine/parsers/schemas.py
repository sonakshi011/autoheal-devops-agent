from pydantic import BaseModel, Field
from typing import Optional, List

class FailureDiagnosisResponse(BaseModel):
    """Schema for the Gemini API response to a failure diagnosis."""
    root_cause: str = Field(..., description="Brief explanation of why the pipeline failed.")
    severity: str = Field(..., description="Severity level: CRITICAL, WARNING, INFO")
    remediation_steps: List[str] = Field(..., description="Step-by-step instructions to fix the issue.")
    code_suggestion: Optional[str] = Field(None, description="Exact code snippet or shell command to resolve the error.")
