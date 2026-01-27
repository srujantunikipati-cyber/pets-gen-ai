"""Redis-backed persistent job storage for video generation workflows."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis

from .job_store import JobRecord, JobStatus

_logger = logging.getLogger(__name__)


class RedisJobStore:
    """Persistent job storage using Redis.

    Stores job records as JSON strings with TTL for automatic cleanup.
    Maintains backward compatibility with in-memory JobStore interface.
    """

    def __init__(self, redis_url: str, ttl_seconds: int = 86400 * 7) -> None:
        """
        Initialize Redis connection.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            ttl_seconds: Time-to-live for job records in seconds (default: 7 days)
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._redis: Optional[redis.Redis] = None
        self._key_prefix = "pet_roast:job:"

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            pong = await self._redis.ping()  # type: ignore[misc]
            if not pong:
                raise ConnectionError("Redis ping failed")
            _logger.info(f"✅ Connected to Redis at {self.redis_url}")
        except Exception as e:
            _logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            _logger.info("Redis connection closed")

    def _make_key(self, job_id: str) -> str:
        """Generate Redis key for a job."""
        return f"{self._key_prefix}{job_id}"

    def _serialize_record(self, record: JobRecord) -> str:
        """Convert JobRecord to JSON string."""
        return json.dumps({
            "job_id": record.job_id,
            "status": record.status.value,
            "text": record.text,
            "image_url": record.image_url,
            "language": record.language,
            "video_url": record.video_url,
            "detail": record.detail,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        })

    def _deserialize_record(self, data: str) -> JobRecord:
        """Convert JSON string to JobRecord."""
        obj = json.loads(data)
        return JobRecord(
            job_id=obj["job_id"],
            status=JobStatus(obj["status"]),
            text=obj["text"],
            image_url=obj["image_url"],
            language=obj["language"],
            video_url=obj.get("video_url"),
            detail=obj.get("detail"),
            created_at=datetime.fromisoformat(obj["created_at"]),
            updated_at=datetime.fromisoformat(obj["updated_at"]),
        )

    async def upsert(self, record: JobRecord) -> None:
        """Insert or replace a job record with TTL."""
        if not self._redis:
            raise RuntimeError("Redis not connected. Call connect() first.")

        key = self._make_key(record.job_id)
        data = self._serialize_record(record)
        await self._redis.setex(key, self.ttl_seconds, data)
        _logger.debug(f"Stored job {record.job_id} with status {record.status}")

    async def get(self, job_id: str) -> Optional[JobRecord]:
        """Retrieve job record by ID."""
        if not self._redis:
            raise RuntimeError("Redis not connected. Call connect() first.")

        key = self._make_key(job_id)
        data = await self._redis.get(key)

        if data is None:
            return None

        return self._deserialize_record(data)

    async def update(
        self,
        job_id: str,
        *,
        status: Optional[JobStatus] = None,
        video_url: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> Optional[JobRecord]:
        """Update existing job record and return updated record."""
        if not self._redis:
            raise RuntimeError("Redis not connected. Call connect() first.")

        record = await self.get(job_id)
        if record is None:
            return None

        # Apply updates
        if status is not None:
            record.status = status
        if video_url is not None:
            record.video_url = video_url
        if detail is not None:
            record.detail = detail
        record.updated_at = datetime.now(timezone.utc)

        # Save updated record
        await self.upsert(record)
        return record

    async def delete(self, job_id: str) -> bool:
        """Delete a job record. Returns True if deleted, False if not found."""
        if not self._redis:
            raise RuntimeError("Redis not connected. Call connect() first.")

        key = self._make_key(job_id)
        result = await self._redis.delete(key)
        return result > 0

    async def exists(self, job_id: str) -> bool:
        """Check if a job record exists."""
        if not self._redis:
            raise RuntimeError("Redis not connected. Call connect() first.")

        key = self._make_key(job_id)
        result = await self._redis.exists(key)
        return result > 0
