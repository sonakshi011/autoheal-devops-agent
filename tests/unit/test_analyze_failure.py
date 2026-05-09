import pytest
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.analyze_failure import generate_fallback_diagnosis
from ai_engine.models.failure import FailurePayload, FailureSeverity, FailureType
from ai_engine.models.responses import AIDiagnosisResponse

@pytest.fixture
def mock_payload():
    return FailurePayload(
        workflow_name="CI Test",
        job_name="test-job",
        step_name="run-tests",
        exit_code=1,
        logs="Error 404: Not Found",
        timestamp=datetime.now(timezone.utc),
        severity=FailureSeverity.HIGH,
        failure_type=FailureType.TEST_FAILURE
    )

def test_generate_fallback_diagnosis(mock_payload):
    error_msg = "Gemini API Timeout"
    fallback = generate_fallback_diagnosis(mock_payload, error_msg)
    
    assert fallback.model_used == "fallback-heuristic"
    assert fallback.confidence_score == 0
    assert fallback.severity == mock_payload.severity
    assert "Original error: Gemini API Timeout" in fallback.root_cause
    assert len(fallback.remediation_steps) > 0
    assert fallback.code_suggestion is None

def test_diagnosis_response_schema_validation():
    # Valid data
    data = {
        "root_cause": "The test failed.",
        "severity": "high",
        "remediation_steps": ["Fix the code"],
        "confidence_score": 95,
        "model_used": "gemini-test",
        "diagnosis_timestamp": datetime.now(timezone.utc).isoformat()
    }
    resp = AIDiagnosisResponse(**data)
    assert resp.confidence_score == 95
    
    # Invalid confidence score (should be 0-100)
    with pytest.raises(ValueError):
        invalid_data = data.copy()
        invalid_data["confidence_score"] = 150
        AIDiagnosisResponse(**invalid_data)
        
    # Missing required field
    with pytest.raises(ValueError):
        missing_data = data.copy()
        del missing_data["root_cause"]
        AIDiagnosisResponse(**missing_data)
