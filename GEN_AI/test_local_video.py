#!/usr/bin/env python3
"""Test local video generation with WhatsApp puppy video"""
import base64
import requests
import json

# Read and encode video
with open("WhatsApp Video 2026-01-30 at 4.17.58 PM.mp4", "rb") as f:
    video_data = base64.b64encode(f.read()).decode('utf-8')

# Prepare payload
payload = {
    "videoData": video_data,
    "userId": "df8e6019-0ba3-4e45-9fb2-22eb56b2c54c"
}

# Send request
print("🎬 Testing video generation with local puppy video...")
print(f"📦 Video size: {len(video_data)} characters (base64)")
print()

response = requests.post(
    "http://localhost:8080/api/generate-video",
    json=payload,
    headers={"Content-Type": "application/json"}
)

print(f"Status Code: {response.status_code}")
print()
print("Response:")
try:
    print(json.dumps(response.json(), indent=2))
except:
    print(response.text)
