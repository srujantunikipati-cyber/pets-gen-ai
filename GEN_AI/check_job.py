#!/usr/bin/env python3
"""Check job status and get video output"""
import requests
import json
import time

job_id = "85256214-6ee6-4f9d-aa01-f4f2f3db3f80"

print(f"🔍 Checking job status for: {job_id}\n")

for i in range(30):  # Check for up to 5 minutes
    response = requests.get(f"http://localhost:8080/api/job-status/{job_id}")
    
    if response.status_code == 200:
        data = response.json()
        status = data.get('status')
        
        print(f"[{i+1}] Status: {status}")
        
        if status == 'completed':
            print("\n✅ Video generation completed!")
            print(f"\n📹 Output:")
            print(json.dumps(data, indent=2))
            
            if 'video_url' in data:
                print(f"\n🎬 Video URL: {data['video_url']}")
            if 'video_path' in data:
                print(f"📁 Video Path: {data['video_path']}")
            break
        elif status == 'failed':
            print("\n❌ Video generation failed!")
            print(json.dumps(data, indent=2))
            break
    else:
        print(f"[{i+1}] HTTP {response.status_code}: {response.text[:100]}")
    
    time.sleep(10)
else:
    print("\n⏰ Timeout waiting for completion")
