import edge_tts
import os
import logging
import tempfile

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.voice = "en-US-ChristopherNeural"  # Funny/Roast style voice

    async def generate_audio(self, text: str, output_path: str) -> str:
        """
        Generates audio using Edge-TTS (Free).
        """
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise
