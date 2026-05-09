import time
import logging
from typing import Optional, Dict, Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from ai_engine.exceptions import AIClientError

logger = logging.getLogger("autoheal.ai")


class GeminiClient:
    """Client for interacting with the Google Gemini API with built-in retry logic."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini Client.
        Falls back to pydantic settings (which reads from .env) if not provided.
        Model names are always read from settings — never hardcoded here.
        """
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise AIClientError("GEMINI_API_KEY is not set or provided in environment.")

        self.default_model = settings.gemini_default_model
        self.complex_model = settings.gemini_complex_model
        self.client = genai.Client(api_key=self.api_key)

        # Safe startup log — shows model configuration but never the API key
        logger.info(
            f"GeminiClient initialised | environment={settings.environment} "
            f"| default_model={self.default_model} "
            f"| complex_model={self.complex_model}"
        )

    def generate_content_with_retry(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_retries: int = 3,
        system_instruction: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> str:
        """
        Generate content using Gemini API with exponential backoff retry logic.
        If model is not specified, falls back to settings.gemini_default_model.
        """
        # Resolve model at call-time so it always reflects current settings
        model = model or self.default_model
        attempt = 0
        backoff_times = [1, 2, 4]  # seconds

        config_args = {"temperature": temperature}
        if system_instruction:
            config_args["system_instruction"] = system_instruction
        if response_schema:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_args)

        while attempt <= max_retries:
            try:
                start_time = time.time()
                response = self.client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
                latency = time.time() - start_time
                logger.info(
                    f"gemini_call_complete model={model} attempt={attempt + 1} "
                    f"latency_ms={latency * 1000:.2f}"
                )

                if not response.text:
                    raise AIClientError("Empty response received from Gemini API.")

                return response.text

            except APIError as e:
                # E.g. 429 Too Many Requests or 500 Internal Server Error
                status_code = getattr(e, "code", None)
                if status_code in (429, 500, 503) and attempt < max_retries:
                    sleep_time = backoff_times[attempt]
                    logger.warning(
                        f"Gemini API error {status_code}: retrying in {sleep_time}s... (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(sleep_time)
                    attempt += 1
                else:
                    logger.error(f"Gemini API request failed after {attempt} retries: {str(e)}")
                    raise AIClientError(f"Gemini API request failed: {str(e)}") from e
            except Exception as e:
                logger.error(f"Unexpected error during Gemini API call: {str(e)}")
                raise AIClientError(f"Unexpected error: {str(e)}") from e

        raise AIClientError("Maximum retries exceeded.")
