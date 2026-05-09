from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FailureSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FailureType(str, Enum):
    LINT_ERROR = "lint_error"
    TEST_FAILURE = "test_failure"
    DOCKER_BUILD_FAILURE = "docker_build_failure"
    DEPENDENCY_ERROR = "dependency_error"
    SECURITY_SCAN_FAILURE = "security_scan_failure"
    TIMEOUT_FAILURE = "timeout_failure"
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    CONTAINER_RUNTIME_FAILURE = "container_runtime_failure"
    UNKNOWN = "unknown"


class FailurePayload(BaseModel):
    """Standardized schema for CI/CD failure payloads ready for AI diagnosis."""

    workflow_name: str = Field(..., description="Name of the GitHub Actions workflow")
    job_name: str = Field(..., description="Name of the specific job that failed")
    step_name: Optional[str] = Field(
        None, description="Name of the specific step that failed, if identifiable"
    )
    exit_code: int = Field(..., description="Exit code of the failing process")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Time the failure was captured"
    )
    logs: str = Field(..., description="Sanitized and truncated logs relevant to the failure")

    # Metadata
    branch: Optional[str] = Field(None, description="Git branch where the failure occurred")
    commit_sha: Optional[str] = Field(None, description="Git commit SHA")
    repository: Optional[str] = Field(None, description="GitHub repository name (owner/repo)")
    runner_os: Optional[str] = Field(
        None, description="Operating system of the runner (e.g., Linux, Windows)"
    )
    python_version: Optional[str] = Field(
        None, description="Python version used in the environment"
    )

    # Classification
    severity: FailureSeverity = Field(
        default=FailureSeverity.HIGH, description="Estimated severity of the failure"
    )
    failure_type: FailureType = Field(
        default=FailureType.UNKNOWN, description="Category of the failure based on heuristics"
    )
