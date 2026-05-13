"""
Async Gemini API client with retry logic.
"""

import json
import re

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Async wrapper for the Google Gemini API."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model = settings.llm_model
        self.max_context = settings.llm_max_context_tokens
        self.default_max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("no_gemini_api_key", msg="LLM features will be disabled")

    @property
    def is_available(self) -> bool:
        return self.client is not None and bool(self.api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def send_message(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int | None = None,
    ) -> str:
        """
        Send a message to Gemini and return the text response.

        Args:
            user_prompt: The user message
            system_prompt: System/instructions prompt
            max_tokens: Max response tokens

        Returns:
            Response text string
        """
        if not self.is_available:
            raise RuntimeError("Gemini API client not configured. Set GEMINI_API_KEY.")

        config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=max_tokens or self.default_max_tokens,
            system_instruction=system_prompt if system_prompt else None,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=config,
        )

        text = response.text
        logger.info("llm_response", response_length=len(text) if text else 0)
        return text

    async def send_json_message(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int | None = None,
    ) -> dict:
        """Send message and parse JSON response."""
        if not self.is_available:
            raise RuntimeError("Gemini API client not configured. Set GEMINI_API_KEY.")

        config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=max_tokens or self.default_max_tokens,
            system_instruction=system_prompt if system_prompt else None,
            response_mime_type="application/json",
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=config,
        )

        text = response.text
        
        # Try to extract JSON from response
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON block in response
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            json_match = re.search(r'\[[\s\S]*\]', text)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")
