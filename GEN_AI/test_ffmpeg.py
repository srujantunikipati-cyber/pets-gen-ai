import ffmpeg
import sys

def test_ffmpeg_syntax():
    input_video = ffmpeg.input('/home/chetan-patil/myprojects/1/GEN_AI/WhatsApp Video 2026-02-21 at 7.42.52 PM.mp4')
    video_stream = (
        input_video
        .filter('scale', w=1080, h=1920, force_original_aspect_ratio='increase')
        .filter('crop', w=1080, h=1920)
        .filter('zoompan', z='min(zoom+0.001,1.5)', x='iw/2-(iw/zoom/2)', y='ih/2-(ih/zoom/2)', d=1)
    )
    
    # Just compile the command to string to verify syntax
    args = ffmpeg.compile(ffmpeg.output(video_stream, 'output.mp4', vcodec='libx264'))
    print(" ".join(args))

if __name__ == "__main__":
    test_ffmpeg_syntax()
