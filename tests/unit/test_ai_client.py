import pytest
import os
from unittest.mock import patch, MagicMock
from google.genai.errors import APIError
from google.genai.types import GenerateContentResponse

from ai_engine.client import GeminiClient
from ai_engine.exceptions import AIClientError


@pytest.fixture
def mock_genai_client():
    with patch("ai_engine.client.genai.Client") as mock_client:
        mock_instance = mock_client.return_value
        yield mock_instance


def test_client_init_no_api_key():
    with patch("ai_engine.client.settings.gemini_api_key", None):
        with pytest.raises(AIClientError, match="GEMINI_API_KEY is not set"):
            GeminiClient()


def test_client_init_with_api_key():
    client = GeminiClient(api_key="test_key")
    assert client.api_key == "test_key"


def test_client_model_comes_from_settings():
    """default_model must reflect settings, not a hardcoded constant."""
    with patch("ai_engine.client.settings.gemini_default_model", "gemini-custom-test"):
        client = GeminiClient(api_key="test_key")
        assert client.default_model == "gemini-custom-test"


def test_generate_content_success(mock_genai_client):
    # Setup mock response
    mock_response = MagicMock(spec=GenerateContentResponse)
    mock_response.text = '{"root_cause": "Typo in variable"}'
    mock_genai_client.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="test_key")
    result = client.generate_content_with_retry(prompt="Analyze this")

    assert result == '{"root_cause": "Typo in variable"}'
    mock_genai_client.models.generate_content.assert_called_once()


@patch("ai_engine.client.time.sleep")
def test_generate_content_retry_on_429(mock_sleep, mock_genai_client):
    # Setup mock to fail twice with 429, then succeed
    mock_error = APIError(code=429, response_json={"error": "Too Many Requests"})

    mock_success = MagicMock(spec=GenerateContentResponse)
    mock_success.text = '{"success": true}'

    mock_genai_client.models.generate_content.side_effect = [mock_error, mock_error, mock_success]

    client = GeminiClient(api_key="test_key")
    result = client.generate_content_with_retry(prompt="Test retry")

    assert result == '{"success": true}'
    assert mock_genai_client.models.generate_content.call_count == 3
    assert mock_sleep.call_count == 2
