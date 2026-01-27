"""Service for extracting audio from video files."""

import logging
import tempfile
import os
from pathlib import Path
from typing import Optional
import base64
import io

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    _logger = logging.getLogger(__name__)
    _logger.warning("moviepy not available. Install with: pip install moviepy")

_logger = logging.getLogger(__name__)


class AudioExtractionError(Exception):
    """Raised when audio extraction fails."""


class AudioExtractionService:
    """Service for extracting audio from video files."""

    def __init__(self):
        if not MOVIEPY_AVAILABLE:
            raise ImportError(
                "moviepy is required for audio extraction. "
                "Install with: pip install moviepy"
            )

    async def extract_audio_from_video_data(
        self, video_data: str, output_format: str = "wav"
    ) -> bytes:
        """Extract audio from base64-encoded video data.
        
        Args:
            video_data: Base64-encoded video data (data:video/...;base64,...)
            output_format: Output audio format (wav, mp3, etc.)
            
        Returns:
            Audio file as bytes
        """
        try:
            # Parse data URL
            if video_data.startswith("data:video/"):
                # Extract base64 part
                header, base64_data = video_data.split(",", 1)
                video_bytes = base64.b64decode(base64_data)
            else:
                # Assume it's already base64
                video_bytes = base64.b64decode(video_data)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video.write(video_bytes)
                temp_video_path = temp_video.name
            
            try:
                # Extract audio using moviepy
                video = VideoFileClip(temp_video_path)
                audio = video.audio
                
                if audio is None:
                    raise AudioExtractionError("No audio track found in video")
                
                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as temp_audio:
                    temp_audio_path = temp_audio.name
                
                try:
                    audio.write_audiofile(
                        temp_audio_path,
                        codec='pcm_s16le' if output_format == 'wav' else 'libmp3lame',
                        verbose=False,
                        logger=None
                    )
                    
                    # Read audio file
                    with open(temp_audio_path, 'rb') as f:
                        audio_bytes = f.read()
                    
                    return audio_bytes
                    
                finally:
                    # Cleanup audio file
                    if os.path.exists(temp_audio_path):
                        os.unlink(temp_audio_path)
                    audio.close()
                    
            finally:
                # Cleanup video file
                video.close()
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                    
        except Exception as e:
            _logger.exception("Failed to extract audio from video")
            raise AudioExtractionError(f"Audio extraction failed: {str(e)}") from e

    async def extract_audio_from_video_file(
        self, video_path: str, output_format: str = "wav"
    ) -> bytes:
        """Extract audio from video file path.
        
        Args:
            video_path: Path to video file
            output_format: Output audio format (wav, mp3, etc.)
            
        Returns:
            Audio file as bytes
        """
        try:
            # Extract audio using moviepy
            video = VideoFileClip(video_path)
            audio = video.audio
            
            if audio is None:
                raise AudioExtractionError("No audio track found in video")
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as temp_audio:
                temp_audio_path = temp_audio.name
            
            try:
                audio.write_audiofile(
                    temp_audio_path,
                    codec='pcm_s16le' if output_format == 'wav' else 'libmp3lame',
                    verbose=False,
                    logger=None
                )
                
                # Read audio file
                with open(temp_audio_path, 'rb') as f:
                    audio_bytes = f.read()
                
                return audio_bytes
                
            finally:
                # Cleanup audio file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                audio.close()
                video.close()
                
        except Exception as e:
            _logger.exception("Failed to extract audio from video file")
            raise AudioExtractionError(f"Audio extraction failed: {str(e)}") from e


def get_audio_extraction_service() -> Optional[AudioExtractionService]:
    """Get audio extraction service instance."""
    if not MOVIEPY_AVAILABLE:
        return None
    return AudioExtractionService()
