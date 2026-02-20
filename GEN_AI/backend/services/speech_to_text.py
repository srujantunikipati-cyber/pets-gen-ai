"""Service for converting speech to text using Whisper or similar STT models."""

import logging
import tempfile
import os
from typing import Optional, Dict, Any
import base64

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    try:
        # Fallback to openai-whisper if faster-whisper not available
        import whisper
        WHISPER_AVAILABLE = True
        USE_FASTER_WHISPER = False
    except ImportError:
        WHISPER_AVAILABLE = False
        USE_FASTER_WHISPER = False
        _logger = logging.getLogger(__name__)
        _logger.warning("whisper not available. Install with: pip install faster-whisper")
else:
    USE_FASTER_WHISPER = True

_logger = logging.getLogger(__name__)


class SpeechToTextError(Exception):
    """Raised when speech-to-text conversion fails."""


class SpeechToTextService:
    """Service for converting speech to text."""

    def __init__(self, model_size: str = "base"):
        """Initialize STT service.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        if not WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper or openai-whisper is required for speech-to-text. "
                "Install with: pip install faster-whisper"
            )
        
        self.model_size = model_size
        self._model = None
        self.use_faster_whisper = USE_FASTER_WHISPER
        _logger.info(f"Initializing Whisper model: {model_size} (faster-whisper: {self.use_faster_whisper})")

    def _load_model(self):
        """Lazy load Whisper model."""
        if self._model is None:
            _logger.info(f"Loading Whisper model: {self.model_size}")
            if self.use_faster_whisper:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            else:
                import whisper
                self._model = whisper.load_model(self.model_size)
            _logger.info("Whisper model loaded successfully")

    async def transcribe_audio_bytes(
        self, audio_bytes: bytes, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio bytes to text.
        
        Args:
            audio_bytes: Audio file as bytes
            language: Optional language code (e.g., 'en', 'hi', 'te')
            
        Returns:
            Dict with 'text', 'language', and 'segments'
        """
        try:
            self._load_model()
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name
            
            try:
                # Transcribe audio
                if self.use_faster_whisper:
                    # faster-whisper API
                    segments, info = self._model.transcribe(
                        temp_audio_path,
                        language=language,
                        task="transcribe"
                    )
                    # Convert generator to list
                    segments_list = list(segments)
                    text_parts = [segment.text for segment in segments_list]
                    text = " ".join(text_parts).strip()
                    
                    return {
                        "text": text,
                        "language": info.language if hasattr(info, 'language') else "unknown",
                        "segments": [{"text": seg.text, "start": seg.start, "end": seg.end} for seg in segments_list],
                    }
                else:
                    # openai-whisper API
                    result = self._model.transcribe(
                        temp_audio_path,
                        language=language,
                        task="transcribe"
                    )
                    
                    return {
                        "text": result.get("text", "").strip(),
                        "language": result.get("language", "unknown"),
                        "segments": result.get("segments", []),
                    }
                
            finally:
                # Cleanup temp file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    
        except Exception as e:
            _logger.exception("Failed to transcribe audio")
            raise SpeechToTextError(f"Speech-to-text failed: {str(e)}") from e

    async def transcribe_audio_file(
        self, audio_path: str, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
            
        Returns:
            Dict with 'text', 'language', and 'segments'
        """
        try:
            self._load_model()
            
            # Transcribe audio
            if self.use_faster_whisper:
                # faster-whisper API
                segments, info = self._model.transcribe(
                    audio_path,
                    language=language,
                    task="transcribe"
                )
                # Convert generator to list
                segments_list = list(segments)
                text_parts = [segment.text for segment in segments_list]
                text = " ".join(text_parts).strip()
                
                return {
                    "text": text,
                    "language": info.language if hasattr(info, 'language') else "unknown",
                    "segments": [{"text": seg.text, "start": seg.start, "end": seg.end} for seg in segments_list],
                }
            else:
                # openai-whisper API
                result = self._model.transcribe(
                    audio_path,
                    language=language,
                    task="transcribe"
                )
                
                return {
                    "text": result.get("text", "").strip(),
                    "language": result.get("language", "unknown"),
                    "segments": result.get("segments", []),
                }
            
        except Exception as e:
            _logger.exception("Failed to transcribe audio file")
            raise SpeechToTextError(f"Speech-to-text failed: {str(e)}") from e


# Global STT service instance (lazy loaded)
_stt_service: Optional[SpeechToTextService] = None


def get_speech_to_text_service(model_size: str = "base") -> Optional[SpeechToTextService]:
    """Get speech-to-text service instance."""
    global _stt_service
    if not WHISPER_AVAILABLE:
        return None
    if _stt_service is None:
        _stt_service = SpeechToTextService(model_size=model_size)
    return _stt_service
