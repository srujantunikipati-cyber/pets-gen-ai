import ffmpeg
import os
import logging
import json
from typing import List, Dict

logger = logging.getLogger(__name__)

class EditorService:
    def __init__(self):
        self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Adjust as needed
        # Fallback font if specific one not found, or use default

    def _create_srt(self, captions: List[Dict], output_path: str):
        """Generates SRT file from captions."""
        with open(output_path, 'w') as f:
            for i, cap in enumerate(captions):
                # Convert seconds to HH:MM:SS,mmm
                start = self._format_time(cap['start'])
                end = self._format_time(cap['end'])
                text = cap['text']
                f.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")

    def _format_time(self, seconds: float) -> str:
        """Formats time for SRT."""
        import datetime
        td = datetime.timedelta(seconds=seconds)
        # simplistic formatting, might need refinement for milliseconds
        # datetime doesn't have easy support for milliseconds in strftime for this format
        # Manual formatting:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        ms = int((s - int(s)) * 1000)
        return f"{int(h):02}:{int(m):02}:{int(s):02},{ms:03}"

    def process_video(self, video_path: str, audio_path: str, captions: List[Dict], output_path: str):
        """
        1. Loops video to match audio.
        2. Adds Audio.
        3. Adds Subtitles.
        4. Applies Zoom effect.
        """
        try:
            # 1. Get audio duration
            probe = ffmpeg.probe(audio_path)
            audio_duration = float(probe['format']['duration'])
            
            # 2. Create SRT
            srt_path = output_path + ".srt"
            self._create_srt(captions, srt_path)
            
            # 3. Build FFmpeg pipeline
            # Input Video (Loop it)
            input_video = ffmpeg.input(video_path, stream_loop=-1)
            input_audio = ffmpeg.input(audio_path)
            
            # Video filter: Zoompan + Scale + Trim to audio duration
            # Use d=1 to apply zoompan per-frame on animated video
            video_stream = (
                input_video
                .filter('scale', w=1080, h=1920, force_original_aspect_ratio='increase')
                .filter('crop', w=1080, h=1920)
                .filter('zoompan', z='min(zoom+0.001,1.5)', x='iw/2-(iw/zoom/2)', y='ih/2-(ih/zoom/2)', d=1)
                .trim(duration=audio_duration)
                .setpts('PTS-STARTPTS')
            )

            # Add subtitles
            # Note: subtitles filter requires a file path.
            # We use force_style to allow simple styling.
            video_stream = video_stream.filter('subtitles', srt_path, force_style='Alignment=2,OutlineColour=&H40000000,BorderStyle=3,Fontsize=24')

            # Combine with audio
            output = ffmpeg.output(
                video_stream,
                input_audio,
                output_path,
                vcodec='libx264',
                acodec='aac',
                strict='experimental',
                shortest=None # We trimmed video, so it should match
            )
            
            logger.info(f"Running FFmpeg command for {output_path}")
            output.run(overwrite_output=True)
            
            # Cleanup SRT
            if os.path.exists(srt_path):
                os.remove(srt_path)
                
            return {"path": output_path, "duration": audio_duration}

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg failed: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Editor failed: {e}")
            raise

