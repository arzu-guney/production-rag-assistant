from __future__ import annotations

from google import genai
from google.genai import types

from app.core.exceptions import ConfigurationError, GenerationError


class GeminiService:
    """Thin wrapper around the Google Gen AI SDK for grounded generation."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ConfigurationError(
                "GEMINI_API_KEY is not set. Copy backend/.env.example to "
                "backend/.env and add your API key."
            )
        self.model = model
        self._client = genai.Client(api_key=api_key)

    async def generate(self, *, system_instruction: str, user_prompt: str) -> str:
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                ),
            )
        except ConfigurationError:
            raise
        except Exception as exc:  # noqa: BLE001 - surface provider failures cleanly
            raise GenerationError(f"Gemini request failed: {exc}") from exc

        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise GenerationError("Gemini returned an empty response.")
        return text
