"""Background music service for video generation."""

import logging
from typing import Dict, Optional
import httpx
import asyncio
import subprocess
import tempfile
import os

_logger = logging.getLogger(__name__)

class MusicService:
    """Service for adding background music to videos."""
    
    # Free royalty-free music tracks (short loops)
    MUSIC_LIBRARY = {
        "playful": {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "description": "Playful and fun music for energetic pets"
        },
        "happy": {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
            "description": "Happy upbeat music"
        },
        "calm": {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
            "description": "Calm and relaxing background music"
        },
        "energetic": {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
            "description": "High energy music for active pets"
        },
        "funny": {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
            "description": "Funny and silly music"
        },
        "cute": {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
            "description": "Cute and adorable music for sweet pets"
        }
    }
    
    def __init__(self):
        """Initialize music service."""
        self._http_client = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        return self._http_client
    
    def get_music_styles(self) -> Dict[str, str]:
        """Get available music styles."""
        return {
            style: info["description"] 
            for style, info in self.MUSIC_LIBRARY.items()
        }
    
    async def add_music_to_video(
        self,
        video_url: str,
        music_style: str = "playful",
        volume: float = 0.3,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """Add background music to a video.
        
        Args:
            video_url: URL of the video to add music to
            music_style: Music style from MUSIC_LIBRARY
            volume: Music volume (0.0 to 1.0)
            output_path: Optional output path, otherwise creates temp file
            
        Returns:
            Path to the video with music, or None if failed
        """
        try:
            # Get music info
            if music_style not in self.MUSIC_LIBRARY:
                _logger.warning(f"Unknown music style: {music_style}, using 'playful'")
                music_style = "playful"
            
            music_info = self.MUSIC_LIBRARY[music_style]
            music_url = music_info["url"]
            
            _logger.info(f"Adding {music_style} music to video (volume: {volume})")
            
            # Download video
            client = await self._get_http_client()
            video_response = await client.get(video_url)
            video_response.raise_for_status()
            
            # Create temp files
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
                video_file.write(video_response.content)
                video_path = video_file.name
            
            # Download music
            music_response = await client.get(music_url)
            music_response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as music_file:
                music_file.write(music_response.content)
                music_path = music_file.name
            
            # Output path
            if output_path is None:
                output_fd, output_path = tempfile.mkstemp(suffix=".mp4")
                os.close(output_fd)
            
            # Use ffmpeg to mix video with background music
            # Get video duration first
            duration_cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            
            try:
                duration_result = subprocess.run(
                    duration_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                video_duration = float(duration_result.stdout.strip())
            except Exception as e:
                _logger.warning(f"Could not get video duration: {e}, using 3 seconds")
                video_duration = 3.0
            
            # Mix audio: trim music to video length, adjust volume, mix with video
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", video_path,
                "-i", music_path,
                "-filter_complex",
                f"[1:a]atrim=0:{video_duration},volume={volume}[music];[music]aformat=sample_rates=44100[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                "-y",
                output_path
            ]
            
            _logger.debug(f"Running ffmpeg: {' '.join(ffmpeg_cmd)}")
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                _logger.error(f"FFmpeg error: {result.stderr}")
                # Return original video if music mixing fails
                return video_path
            
            # Cleanup temp files
            try:
                os.unlink(video_path)
                os.unlink(music_path)
            except Exception as e:
                _logger.warning(f"Could not cleanup temp files: {e}")
            
            _logger.info(f"✅ Successfully added {music_style} music to video")
            return output_path
            
        except Exception as e:
            _logger.error(f"Failed to add music to video: {e}")
            return None
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# Global instance
_music_service: Optional[MusicService] = None

def get_music_service() -> MusicService:
    """Get or create music service instance."""
    global _music_service
    if _music_service is None:
        _music_service = MusicService()
    return _music_service
