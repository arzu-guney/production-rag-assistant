from __future__ import annotations

from google import genai
from google.genai import types

from app.core.exceptions import ConfigurationError, GenerationError

_PLACEHOLDER_KEYS = {
    "your_gemini_api_key_here",
    "changeme",
    "replace_me",
    "xxx",
    "todo",
}

# Hard request timeout (milliseconds) for the google-genai HTTP client.
# 60s is enough for a short grounded answer but fails cleanly instead of hanging.
DEFAULT_HTTP_TIMEOUT_MS = 60_000

# google-genai defaults to 5 attempts with exponential backoff (up to 60s delay)
# for retryable codes including 429. For this portfolio app we disable retries so
# one failed call cannot multiply quota usage or look like a freeze.
DEFAULT_HTTP_RETRY_ATTEMPTS = 1


class GeminiService:
    """Thin wrapper around the Google Gen AI SDK for grounded generation."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        timeout_ms: int = DEFAULT_HTTP_TIMEOUT_MS,
        retry_attempts: int = DEFAULT_HTTP_RETRY_ATTEMPTS,
    ) -> None:
        cleaned = api_key.strip()
        if not cleaned:
            raise ConfigurationError(
                "GEMINI_API_KEY is not set. Copy backend/.env.example to "
                "backend/.env and add your API key."
            )
        if cleaned.lower() in _PLACEHOLDER_KEYS or cleaned.lower().startswith("your_"):
            raise ConfigurationError(
                "GEMINI_API_KEY in backend/.env is still the placeholder value. "
                "Replace it with a real key from Google AI Studio, then restart the server."
            )
        self.model = model
        self.timeout_ms = timeout_ms
        self.retry_attempts = retry_attempts
        # Explicit API-key auth for the Gemini Developer API (not Vertex AI).
        self._client = genai.Client(
            api_key=cleaned,
            http_options=types.HttpOptions(
                timeout=timeout_ms,
                retry_options=types.HttpRetryOptions(attempts=retry_attempts),
            ),
        )

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
        except Exception as exc:  # noqa: BLE001
            raise GenerationError(_public_generation_error(exc)) from exc

        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise GenerationError("Gemini returned an empty response.")
        return text


def _public_generation_error(exc: Exception) -> str:
    """Return a client-safe message; keep provider detail on the exception chain."""
    text = str(exc).lower()
    if "api_key_invalid" in text or "api key not valid" in text:
        return (
            "Gemini authentication failed. Check that backend/.env contains a valid "
            "GEMINI_API_KEY (not the placeholder) and restart the API server."
        )
    if "429" in text or "resource_exhausted" in text or "rate" in text:
        return (
            "Gemini rate limit reached. Wait and retry manually later, or use "
            "--max-cases 1 with a longer --delay-seconds in live evaluation."
        )
    if "timeout" in text or "timed out" in text:
        return "Gemini request timed out. Try again later or increase the request timeout."
    if "not found" in text and "model" in text:
        return (
            "Gemini model request failed. Check GEMINI_MODEL in backend/.env "
            "and restart the API server."
        )
    return "Gemini request failed. Check server logs for details."
