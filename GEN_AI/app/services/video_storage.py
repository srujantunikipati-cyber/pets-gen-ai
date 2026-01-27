"""Video storage service for downloading and saving generated videos."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import httpx

_logger = logging.getLogger(__name__)


class VideoStorageService:
    """Service for downloading and storing video files."""

    def __init__(self, storage_path: str = "storage/videos"):
        """Initialize video storage service.
        
        Args:
            storage_path: Base directory path for storing videos
        """
        self.storage_path = Path(storage_path)
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            # Ensure directory is writable
            os.chmod(self.storage_path, 0o755)
            _logger.info(f"📁 Video storage initialized at: {self.storage_path.absolute()}")
        except Exception as e:
            _logger.warning(f"⚠️  Failed to create storage directory: {e}. Using /tmp as fallback.")
            self.storage_path = Path("/tmp/videos")
            self.storage_path.mkdir(parents=True, exist_ok=True)

    async def download_and_save_video(
        self,
        video_url: str,
        job_id: str,
        timeout: float = 60.0,
    ) -> Optional[str]:
        """Download video from URL and save to storage.
        
        Args:
            video_url: URL of the video to download
            job_id: Job identifier for filename
            timeout: Download timeout in seconds
            
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            _logger.info(f"📥 Downloading video for job {job_id} from: {video_url}")
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{job_id}_{timestamp}.mp4"
            file_path = self.storage_path / filename
            
            # Download video
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
                response = await client.get(video_url)
                response.raise_for_status()
                
                # Save to file
                with open(file_path, "wb") as f:
                    f.write(response.content)
            
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            _logger.info(
                f"✅ Video saved successfully: {file_path.absolute()} "
                f"({file_size_mb:.2f} MB)"
            )
            
            return str(file_path.absolute())
            
        except httpx.HTTPError as e:
            _logger.error(f"❌ Failed to download video from {video_url}: {e}")
            return None
        except Exception as e:
            _logger.exception(f"❌ Error saving video for job {job_id}: {e}")
            return None

    def get_video_path(self, job_id: str) -> Optional[str]:
        """Get local file path for a video by job_id.
        
        Args:
            job_id: Job identifier
            
        Returns:
            File path if found, None otherwise
        """
        # Search for files starting with job_id
        for file_path in self.storage_path.glob(f"{job_id}_*.mp4"):
            return str(file_path.absolute())
        return None

    def list_videos(self) -> list[str]:
        """List all stored video files.
        
        Returns:
            List of file paths
        """
        return [str(f.absolute()) for f in self.storage_path.glob("*.mp4")]

    def delete_video(self, job_id: str) -> bool:
        """Delete video file by job_id.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted, False otherwise
        """
        video_path = self.get_video_path(job_id)
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                _logger.info(f"🗑️  Deleted video: {video_path}")
                return True
            except Exception as e:
                _logger.error(f"❌ Failed to delete video {video_path}: {e}")
                return False
        return False
