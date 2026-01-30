#!/usr/bin/env python3
"""Simple test with text+image to verify complete flow"""
import requests
import json
import time

# Test with a simple dog image from a public URL
payload = {
    "text": "Generate a fun roast video for this cute puppy",
    "imageUrl": "https://images.dog.ceo/breeds/retriever-golden/n02099601_3004.jpg",
    "userId": "test-user-123"
}

print("🎬 Testing video generation with text + image...")
print(f"📝 Text: {payload['text']}")
print(f"🖼️  Image: {payload['imageUrl']}")
print()

response = requests.post(
    "http://localhost:8080/api/generate-video",
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=120
)

print(f"✅ Status Code: {response.status_code}")
print()

if response.status_code == 202:
    result = response.json()
    print("📦 Response:")
    print(json.dumps(result, indent=2))
    print()
    print("✅ Video generation job created successfully!")
    print(f"Job ID: {result.get('job_id')}")
    print()
    print("Note: Since Redis is disabled, the job runs in background.")
    print("The video URL will be sent to FAL.ai and processed asynchronously.")
    print("In production with Redis enabled, you can poll the job status.")
else:
    print("❌ Error:")
    print(response.text)
