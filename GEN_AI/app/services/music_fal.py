"""Background music service for video generation using FAL.ai."""

import logging
from typing import Dict, Optional
import httpx
import asyncio
import subprocess
import tempfile
import os

_logger = logging.getLogger(__name__)

class MusicServiceFal:
    """Service for generating and adding background music to videos using FAL.ai."""
    
    # Pet-themed music prompts for FAL.ai MusicGen
    MUSIC_PROMPTS = {
        "playful": "upbeat playful music with light percussion, fun and energetic, perfect for cute pets playing",
        "happy": "cheerful happy music with bright melodies, joyful and uplifting, pet-friendly background",
        "calm": "calm relaxing music with gentle piano, peaceful and soothing, for calm pets",
        "energetic": "high energy music with fast tempo, exciting and dynamic, for active playful pets",
        "funny": "silly comedic music with quirky sounds, humorous and lighthearted, for funny pet moments",
        "cute": "sweet adorable music with soft melodies, warm and tender, for cute lovable pets"
    }
    
    def __init__(self, fal_api_key: Optional[str] = None):
        """Initialize music service.
        
        Args:
            fal_api_key: FAL.ai API key for music generation
        """
        self._fal_api_key = fal_api_key
        self._http_client = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        return self._http_client
    
    def get_music_styles(self) -> Dict[str, str]:
        """Get available music styles."""
        return {
            style: prompt 
            for style, prompt in self.MUSIC_PROMPTS.items()
        }
    
    async def generate_music_with_fal(
        self,
        music_style: str = "playful",
        duration: float = 10.0
    ) -> Optional[str]:
        """Generate background music using FAL.ai MusicGen.
        
        Args:
            music_style: Music style from MUSIC_PROMPTS
            duration: Duration in seconds (default: 10.0)
            
        Returns:
            URL of generated music, or None if failed
        """
        if not self._fal_api_key:
            _logger.warning("No FAL.ai API key, skipping music generation")
            return None
        
        try:
            # Get music prompt
            if music_style not in self.MUSIC_PROMPTS:
                _logger.warning(f"Unknown music style: {music_style}, using 'playful'")
                music_style = "playful"
            
            prompt = self.MUSIC_PROMPTS[music_style]
            
            _logger.info(f"🎵 Generating {music_style} music with FAL.ai MusicGen...")
            _logger.info(f"Prompt: {prompt}")
            
            # Call FAL.ai MusicGen API
            client = await self._get_http_client()
            
            payload = {
                "prompt": prompt,
                "duration": duration,
                "temperature": 1.0,
                "top_k": 250,
                "top_p": 0.0
            }
            
            headers = {
                "Authorization": f"Key {self._fal_api_key}",
                "Content-Type": "application/json"
            }
            
            # Submit music generation job
            response = await client.post(
                "https://queue.fal.run/fal-ai/musicgen",
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            request_id = result.get("request_id")
            if not request_id:
                _logger.error("No request_id from FAL.ai MusicGen")
                return None
            
            _logger.info(f"Music generation started: {request_id}")
            
            # Poll for completion (music generation can take 2-3 minutes)
            max_attempts = 90  # 3 minutes (poll every 2 seconds)
            for attempt in range(max_attempts):
                await asyncio.sleep(2)  # Poll every 2 seconds
                
                status_response = await client.get(
                    f"https://queue.fal.run/fal-ai/musicgen/requests/{request_id}/status",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status_value = status_data.get("status", "").upper()
                    
                    if status_value == "COMPLETED":
                        # Get the result
                        result_response = await client.get(
                            f"https://queue.fal.run/fal-ai/musicgen/requests/{request_id}",
                            headers=headers
                        )
                        
                        if result_response.status_code == 200:
                            result_data = result_response.json()
                            audio_url = result_data.get("audio_file", {}).get("url")
                            
                            if audio_url:
                                _logger.info(f"✅ Music generated: {audio_url}")
                                return audio_url
                            else:
                                _logger.error(f"No audio URL in result: {result_data}")
                                return None
                    elif status_value == "FAILED":
                        error = status_data.get("error", "Unknown error")
                        _logger.error(f"Music generation failed: {error}")
                        return None
            
            _logger.warning(f"Music generation timed out after {max_attempts * 2}s")
            return None
            
        except Exception as e:
            _logger.error(f"Failed to generate music with FAL.ai: {e}")
            return None
    
    async def merge_video_and_music(
        self,
        video_url: str,
        music_url: str,
        volume: float = 0.3,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """Merge video and music using ffmpeg.
        
        Args:
            video_url: URL of the video
            music_url: URL of the music
            volume: Music volume (0.0 to 1.0)
            output_path: Optional output path, otherwise creates temp file
            
        Returns:
            Path to the merged video, or None if failed
        """
        try:
            _logger.info(f"Merging video with music (volume: {volume})")
            
            # Download video and music
            client = await self._get_http_client()
            
            video_response = await client.get(video_url)
            video_response.raise_for_status()
            
            music_response = await client.get(music_url)
            music_response.raise_for_status()
            
            # Save to temp files
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
                video_file.write(video_response.content)
                video_path = video_file.name
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as music_file:
                music_file.write(music_response.content)
                music_path = music_file.name
            
            try:
                # Create output path if not provided
                if output_path is None:
                    output_fd, output_path = tempfile.mkstemp(suffix=".mp4")
                    os.close(output_fd)
                
                # Mix audio with ffmpeg
                # -shortest ensures output is as long as the shortest input
                # volume filter adjusts music volume
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", music_path,
                    "-filter_complex",
                    f"[1:a]volume={volume}[a1];[0:a][a1]amix=inputs=2:duration=shortest[aout]",
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    output_path
                ]
                
                _logger.info(f"Running ffmpeg: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    _logger.error(f"ffmpeg failed: {result.stderr}")
                    return None
                
                _logger.info(f"✅ Video merged with music: {output_path}")
                return output_path
                
            finally:
                # Clean up temp files
                try:
                    os.unlink(video_path)
                    os.unlink(music_path)
                except Exception as e:
                    _logger.warning(f"Failed to clean up temp files: {e}")
            
        except Exception as e:
            _logger.error(f"Failed to merge video and music: {e}")
            return None
