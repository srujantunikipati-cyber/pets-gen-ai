"""fal.ai async client wrapper for video generation."""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.exceptions import FalAPIError

_logger = logging.getLogger(__name__)


class FalClient:
    """Handles fal.ai video generation workflow calls."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        api_key: str,
        base_url: str,
        model_id: str,
        max_retries: int = 3,
        retry_backoff_factor: float = 1.5,
    ) -> None:
        self._http_client = http_client
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model_id = model_id
        self._max_retries = max_retries
        self._retry_backoff_factor = retry_backoff_factor

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Key {self._api_key}",
            "Content-Type": "application/json",
        }

    async def create_video_job(self, *, text: str, image_url: str, language: str = "en") -> Dict[str, Any]:
        """Submit a new video generation job to fal.ai.
        
        Args:
            text: The script/prompt text for the video
            image_url: URL of the input image
            language: Language code (default: "en")
            
        Returns:
            Dictionary containing job_id and status
        """
        # fal.ai uses queue API for async jobs
        # Format: https://queue.fal.run/{model_id}
        if "queue.fal.run" in self._base_url or "api.fal.ai" in self._base_url:
            # Use queue.fal.run directly
            url = f"https://queue.fal.run/{self._model_id}"
        else:
            url = f"{self._base_url}/v1/queue/{self._model_id}"
        
        _logger.info(f"fal.ai create_video_job: URL={url}, model_id={self._model_id}, base_url={self._base_url}")
        
        # Prepare payload according to fal.ai schema
        # Include webhook URL if configured
        payload = {
            "input": {
                "image_url": image_url,
                "prompt": text,
            }
        }
        
        # Add webhook URL if available (fal.ai supports webhook_url in request)
        # This allows fal.ai to notify us when the job completes
        # Note: This would need to be configured in settings
        
        _logger.debug(f"fal.ai payload: {payload}")

        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._http_client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError as exc:
                    raise FalAPIError("fal.ai create job response was not valid JSON.") from exc
                
                # fal.ai returns request_id as the job identifier
                request_id = data.get("request_id") or data.get("id")
                if not request_id:
                    raise FalAPIError("fal.ai response missing 'request_id' or 'id'.")
                
                # Normalize response format
                return {
                    "job_id": request_id,
                    "status": data.get("status", "queued"),
                    "detail": data.get("detail"),
                }

            except httpx.HTTPStatusError as exc:
                # Only retry on server errors (5xx)
                if exc.response.status_code >= 500:
                    last_exception = exc
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_factor ** attempt
                        _logger.warning(
                            "fal.ai create_video_job failed with %d, retrying in %.2fs (attempt %d/%d)",
                            exc.response.status_code,
                            backoff,
                            attempt + 1,
                            self._max_retries,
                        )
                        await asyncio.sleep(backoff)
                        continue
                raise FalAPIError(f"fal.ai create job failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                last_exception = exc
                if attempt < self._max_retries - 1:
                    backoff = self._retry_backoff_factor ** attempt
                    _logger.warning(
                        "fal.ai connection error: %s, retrying in %.2fs (attempt %d/%d)",
                        exc,
                        backoff,
                        attempt + 1,
                        self._max_retries,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise FalAPIError(f"fal.ai request error: {exc}") from exc

        raise FalAPIError(
            f"fal.ai create_video_job failed after {self._max_retries} attempts"
        ) from last_exception

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Fetch job status from fal.ai for the supplied job identifier.
        
        Args:
            job_id: The request_id from fal.ai
            
        Returns:
            Dictionary containing status, video_url if available, and other metadata
        """
        # fal.ai status endpoint format: https://queue.fal.run/{model_id}/requests/{job_id}/status
        if "queue.fal.run" in self._base_url or "api.fal.ai" in self._base_url:
            url = f"https://queue.fal.run/{self._model_id}/requests/{job_id}/status"
        else:
            url = f"{self._base_url}/v1/queue/{self._model_id}/requests/{job_id}/status"

        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._http_client.get(url, headers=self._headers())
                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError as exc:
                    raise FalAPIError("fal.ai status response was not valid JSON.") from exc
                
                # Normalize fal.ai response format
                status = data.get("status", "processing")
                # Normalize status to lowercase for consistency
                status = status.lower() if isinstance(status, str) else status
                video_url = None
                
                # Check if video is ready - fal.ai returns status as "COMPLETED" (uppercase)
                # When completed, the video URL might be in the response_url endpoint
                if status in ["completed", "COMPLETED"]:
                    # Check if video URL is in the response directly
                    if "video" in data:
                        video_data = data.get("video")
                        if isinstance(video_data, dict):
                            video_url = video_data.get("url") or video_data.get("urls", {}).get("mp4")
                        elif isinstance(video_data, str):
                            video_url = video_data
                
                return {
                    "status": status,
                    "video_url": video_url,
                    "detail": data.get("detail") or data.get("error"),
                }

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500:
                    last_exception = exc
                    if attempt < self._max_retries - 1:
                        backoff = self._retry_backoff_factor ** attempt
                        _logger.warning(
                            "fal.ai get_job_status failed with %d, retrying in %.2fs (attempt %d/%d)",
                            exc.response.status_code,
                            backoff,
                            attempt + 1,
                            self._max_retries,
                        )
                        await asyncio.sleep(backoff)
                        continue
                raise FalAPIError(f"fal.ai status fetch failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                last_exception = exc
                if attempt < self._max_retries - 1:
                    backoff = self._retry_backoff_factor ** attempt
                    _logger.warning(
                        "fal.ai connection error: %s, retrying in %.2fs (attempt %d/%d)",
                        exc,
                        backoff,
                        attempt + 1,
                        self._max_retries,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise FalAPIError(f"fal.ai request error: {exc}") from exc

        raise FalAPIError(
            f"fal.ai get_job_status failed after {self._max_retries} attempts"
        ) from last_exception

    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the final video artifact, if ready.
        
        Args:
            job_id: The request_id from fal.ai
            
        Returns:
            Dictionary containing video_url if available, None if not ready
        """
        # First, get the status to check if completed
        status_data = await self.get_job_status(job_id)
        status = status_data.get("status", "").lower()
        
        # If already have video_url from status, return it
        if status == "completed" and status_data.get("video_url"):
            return {
                "video_url": status_data["video_url"],
                "status": "completed",
            }
        
        # If not completed, return None
        if status not in ["completed"]:
            return None
        
        # For completed jobs without video_url in status, try to fetch from response_url
        # Get status again to get response_url
        status_url = f"https://queue.fal.run/{self._model_id}/requests/{job_id}/status"
        try:
            status_resp = await self._http_client.get(status_url, headers=self._headers())
            status_resp.raise_for_status()
            status_json = status_resp.json()
            response_url = status_json.get("response_url")
            
            if response_url:
                # Try GET on response_url - some fal.ai APIs return result here
                try:
                    result_resp = await self._http_client.get(response_url, headers=self._headers())
                    if result_resp.status_code == 200:
                        result_data = result_resp.json()
                        # Check for video in various possible locations
                        video_url = None
                        if "video" in result_data:
                            video_data = result_data["video"]
                            if isinstance(video_data, str):
                                video_url = video_data
                            elif isinstance(video_data, dict):
                                video_url = video_data.get("url") or video_data.get("urls", {}).get("mp4")
                        elif "output" in result_data:
                            output = result_data["output"]
                            if isinstance(output, dict) and "video" in output:
                                video_data = output["video"]
                                if isinstance(video_data, str):
                                    video_url = video_data
                                elif isinstance(video_data, dict):
                                    video_url = video_data.get("url") or video_data.get("urls", {}).get("mp4")
                        
                        if video_url:
                            _logger.info(f"✅ Found video URL for job {job_id}: {video_url}")
                            return {
                                "video_url": video_url,
                                "status": "completed",
                            }
                except Exception as e:
                    _logger.debug(f"Failed to fetch from response_url {response_url}: {e}")
        except Exception as e:
            _logger.debug(f"Error fetching response_url: {e}")
        
        # If all methods fail, the video URL should come via webhook
        _logger.warning(
            f"Job {job_id} is completed but video_url not found. "
            "Video URL should be delivered via webhook when job completes."
        )
        
        return None
