import ffmpeg
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

class AudioExtractionService:
    def extract_audio(self, video_path: str, output_audio_path: str) -> str:
        """
        Extracts the audio track from a video file and saves it as a valid audio format (e.g. .wav).
        Returns the output path.
        """
        try:
            logger.info(f"Extracting audio from {video_path} to {output_audio_path}")
            
            # Use ffmpeg-python to extract audio
            # -vn: no video
            # -acodec pcm_s16le: 16-bit PCM for accurate Whisper transcription
            # -ar 16000: 16kHz sample rate (optimal for whisper)
            # -ac 1: Mono audio
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, output_audio_path, vn=None, acodec='pcm_s16le', ar='16000', ac=1)
            
            # Execute
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            if not os.path.exists(output_audio_path):
                raise Exception("FFmpeg completed but output audio file not found")
                
            return output_audio_path
            
        except ffmpeg.Error as e:
            err_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Failed to extract audio using FFmpeg: {err_msg}")
            raise Exception(f"Audio extraction failed: {err_msg}")
        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise

    def has_audio(self, video_path: str) -> bool:
        """
        Checks if the video file contains an audio stream.
        """
        try:
            probe = ffmpeg.probe(video_path, select_streams='a')
            return len(probe.get('streams', [])) > 0
        except ffmpeg.Error as e:
            logger.warning(f"FFprobe error while checking audio stream: {e}")
            return False

    def extract_frame(self, video_path: str, output_image_path: str) -> str:
        """
        Extracts the first frame of the video and saves it as an image.
        """
        try:
            logger.info(f"Extracting frame from {video_path}")
            (
                ffmpeg
                .input(video_path)
                .output(output_image_path, vframes=1)
                .overwrite_output()
                .run(quiet=True)
            )
            return output_image_path
        except ffmpeg.Error as e:
            err_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Failed to extract frame: {err_msg}")
            raise Exception(f"Frame extraction failed: {err_msg}")

    def extract_frame_at(self, video_path: str, output_image_path: str, offset_seconds: float = 0.0) -> str:
        """
        Extracts a single frame at the given time offset (seconds).
        Falls back to first frame if seeking fails.
        """
        try:
            (
                ffmpeg
                .input(video_path, ss=offset_seconds)
                .output(output_image_path, vframes=1)
                .overwrite_output()
                .run(quiet=True)
            )
            return output_image_path
        except ffmpeg.Error:
            # Fallback: extract first frame
            return self.extract_frame(video_path, output_image_path)

    def get_video_duration(self, video_path: str) -> float:
        """Return video duration in seconds (0.0 on error)."""
        try:
            probe = ffmpeg.probe(video_path)
            return float(probe['format'].get('duration', 0.0))
        except Exception:
            return 0.0
