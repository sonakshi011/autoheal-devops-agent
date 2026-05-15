import os
import sys
import json
import logging
from typing import List, Dict, Any

# pyrefly: ignore [missing-import]
from github import Github
from unidiff import PatchSet

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_engine.client import GeminiClient
from ai_engine.models.review import PRReviewResponse
from ai_engine.prompts.templates import PromptBuilder
from ai_engine.utils.sanitizer import sanitize_logs

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("review_pr")

# File extensions we care about for review
REVIEWABLE_EXTENSIONS = {".py", ".js", ".ts", ".go", ".java", ".cpp", ".c", ".h", ".sql", ".sh"}


def get_pr_diff(gh_token: str, repo_name: str, pr_number: int) -> str:
    """Fetches the PR diff as a string."""
    # Fetch the raw diff directly using requests
    import requests

    headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3.diff"}
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.text


def parse_diff_to_files(diff_str: str) -> List[Dict[str, Any]]:
    """Parses unified diff into a list of file changes."""
    patch = PatchSet(diff_str)
    files_to_review = []

    for patched_file in patch:
        file_path = patched_file.path
        _, ext = os.path.splitext(file_path)

        if ext.lower() not in REVIEWABLE_EXTENSIONS:
            continue

        # Only include the diff content (hunks)
        # We sanitize the diff to avoid sending secrets to AI
        raw_diff = str(patched_file)
        sanitized_diff = sanitize_logs(raw_diff)

        files_to_review.append({"path": file_path, "diff": sanitized_diff})

    return files_to_review


def main():
    gh_token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number_str = os.getenv("PR_NUMBER")

    if not all([gh_token, repo_name, pr_number_str]):
        logger.error(
            "Missing required environment variables: GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER"
        )
        sys.exit(1)

    pr_number = int(pr_number_str)

    logger.info(f"Stage: Fetching diff for PR #{pr_number} in {repo_name}")
    try:
        diff_str = get_pr_diff(gh_token, repo_name, pr_number)
    except Exception as e:
        logger.error(f"Failed to fetch PR diff: {e}")
        sys.exit(1)

    files_to_review = parse_diff_to_files(diff_str)
    if not files_to_review:
        logger.info("No reviewable files found in PR. Skipping AI review.")
        sys.exit(0)

    logger.info(f"Stage: Found {len(files_to_review)} files to review.")

    prompt_builder = PromptBuilder()
    ai_client = GeminiClient()

    # We can run both code quality and security reviews
    templates = ["code_review.j2", "security_review.j2"]

    final_comments = []
    final_summaries = []

    for template_name in templates:
        logger.info(f"Stage: Executing {template_name} via Gemini")
        try:
            prompt = prompt_builder.env.get_template(template_name).render(
                workflow_name="AI PR Review", repository=repo_name, files=files_to_review
            )

            raw_response = ai_client.generate_content_with_retry(
                prompt=prompt, response_schema=PRReviewResponse.model_json_schema()
            )

            review_data = PRReviewResponse.model_validate_json(raw_response)
            final_summaries.append(
                f"### {template_name.replace('_', ' ').replace('.j2', '').title()}\n{review_data.summary}"
            )
            final_comments.extend(review_data.comments)

        except Exception as e:
            logger.error(f"Error during {template_name}: {e}")
            continue

    if not final_comments and not final_summaries:
        logger.warning("No review comments generated.")
        sys.exit(0)

    # Post comments to GitHub
    full_summary = "\n\n".join(final_summaries)

    # Save for artifacts
    with open("ai_review_response.json", "w", encoding="utf-8") as f:
        json.dump(
            {"summary": full_summary, "comments": [c.model_dump() for c in final_comments]},
            f,
            indent=2,
        )

    logger.info("Stage: Pipeline complete. Artifacts written: ai_review_response.json")

    logger.info("Stage: Posting consolidated review to GitHub")
    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # We post as a review with comments
    # To post inline comments, we need to map the line number to the 'position' in the diff.
    # PyGithub's create_review supports 'comments' as a list of dicts: {"path": path, "position": position, "body": body}
    # For now, we post a single high-level review comment as an MVP.
    # In a full implementation, we would iterate through hunks to map line -> position.

    try:
        # Posting a single review with a summary
        # And individual comments (using PRReviewComment line as a best effort)
        # Note: GitHub API 'line' parameter is newer than 'position' and easier to use.
        review_comments = []
        for c in final_comments:
            review_comments.append(
                {"path": c.path, "line": c.line, "body": f"**[{c.severity.upper()}]** {c.body}"}
            )

        # Post the review
        pr.create_review(body=full_summary, comments=review_comments, event="COMMENT")
        logger.info("Successfully posted AI PR Review.")
    except Exception as e:
        logger.error(f"Failed to post PR review: {e}")
        # Log the comments we would have posted
        logger.info(f"Summary: {full_summary}")
        for c in final_comments:
            logger.info(f"[{c.path}:{c.line}] {c.body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
