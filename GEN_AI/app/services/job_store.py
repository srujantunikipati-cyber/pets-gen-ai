"""In-memory job tracking utilities for video generation workflows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class JobStatus(str, Enum):
    """Represents lifecycle states for asynchronous video generation."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobRecord:
    """Stores job metadata and latest status."""

    job_id: str
    status: JobStatus
    text: str
    image_url: str
    language: str
    video_url: Optional[str] = None
    detail: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update(
        self,
        *,
        status: Optional[JobStatus] = None,
        video_url: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        """Apply updates to the record."""

        if status is not None:
            self.status = status
        if video_url is not None:
            self.video_url = video_url
        if detail is not None:
            self.detail = detail
        self.updated_at = datetime.now(timezone.utc)


class JobStore:
    """Simple asynchronous storage for job state.

    Intended for prototypes. Replace with persistent storage for production.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def upsert(self, record: JobRecord) -> None:
        """Insert or replace a job record."""

        async with self._lock:
            self._jobs[record.job_id] = record

    async def get(self, job_id: str) -> Optional[JobRecord]:
        """Return job record if it exists."""

        async with self._lock:
            return self._jobs.get(job_id)

    async def update(
        self,
        job_id: str,
        *,
        status: Optional[JobStatus] = None,
        video_url: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> Optional[JobRecord]:
        """Apply updates to an existing job and return the result."""

        async with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            record.update(status=status, video_url=video_url, detail=detail)
            return record
