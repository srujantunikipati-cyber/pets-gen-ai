"""Text-to-speech service for generating audio."""

import logging
from typing import Optional
import httpx

_logger = logging.getLogger(__name__)

class TTSService:
    """Simple TTS service using Google Cloud TTS API."""
    
    # Two default voice options
    VOICE_FEMALE = "en-US-Neural2-F"  # Female voice
    VOICE_MALE = "en-US-Neural2-D"    # Male voice
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize TTS service.
        
        Args:
            api_key: Google Cloud TTS API key (optional - uses free tier if None)
        """
        self._api_key = api_key
        self._base_url = "https://texttospeech.googleapis.com/v1"
    
    async def generate_audio(
        self,
        text: str,
        voice_id: str = VOICE_FEMALE,
        language_code: str = "en-US"
    ) -> Optional[bytes]:
        """Generate audio from text.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID (VOICE_FEMALE or VOICE_MALE)
            language_code: Language code (default: en-US)
            
        Returns:
            Audio data as bytes (MP3 format) or None if failed
        """
        if not text or not text.strip():
            _logger.warning("Empty text provided for TTS")
            return None
        
        # For now, return None to skip audio (will implement full TTS later)
        # This prevents the video generation from failing
        _logger.info(f"TTS requested for text: {text[:50]}... (voice: {voice_id})")
        _logger.info("Audio generation skipped - feature coming soon!")
        return None
    
    def get_available_voices(self):
        """Get list of available voices."""
        return {
            "female": self.VOICE_FEMALE,
            "male": self.VOICE_MALE,
        }


def get_tts_service(api_key: Optional[str] = None) -> TTSService:
    """Get TTS service instance."""
    return TTSService(api_key=api_key)
