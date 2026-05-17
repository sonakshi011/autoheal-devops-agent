from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_centralized_error_handling_404():
    """Verify that a missing report returns a standardized enveloped JSON response with 404 status."""
    with patch("app.services.github_service.GitHubService.get_workflow_runs") as mock_get:
        mock_get.return_value = {
            "runs": [
                {
                    "id": 1001,
                    "name": "Workflow Run",
                    "status": "completed",
                    "conclusion": "failure",
                    "event": "push",
                    "html_url": "https://github.com/dummy/repo",
                    "created_at": None,
                }
            ],
            "is_mock": True,
        }
        with patch("app.services.reports_service.os.path.exists", return_value=False):
            response = client.get("/api/v1/ai/latest-diagnosis")
            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert "error" in data
            assert "timestamp" in data


def test_latest_diagnosis_success_clear():
    """Verify that if the latest workflow run succeeded, get_latest_diagnosis raises 404 (clears stale state)."""
    with patch("app.services.github_service.GitHubService.get_workflow_runs") as mock_get:
        mock_get.return_value = {
            "runs": [
                {
                    "id": 1001,
                    "name": "Workflow Run",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "html_url": "https://github.com/dummy/repo",
                    "created_at": None,
                }
            ],
            "is_mock": True,
        }
        response = client.get("/api/v1/ai/latest-diagnosis")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "No active failures detected" in data["error"]


def test_pipeline_runs_mock_fallback():
    """Verify that when github credentials are not configured, the endpoint returns structured mock runs."""
    with patch("app.services.github_service.settings.github_token", None):
        with patch("app.services.github_service.settings.github_repository", None):
            response = client.get("/api/v1/pipelines/runs")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["is_mock"] is True
            assert len(data["data"]["runs"]) == 2
            assert data["data"]["runs"][0]["id"] == 1001


def test_cors_headers():
    """Verify that CORS preflight and access headers match our dynamic configuration."""
    with patch("app.services.github_service.settings.github_token", None):
        with patch("app.services.github_service.settings.github_repository", None):
            response = client.get(
                "/api/v1/pipelines/runs", headers={"Origin": "http://localhost:3000"}
            )
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
