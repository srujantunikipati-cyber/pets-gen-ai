"""AI4Bharat LLM client for translation and understanding tasks."""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.exceptions import AI4BharatAPIError

_logger = logging.getLogger(__name__)


class AI4BharatClient:
    """Async wrapper around an AI4Bharat-compatible inference endpoint."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        base_url: str,
        translate_path: str,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_factor: float = 1.5,
    ) -> None:
        self._http_client = http_client
        self._base_url = base_url.rstrip("/")
        self._translate_path = translate_path
        self._api_key = api_key
        self._max_retries = max_retries
        self._retry_backoff_factor = retry_backoff_factor

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def translate_text(
        self,
        *,
        text: str,
        source_language: Optional[str] = None,
        target_language: str = "en",
        task: str = "translation",
    ) -> Dict[str, Any]:
        """Call IndicTrans2 (AI4Bharat) to translate Indian language text.

        IndicTrans2 supports: Hindi (hi), Bengali (bn), Gujarati (gu), Marathi (mr),
        Kannada (kn), Telugu (te), Malayalam (ml), Tamil (ta), Punjabi (pa), Odia (or),
        Assamese (as), Urdu (ur), and English (en).
        """

        # IndicTrans2 API format
        payload: Dict[str, Any] = {
            "input": text,
            "source_language": source_language or "auto",
            "target_language": target_language,
        }
        url = f"{self._base_url}{self._translate_path}"

        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._http_client.post(
                    url,
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()

                # Success - parse and normalize IndicTrans2 response
                try:
                    result = response.json()
                    # Normalize IndicTrans2 response format to match expected interface
                    return {
                        "translated_text": result.get("output", result.get("translation", text)),
                        "source_language": source_language or result.get("detected_language", "auto"),
                        "target_language": target_language,
                        "task": task,
                    }
                except ValueError as exc:  # pragma: no cover - defensive guard
                    raise AI4BharatAPIError(
                        "AI4Bharat response was not valid JSON."
                    ) from exc

            except httpx.HTTPStatusError as exc:
                # Only retry on server errors (5xx)
                if exc.response.status_code >= 500:
                    last_exception = exc
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_factor ** attempt
                        _logger.warning(
                            "AI4Bharat translation failed with %d, retrying in %.2fs (attempt %d/%d)",
                            exc.response.status_code,
                            backoff,
                            attempt + 1,
                            self._max_retries,
                        )
                        await asyncio.sleep(backoff)
                        continue
                # Client errors (4xx) or final attempt - raise immediately
                raise AI4BharatAPIError(
                    f"AI4Bharat translation failed: {exc.response.text}"
                ) from exc

            except httpx.HTTPError as exc:
                # Retry on connection errors
                last_exception = exc
                if attempt < self._max_retries - 1:
                    backoff = self._retry_backoff_factor ** attempt
                    _logger.warning(
                        "AI4Bharat connection error: %s, retrying in %.2fs (attempt %d/%d)",
                        exc,
                        backoff,
                        attempt + 1,
                        self._max_retries,
                    )
                    await asyncio.sleep(backoff)
                    continue
                # Final attempt - raise
                raise AI4BharatAPIError(
                    f"AI4Bharat request error: {exc}"
                ) from exc

        # Should not reach here, but handle gracefully
        raise AI4BharatAPIError(
            f"AI4Bharat request failed after {self._max_retries} attempts"
        ) from last_exception
