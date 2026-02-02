#!/usr/bin/env python3
"""Generate video from local WhatsApp video file with audio."""

import base64
import json
import sys
import time
import requests

BASE_URL = "https://pets-gen-ai-production-7245.up.railway.app"

def generate_video_with_audio(image_path: str, text: str, voice: str = "female", music_style: str = "playful"):
    """Generate video from local image with audio and music."""
    
    print(f"\n{'='*60}")
    print(f"🎬 Generating Video from Local File")
    print(f"{'='*60}\n")
    
    # Read and encode image
    print(f"📖 Reading image: {image_path}")
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"📦 Image size: {len(image_data)} chars (base64)")
    
    # Prepare payload with audio options
    voice_id = "en-US-Neural2-F" if voice == "female" else "en-US-Neural2-D"
    
    payload = {
        "text": text,
        "imageData": f"data:image/jpeg;base64,{image_data}",
        "userId": "local-test",
        "audioEnabled": True,
        "audioVoice": voice_id,
        "musicEnabled": True,
        "musicStyle": music_style,
        "musicVolume": 0.3
    }
    
    print(f"\n🎬 Generating video...")
    print(f"📝 Text: {text}")
    print(f"🎤 Voice: {voice} ({voice_id})")
    print(f"🎵 Music: {music_style}")
    print(f"💰 Cost: $0.02 (AnimateDiff model)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate-video",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Accept both 200 and 202 status codes
        if response.status_code not in [200, 202]:
            print(f"\n❌ Error {response.status_code}:")
            print(response.text)
            return None
        
        result = response.json()
        job_id = result.get('job_id')
        
        if not job_id:
            print(f"❌ No job_id in response: {result}")
            return None
        
        print(f"\n✅ Job created: {job_id}")
        print(f"Status: {result.get('status')}")
        
        # Poll for completion
        print(f"\n⏳ Waiting for video generation...")
        print(f"   Checking every 10 seconds (typically takes 60-120 seconds)")
        
        max_checks = 18  # 3 minutes max
        check_count = 0
        
        while check_count < max_checks:
            check_count += 1
            time.sleep(10)
            
            print(f"\n🔍 Check #{check_count} ({check_count * 10}s)...", end=" ")
            
            try:
                status_response = requests.get(
                    f"{BASE_URL}/api/video-status/{job_id}",
                    timeout=10
                )
                
                if status_response.status_code != 200:
                    print(f"⚠️ Status check failed: {status_response.status_code}")
                    continue
                
                status_data = status_response.json()
                current_status = status_data.get('status')
                
                if current_status == 'completed':
                    print(f"✅ COMPLETED!")
                    
                    # Get video result
                    result_response = requests.get(
                        f"{BASE_URL}/api/video-result/{job_id}",
                        timeout=10
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        video_url = result_data.get('video_url')
                        
                        if video_url:
                            print(f"\n{'='*60}")
                            print(f"🎉 SUCCESS! Video is ready!")
                            print(f"{'='*60}")
                            print(f"\n📹 Video URL:")
                            print(f"   {video_url}")
                            print(f"\n⬇️  Download:")
                            print(f"   curl -o my_video.mp4 \"{video_url}\"")
                            print(f"\n   Or use:")
                            print(f"   wget \"{video_url}\" -O my_video.mp4")
                            print(f"\n💰 Cost: $0.02")
                            print(f"{'='*60}\n")
                            return video_url
                        else:
                            print(f"\n❌ No video URL in result")
                            return None
                    else:
                        print(f"\n❌ Failed to get result: {result_response.status_code}")
                        return None
                
                elif current_status == 'failed':
                    print(f"❌ FAILED!")
                    print(f"\nDetails: {status_data}")
                    return None
                
                else:
                    print(f"⏳ {current_status}")
            
            except Exception as e:
                print(f"⚠️ Error: {e}")
                continue
        
        print(f"\n⏱️ Timeout after {max_checks * 10} seconds")
        print(f"   Check manually: {BASE_URL}/api/video-result/{job_id}")
        return None
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Configuration
    image_file = "/tmp/pet_frame.jpg"
    text_prompt = "This adorable pet is full of energy and loves to play all day long!"
    voice_option = "female"  # or "male"
    music_choice = "playful"  # playful, happy, calm, energetic, funny, cute
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        text_prompt = sys.argv[1]
    if len(sys.argv) > 2:
        voice_option = sys.argv[2]
    if len(sys.argv) > 3:
        music_choice = sys.argv[3]
    
    print("\n💡 Usage:")
    print(f"   python3 {sys.argv[0]} \"Your text here\" [female|male] [playful|happy|calm|energetic|funny|cute]")
    print(f"\n📝 Current settings:")
    print(f"   Text: {text_prompt}")
    print(f"   Voice: {voice_option}")
    print(f"   Music: {music_choice}")
    print(f"   Image: {image_file}")
    
    try:
        video_url = generate_video_with_audio(image_file, text_prompt, voice_option, music_choice)
        if video_url:
            print(f"✅ Video generation completed successfully!")
            sys.exit(0)
        else:
            print(f"❌ Video generation failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Interrupted by user")
        sys.exit(1)
