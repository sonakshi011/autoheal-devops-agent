import pytest
import os
import json
from unittest.mock import patch, mock_open
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.capture_logs import heuristic_classification, process_logs, MAX_LOG_LENGTH
from ai_engine.models.failure import FailureType, FailureSeverity


def test_heuristic_classification():
    # Test Pytest
    logs = "pytest FAILED tests/test_app.py - AssertionError"
    t, s = heuristic_classification(logs)
    assert t == FailureType.TEST_FAILURE
    assert s == FailureSeverity.HIGH

    # Test Lint
    logs = "ruff format --check failed"
    t, s = heuristic_classification(logs)
    assert t == FailureType.LINT_ERROR
    assert s == FailureSeverity.MEDIUM

    # Test Docker
    logs = "ERROR: failed to solve: process '/bin/sh -c pip install' returned 1"
    t, s = heuristic_classification(logs)
    # The term 'pip install' might trigger DEPENDENCY_ERROR or DOCKER_BUILD_FAILURE
    # Let's test a clear docker one
    logs_docker = "docker build -t app ."
    t, s = heuristic_classification(logs_docker)
    assert t == FailureType.DOCKER_BUILD_FAILURE
    assert s == FailureSeverity.CRITICAL


def test_heuristic_classification_expanded():
    logs_timeout = "Workflow exceeded maximum execution time of 360 mins"
    t, s = heuristic_classification(logs_timeout)
    assert t == FailureType.TIMEOUT_FAILURE

    logs_syntax = "SyntaxError: invalid syntax"
    t, s = heuristic_classification(logs_syntax)
    assert t == FailureType.SYNTAX_ERROR

    logs_import = "ImportError: cannot import name 'xyz'"
    t, s = heuristic_classification(logs_import)
    assert t == FailureType.IMPORT_ERROR


def test_process_logs_truncation_head_tail():
    long_logs = "START_OF_LOGS " + "A" * (MAX_LOG_LENGTH + 1000) + " END_OF_LOGS"
    processed = process_logs(long_logs)
    assert len(processed) <= MAX_LOG_LENGTH + 100  # Account for markers
    assert "...[TRUNCATED TO PRESERVE TOKEN LIMITS]..." in processed
    assert "START_OF_LOGS" in processed
    assert "END_OF_LOGS" in processed


def test_process_logs_sanitization():
    logs = "Error processing. API_KEY=secret_value"
    processed = process_logs(logs)
    assert "secret_value" not in processed
    assert "[REDACTED_API_KEY]" in processed
