import re
import logging

logger = logging.getLogger("autoheal.ai.sanitizer")

# Common patterns for secrets
SECRET_PATTERNS = [
    # General API keys and secrets
    (re.compile(r"(?i)(api[_-]?key[\s:=]+)[a-zA-Z0-9_\-]+"), r"\1[REDACTED_API_KEY]"),
    (re.compile(r"(?i)(secret[\s:=]+)[a-zA-Z0-9_\-]+"), r"\1[REDACTED_SECRET]"),
    (re.compile(r"(?i)(token[\s:=]+)[a-zA-Z0-9_\-]+"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(password[\s:=]+)[a-zA-Z0-9_\-]+"), r"\1[REDACTED_PASSWORD]"),
    # Specific cloud provider patterns
    (re.compile(r"(?i)(AKIA[0-9A-Z]{16})"), r"[REDACTED_AWS_ACCESS_KEY]"),
    (re.compile(r"(?i)(ghp_[a-zA-Z0-9]{36})"), r"[REDACTED_GITHUB_TOKEN]"),
]

# Patterns designed to confuse or jailbreak the LLM
PROMPT_INJECTION_PATTERNS = [
    (re.compile(r"(?i)(ignore previous instructions)"), r"[REDACTED_INJECTION_ATTEMPT]"),
    (re.compile(r"(?i)(system prompt)"), r"[REDACTED_SYSTEM_OVERRIDE]"),
    (re.compile(r"(?i)(you are now)"), r"[REDACTED_ROLE_OVERRIDE]"),
    # Hidden instruction patterns & multiline jailbreaks
    (
        re.compile(r"(?is)(?:\b(forget|disregard)\b.+?\b(instructions|rules|context)\b)"),
        r"[REDACTED_JAILBREAK_ATTEMPT]",
    ),
    # Markdown-based prompt manipulation (e.g., closing fences early)
    (re.compile(r"```(?:json|text)?\s*[\n\r]+\s*```"), r"[REDACTED_EMPTY_FENCE]"),
    # Base64 encoded generic jailbreaks (e.g., "ignore" -> aWdub3Jl)
    (re.compile(r"(?i)(aWdub3JlIHByZXZpb3Vz)"), r"[REDACTED_B64_INJECTION]"),
]


def sanitize_logs(log_content: str) -> str:
    """
    Sanitize raw logs by removing secrets, passwords, tokens, and
    potential prompt injection vectors. Preserves stack traces.
    """
    if not log_content:
        return ""

    sanitized_content = log_content
    stats = {"secrets_redacted": 0, "injections_mitigated": 0}

    # 1. Redact secrets
    for pattern, replacement in SECRET_PATTERNS:
        sanitized_content, count = pattern.subn(replacement, sanitized_content)
        stats["secrets_redacted"] += count

    # 2. Mitigate prompt injection
    for pattern, replacement in PROMPT_INJECTION_PATTERNS:
        sanitized_content, count = pattern.subn(replacement, sanitized_content)
        stats["injections_mitigated"] += count

    if stats["secrets_redacted"] > 0 or stats["injections_mitigated"] > 0:
        logger.info(f"Sanitization complete. Stats: {stats}")

    return sanitized_content
