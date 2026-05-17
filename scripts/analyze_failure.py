import os
import sys
import json
import logging
from datetime import datetime, timezone
from pydantic import ValidationError

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_engine.models.failure import FailurePayload
from ai_engine.models.responses import GeminiDiagnosisOutput, AIDiagnosisResponse
from ai_engine.prompts.templates import PromptBuilder
from ai_engine.client import GeminiClient
from ai_engine.exceptions import AIClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("analyze_failure")


def load_payload(file_path: str) -> FailurePayload:
    """Loads and validates the JSON payload from capture_logs.py."""
    if not os.path.exists(file_path):
        logger.error(f"Payload file not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        payload = FailurePayload(**data)
        logger.info("Successfully loaded and validated FailurePayload schema.")
        return payload
    except ValidationError as e:
        logger.error(f"Payload validation failed: {e}")
        sys.exit(1)


def generate_fallback_diagnosis(payload: FailurePayload, error_msg: str) -> AIDiagnosisResponse:
    """Generate a deterministic fallback diagnosis when AI fails."""
    logger.warning("Stage: Generating Fallback Diagnosis")
    return AIDiagnosisResponse(
        root_cause=f"AI Diagnosis failed or timed out. Original error: {error_msg}",
        severity=payload.severity,
        remediation_steps=[
            "Review the raw logs directly in the GitHub Actions UI.",
            "Verify Gemini API quota and connectivity.",
        ],
        code_suggestion=None,
        confidence_score=0,
        model_used="fallback-heuristic",
        diagnosis_timestamp=datetime.now(timezone.utc),
    )


def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python analyze_failure.py <path_to_payload.json>")
        sys.exit(1)

    payload_path = sys.argv[1]
    payload = load_payload(payload_path)

    logger.info(f"Stage: Preparing AI diagnostic context for workflow: {payload.workflow_name}")
    logger.info(f"Context Classification: {payload.failure_type.value} ({payload.severity.value})")

    prompt_builder = PromptBuilder()
    diagnostic_prompt = prompt_builder.build_failure_diagnosis_prompt(
        logs=payload.logs, exit_code=payload.exit_code, workflow_name=payload.workflow_name
    )

    # AI Integration — model is resolved from settings, never hardcoded here
    try:
        logger.info("Stage: Initializing GeminiClient")
        client = GeminiClient()
        model_name = client.default_model
        # GeminiClient.__init__ already logs model + environment safely
        logger.info(f"Stage: Active model for this run → {model_name}")

        logger.info("Stage: Executing Gemini API generate_content_with_retry")
        raw_response = client.generate_content_with_retry(
            prompt=diagnostic_prompt, response_schema=GeminiDiagnosisOutput.model_json_schema()
        )

        logger.info("Stage: Parsing and validating structured AI response")
        ai_output = GeminiDiagnosisOutput.model_validate_json(raw_response)

        # Wrap into final operational response
        final_diagnosis = AIDiagnosisResponse(
            **ai_output.model_dump(),
            model_used=model_name,
            diagnosis_timestamp=datetime.now(timezone.utc),
        )
        logger.info("Stage: AI Diagnosis generation SUCCESS. Validation passed.")

    except AIClientError as e:
        logger.error(f"AIClientError: API call failed - {str(e)}")
        final_diagnosis = generate_fallback_diagnosis(payload, str(e))
    except ValidationError as e:
        logger.error(f"ValidationError: Malformed JSON from AI - {str(e)}")
        final_diagnosis = generate_fallback_diagnosis(
            payload, "Malformed structured output from AI"
        )
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        final_diagnosis = generate_fallback_diagnosis(payload, str(e))

    # Save structured JSON
    output_json_path = "reports/ai_diagnosis.json"
    with open(output_json_path, "w", encoding="utf-8") as f:
        f.write(final_diagnosis.model_dump_json(indent=2))

    # Save human-readable markdown
    output_md_path = "reports/ai_diagnosis_report.md"
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("# AutoHeal Diagnosis Report\n\n")
        f.write(f"**Root Cause**: {final_diagnosis.root_cause}\n\n")
        f.write(f"**Severity**: {final_diagnosis.severity.value.upper()}\n")
        f.write(f"**Confidence**: {final_diagnosis.confidence_score}%\n\n")
        f.write("### Remediation Steps\n")
        for step in final_diagnosis.remediation_steps:
            f.write(f"1. {step}\n")
        if final_diagnosis.code_suggestion:
            f.write("\n### Suggested Code / Commands (INFORMATIONAL ONLY)\n")
            f.write(
                "> [!WARNING]\n> These suggestions are AI-generated and should be reviewed before execution. AutoHeal does NOT execute them automatically.\n\n"
            )
            f.write(f"```\n{final_diagnosis.code_suggestion}\n```\n")

    logger.info(
        f"Stage: Pipeline complete. Artifacts written: {output_json_path}, {output_md_path}"
    )


if __name__ == "__main__":
    main()
