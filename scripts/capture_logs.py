import os
import sys
import argparse
import json
import logging
from datetime import datetime
from typing import Optional

# Ensure project root is in PYTHONPATH when running as a standalone script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_engine.models.failure import FailurePayload, FailureSeverity, FailureType
from ai_engine.utils.sanitizer import sanitize_logs

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("capture_logs")

MAX_LOG_LENGTH = 15000  # Token-safe truncation limit (approx 3k-4k tokens)


def heuristic_classification(logs: str) -> tuple[FailureType, FailureSeverity]:
    """Basic heuristic to classify the failure type and severity based on log content."""
    logs_lower = logs.lower()

    if (
        "docker build" in logs_lower
        or "failed to compute cache key" in logs_lower
        or "containerd" in logs_lower
    ):
        return FailureType.DOCKER_BUILD_FAILURE, FailureSeverity.CRITICAL
    elif (
        "pip install" in logs_lower
        or "no matching distribution" in logs_lower
        or "modulenotfounderror" in logs_lower
    ):
        return FailureType.DEPENDENCY_ERROR, FailureSeverity.HIGH
    elif "syntaxerror" in logs_lower or "indentationerror" in logs_lower:
        return FailureType.SYNTAX_ERROR, FailureSeverity.HIGH
    elif "importerror" in logs_lower:
        return FailureType.IMPORT_ERROR, FailureSeverity.HIGH
    elif "timeout" in logs_lower or "exceeded maximum execution time" in logs_lower:
        return FailureType.TIMEOUT_FAILURE, FailureSeverity.MEDIUM
    elif "pytest" in logs_lower and ("failed" in logs_lower or "assertionerror" in logs_lower):
        return FailureType.TEST_FAILURE, FailureSeverity.HIGH
    elif "trivy" in logs_lower or "bandit" in logs_lower or "safety check" in logs_lower:
        return FailureType.SECURITY_SCAN_FAILURE, FailureSeverity.CRITICAL
    elif "ruff" in logs_lower or "black" in logs_lower or "flake8" in logs_lower:
        return FailureType.LINT_ERROR, FailureSeverity.MEDIUM

    return FailureType.UNKNOWN, FailureSeverity.MEDIUM


def extract_logs_from_stdin() -> str:
    """Read logs from standard input."""
    return sys.stdin.read()


def extract_logs_from_file(file_path: str) -> str:
    """Read logs from a local file."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return ""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_logs_from_gh_artifact(artifact_path: str) -> str:
    """Read logs downloaded from a GitHub artifact (often a zip or directory)."""
    # For MVP, we assume the artifact was extracted to a text file
    return extract_logs_from_file(artifact_path)


def process_logs(raw_logs: str) -> str:
    """Sanitizes and truncates raw logs deterministically, preserving beginning and end."""
    logger.info("Stage: Sanitizing raw logs")
    sanitized = sanitize_logs(raw_logs)

    if len(sanitized) > MAX_LOG_LENGTH:
        logger.warning(
            f"Stage: Truncation required. Logs ({len(sanitized)} chars) exceed {MAX_LOG_LENGTH} limit."
        )
        # Preserve first 15% (for workflow context) and last 85% (for error stack trace)
        head_length = int(MAX_LOG_LENGTH * 0.15)
        tail_length = int(MAX_LOG_LENGTH * 0.85) - 50  # leave room for marker

        head = sanitized[:head_length]
        tail = sanitized[-tail_length:]
        sanitized = f"{head}\n\n...[TRUNCATED TO PRESERVE TOKEN LIMITS]...\n\n{tail}"
        logger.info("Stage: Truncation applied successfully (Head + Tail strategy).")
    else:
        logger.info("Stage: Logs within limits, no truncation required.")

    return sanitized


def main():
    parser = argparse.ArgumentParser(description="Capture and sanitize CI logs.")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--file", type=str, help="Path to log file")
    parser.add_argument("--gh-artifact", type=str, help="Path to extracted GitHub artifact file")
    parser.add_argument("--workflow", type=str, default="Unknown", help="Workflow name")
    parser.add_argument("--job", type=str, default="Unknown", help="Job name")
    parser.add_argument("--step", type=str, help="Step name")
    parser.add_argument("--exit-code", type=int, default=1, help="Exit code of the failed process")
    parser.add_argument(
        "--output", type=str, default="failure_payload.json", help="Output JSON path"
    )

    args = parser.parse_args()

    raw_logs = ""
    if args.stdin:
        raw_logs = extract_logs_from_stdin()
    elif args.file:
        raw_logs = extract_logs_from_file(args.file)
    elif args.gh_artifact:
        raw_logs = extract_logs_from_gh_artifact(args.gh_artifact)
    else:
        logger.error("No input source provided. Use --stdin, --file, or --gh-artifact.")
        sys.exit(1)

    if not raw_logs.strip():
        logger.warning("Captured logs are empty.")

    processed_logs = process_logs(raw_logs)
    failure_type, severity = heuristic_classification(processed_logs)

    payload = FailurePayload(
        workflow_name=args.workflow,
        job_name=args.job,
        step_name=args.step,
        exit_code=args.exit_code,
        logs=processed_logs,
        timestamp=datetime.utcnow(),
        branch=os.getenv("GITHUB_REF_NAME"),
        commit_sha=os.getenv("GITHUB_SHA"),
        repository=os.getenv("GITHUB_REPOSITORY"),
        runner_os=os.getenv("RUNNER_OS"),
        failure_type=failure_type,
        severity=severity,
    )

    output_path = args.output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(payload.model_dump_json(indent=2))

    logger.info(f"Sanitized failure payload written to {output_path}")
    logger.info(f"Classified as: {failure_type.value} | Severity: {severity.value}")


if __name__ == "__main__":
    main()
