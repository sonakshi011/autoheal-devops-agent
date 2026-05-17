from fastapi import APIRouter, HTTPException
from app.models.responses import APISuccessResponse
from app.services.reports_service import ReportsService
from app.services.github_service import GitHubService

v1_router = APIRouter(prefix="/api/v1")


@v1_router.get("/ai/latest-diagnosis", response_model=APISuccessResponse)
def get_latest_diagnosis():
    """Gets the latest AI diagnosis JSON report, synchronized with the current GitHub workflow state."""
    # 1. Fetch latest workflow state from GitHub (live or mock fallback)
    runs_data = GitHubService.get_workflow_runs()
    runs = runs_data.get("runs", [])

    if not runs:
        raise HTTPException(
            status_code=404, detail="No active failures detected. No workflow runs found."
        )

    latest_run = runs[0]

    # 2. Check if the latest run did NOT fail
    # Note: conclusion could be 'success', 'cancelled', 'skipped', or in-progress (None)
    # If the latest run is NOT a failure, we clear the stale diagnosis rendering!
    if latest_run.get("conclusion") != "failure":
        raise HTTPException(
            status_code=404,
            detail="No active failures detected. The latest workflow run succeeded.",
        )

    # 3. If it failed, load the latest generated failure diagnosis report
    data = ReportsService.read_and_validate_report("reports/ai_diagnosis.json")
    return APISuccessResponse(data=data)


@v1_router.get("/scans/bandit", response_model=APISuccessResponse)
def get_bandit_scan():
    """Delegates to ReportsService to get the Bandit SAST findings."""
    data = ReportsService.read_and_validate_report("reports/bandit-results.sarif")
    return APISuccessResponse(data=data)


@v1_router.get("/scans/trivy", response_model=APISuccessResponse)
def get_trivy_scan():
    """Delegates to ReportsService to get the Trivy vulnerability scan findings."""
    data = ReportsService.read_and_validate_report("reports/trivy-results.json")
    return APISuccessResponse(data=data)


@v1_router.get("/pipelines/runs", response_model=APISuccessResponse)
def get_pipeline_runs():
    """Delegates to GitHubService to get recent pipeline workflow runs."""
    data = GitHubService.get_workflow_runs()
    return APISuccessResponse(data=data)
