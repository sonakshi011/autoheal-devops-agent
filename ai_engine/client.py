import os
import time
import logging
from typing import Optional, Dict, Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from ai_engine.exceptions import AIClientError

logger = logging.getLogger("autoheal.ai")


class GeminiClient:
    """Client for interacting with the Google Gemini API with built-in retry logic."""

    DEFAULT_MODEL = "gemini-2.0-flash"
    COMPLEX_MODEL = "gemini-2.5-pro"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini Client.
        Falls back to GEMINI_API_KEY environment variable if not provided.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise AIClientError("GEMINI_API_KEY is not set or provided.")

        self.client = genai.Client(api_key=self.api_key)

    def generate_content_with_retry(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        max_retries: int = 3,
        system_instruction: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> str:
        """
        Generate content using Gemini API with exponential backoff retry logic.
        """
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
