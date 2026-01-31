#!/usr/bin/env python3
"""
Complete video generation flow: Input video → Process → Output video
"""

import base64
import requests
import json
import time
import sys

# Configuration
INPUT_VIDEO = "/home/chetan-patil/myprojects/1/GEN_AI/WhatsApp Video 2026-01-30 at 4.17.58 PM.mp4"
RAILWAY_URL = "https://pets-gen-ai-production-7245.up.railway.app"
LOCAL_URL = "http://localhost:8000"

# Use Railway by default (change to LOCAL_URL for local testing)
API_URL = RAILWAY_URL

def encode_video(video_path):
    """Encode video to base64"""
    print(f"📹 Reading input video: {video_path}")
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    
    b64 = base64.b64encode(video_bytes).decode('utf-8')
    video_data = f"data:video/mp4;base64,{b64}"
    print(f"✅ Video encoded: {len(video_data)} characters")
    return video_data

def submit_video_generation(video_data, user_id="demo-user"):
    """Submit video for generation"""
    print(f"\n📤 Submitting to {API_URL}/api/generate-video")
    
    payload = {
        "videoData": video_data,
        "userId": user_id
    }
    
    response = requests.post(
        f"{API_URL}/api/generate-video",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=90
    )
    
    if response.status_code != 202:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    job_id = result.get("job_id")
    print(f"✅ Job submitted successfully!")
    print(f"📝 Job ID: {job_id}")
    return job_id

def check_job_status(job_id):
    """Check the status of video generation job"""
    response = requests.get(
        f"{API_URL}/api/video-status/{job_id}",
        timeout=30
    )
    
    if response.status_code != 200:
        return None
    
    return response.json()

def wait_for_completion(job_id, max_wait_minutes=15):
    """Poll job status until completion or timeout"""
    print(f"\n⏳ Waiting for video generation to complete...")
    print(f"   (Max wait time: {max_wait_minutes} minutes)")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    poll_interval = 10  # Check every 10 seconds
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait_seconds:
            print(f"\n⏰ Timeout after {max_wait_minutes} minutes")
            return None
        
        status_data = check_job_status(job_id)
        
        if not status_data:
            print("❌ Failed to get job status")
            return None
        
        status = status_data.get("status")
        print(f"   Status: {status} (elapsed: {int(elapsed)}s)")
        
        if status == "completed":
            print("✅ Video generation completed!")
            return status_data
        
        elif status == "failed":
            error_msg = status_data.get("error_message", "Unknown error")
            print(f"❌ Video generation failed: {error_msg}")
            return None
        
        elif status in ["processing", "pending"]:
            time.sleep(poll_interval)
        
        else:
            print(f"⚠️  Unknown status: {status}")
            time.sleep(poll_interval)

def download_video(video_url, output_path="/home/chetan-patil/myprojects/1/GEN_AI/output_generated_video.mp4"):
    """Download the generated video"""
    print(f"\n⬇️  Downloading generated video...")
    print(f"   From: {video_url}")
    print(f"   To: {output_path}")
    
    response = requests.get(video_url, stream=True, timeout=60)
    
    if response.status_code != 200:
        print(f"❌ Failed to download video: {response.status_code}")
        return None
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"✅ Video downloaded successfully!")
    print(f"📁 Output: {output_path}")
    return output_path

def main():
    print("=" * 70)
    print("🎬 PET ROAST AI - COMPLETE VIDEO GENERATION")
    print("=" * 70)
    print(f"\n📹 Input Video: {INPUT_VIDEO}")
    print(f"🌐 API Endpoint: {API_URL}")
    
    # Step 1: Encode video
    video_data = encode_video(INPUT_VIDEO)
    
    # Step 2: Submit for generation
    job_id = submit_video_generation(video_data)
    if not job_id:
        print("\n❌ Failed to submit video generation")
        sys.exit(1)
    
    # Step 3: Wait for completion
    result = wait_for_completion(job_id, max_wait_minutes=15)
    if not result:
        print("\n❌ Video generation did not complete successfully")
        print(f"💡 You can check status manually at: {API_URL}/api/video-status/{job_id}")
        sys.exit(1)
    
    # Step 4: Get video URL
    video_url = result.get("video_url") or result.get("videoUrl")
    if not video_url:
        print("\n⚠️  Video generation completed but no video URL found")
        print(f"📄 Full result: {json.dumps(result, indent=2)}")
        sys.exit(1)
    
    # Step 5: Download video
    output_path = download_video(video_url)
    if not output_path:
        print("\n❌ Failed to download video")
        sys.exit(1)
    
    # Success!
    print("\n" + "=" * 70)
    print("🎉 VIDEO GENERATION COMPLETE!")
    print("=" * 70)
    print(f"📥 Input:  {INPUT_VIDEO}")
    print(f"📤 Output: {output_path}")
    print(f"🔗 Video URL: {video_url}")
    print(f"📝 Job ID: {job_id}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
