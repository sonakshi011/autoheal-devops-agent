from fastapi import HTTPException
from github import Github
from github.GithubException import GithubException
from app.config import settings

class GitHubService:
    @staticmethod
    def get_workflow_runs() -> dict:
        """Fetches the latest 10 workflow runs from GitHub, or provides fallback mock data if credentials are not configured."""
        token = settings.github_token
        repo_name = settings.github_repository

        if not token or not repo_name:
            mock_runs = [
                {
                    "id": 1001,
                    "name": "Security Scan & Lint",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "html_url": "https://github.com/dummy/repo/actions/runs/1",
                    "created_at": "2026-05-17T10:00:00Z"
                },
                {
                    "id": 1002,
                    "name": "AI Failure Diagnosis",
                    "status": "completed",
                    "conclusion": "failure",
                    "event": "pull_request",
                    "html_url": "https://github.com/dummy/repo/actions/runs/2",
                    "created_at": "2026-05-17T09:30:00Z"
                }
            ]
            return {"runs": mock_runs, "is_mock": True}

        try:
            g = Github(token)
            repo = g.get_repo(repo_name)
            runs = []
            for run in repo.get_workflow_runs()[:10]:
                runs.append({
                    "id": run.id,
                    "name": run.name,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "event": run.event,
                    "html_url": run.html_url,
                    "created_at": run.created_at.isoformat() if run.created_at else None
                })
            return {"runs": runs, "is_mock": False}
        except GithubException as ge:
            raise HTTPException(
                status_code=502,
                detail=f"GitHub API Error: {ge.data.get('message', 'Failed to communicate with GitHub')}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch runs from GitHub: {str(e)}")
