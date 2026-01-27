"""Revid.ai async client wrapper."""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.exceptions import RevidAPIError

_logger = logging.getLogger(__name__)


class RevidClient:
    """Handles Revid.ai video generation workflow calls."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        api_key: str,
        base_url: str,
        create_job_path: str,
        status_path: str,
        result_path: str,
        max_retries: int = 3,
        retry_backoff_factor: float = 1.5,
    ) -> None:
        self._http_client = http_client
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._create_job_path = create_job_path
        self._status_path = status_path
        self._result_path = result_path
        self._max_retries = max_retries
        self._retry_backoff_factor = retry_backoff_factor

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    async def create_video_job(self, *, text: str, image_url: str, language: str) -> Dict[str, Any]:
        """Submit a new video generation job to Revid.ai."""

        url = f"{self._base_url}{self._create_job_path}"
        payload = {"script": text, "image_url": image_url, "language": language}

        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._http_client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError as exc:  # pragma: no cover - defensive guard
                    raise RevidAPIError("Revid create job response was not valid JSON.") from exc
                if "job_id" not in data:
                    raise RevidAPIError("Revid response missing 'job_id'.")
                return data

            except httpx.HTTPStatusError as exc:
                # Only retry on server errors (5xx)
                if exc.response.status_code >= 500:
                    last_exception = exc
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_factor ** attempt
                        _logger.warning(
                            "Revid create_video_job failed with %d, retrying in %.2fs (attempt %d/%d)",
                            exc.response.status_code,
                            backoff,
                            attempt + 1,
                            self._max_retries,
                        )
                        await asyncio.sleep(backoff)
                        continue
                raise RevidAPIError(f"Revid create job failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                last_exception = exc
                if attempt < self._max_retries - 1:
                    backoff = self._retry_backoff_factor ** attempt
                    _logger.warning(
                        "Revid connection error: %s, retrying in %.2fs (attempt %d/%d)",
                        exc,
                        backoff,
                        attempt + 1,
                        self._max_retries,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise RevidAPIError(f"Revid request error: {exc}") from exc

        raise RevidAPIError(
            f"Revid create_video_job failed after {self._max_retries} attempts"
        ) from last_exception

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Fetch job status from Revid.ai for the supplied job identifier."""

        url = f"{self._base_url}{self._status_path.format(job_id=job_id)}"

        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._http_client.get(url, headers=self._headers())
                response.raise_for_status()

                try:
                    return response.json()
                except ValueError as exc:  # pragma: no cover - defensive guard
                    raise RevidAPIError("Revid status response was not valid JSON.") from exc

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500:
                    last_exception = exc
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_factor ** attempt
                        _logger.warning(
                            "Revid get_job_status failed with %d, retrying in %.2fs (attempt %d/%d)",
                            exc.response.status_code,
                            backoff,
                            attempt + 1,
                            self._max_retries,
                        )
                        await asyncio.sleep(backoff)
                        continue
                raise RevidAPIError(f"Revid status fetch failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                last_exception = exc
                if attempt < self._max_retries - 1:
                    backoff = self._retry_backoff_factor ** attempt
                    _logger.warning(
                        "Revid connection error: %s, retrying in %.2fs (attempt %d/%d)",
                        exc,
                        backoff,
                        attempt + 1,
                        self._max_retries,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise RevidAPIError(f"Revid request error: {exc}") from exc

        raise RevidAPIError(
            f"Revid get_job_status failed after {self._max_retries} attempts"
        ) from last_exception

    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the final video artifact, if ready."""

        url = f"{self._base_url}{self._result_path.format(job_id=job_id)}"

        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._http_client.get(url, headers=self._headers())
                if response.status_code == httpx.codes.NOT_FOUND:
                    return None
                response.raise_for_status()

                try:
                    return response.json()
                except ValueError as exc:  # pragma: no cover - defensive guard
                    raise RevidAPIError("Revid result response was not valid JSON.") from exc

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500:
                    last_exception = exc
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_factor ** attempt
                        _logger.warning(
                            "Revid get_job_result failed with %d, retrying in %.2fs (attempt %d/%d)",
                            exc.response.status_code,
                            backoff,
                            attempt + 1,
                            self._max_retries,
                        )
                        await asyncio.sleep(backoff)
                        continue
                raise RevidAPIError(f"Revid result fetch failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                last_exception = exc
                if attempt < self._max_retries - 1:
                    backoff = self._retry_backoff_factor ** attempt
                    _logger.warning(
                        "Revid connection error: %s, retrying in %.2fs (attempt %d/%d)",
                        exc,
                        backoff,
                        attempt + 1,
                        self._max_retries,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise RevidAPIError(f"Revid request error: {exc}") from exc

        raise RevidAPIError(
            f"Revid get_job_result failed after {self._max_retries} attempts"
        ) from last_exception
