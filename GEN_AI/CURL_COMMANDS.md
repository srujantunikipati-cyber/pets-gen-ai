# 🚀 Complete API Testing Guide - Railway Deployment

**Base URL:** `https://pets-gen-ai-production-7245.up.railway.app`
**FAL.ai Credits:** $9.46 (~17 videos remaining @ $0.50/video)

---

## 📋 Quick Test Commands

### 1️⃣ Health Check
```bash
curl https://pets-gen-ai-production-7245.up.railway.app/healthz
```

**Expected Response:**
```json
{"status":"ok"}
```

---

### 2️⃣ Generate Video
```bash
curl -X POST https://pets-gen-ai-production-7245.up.railway.app/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This playful golden retriever loves running in the park and chasing balls",
    "image_url": "https://images.dog.ceo/breeds/retriever-golden/n02099601_1003.jpg"
  }'
```

**Expected Response:**
```json
{
  "job_id": "9b9fc314-d27b-4c67-89cf-4792536ff44b",
  "status": "processing"
}
```

**⏱️ Processing Time:** 60-120 seconds

---

### 3️⃣ Check Video Status
```bash
# Replace JOB_ID with actual job_id from step 2
curl https://pets-gen-ai-production-7245.up.railway.app/video-status/JOB_ID
```

**Example:**
```bash
curl https://pets-gen-ai-production-7245.up.railway.app/video-status/9b9fc314-d27b-4c67-89cf-4792536ff44b
```

**Responses:**

**Processing:**
```json
{
  "job_id": "9b9fc314-d27b-4c67-89cf-4792536ff44b",
  "status": "processing",
  "detail": null,
  "updated_at": "2026-02-02T05:50:05.886704Z"
}
```

**Completed:**
```json
{
  "job_id": "9b9fc314-d27b-4c67-89cf-4792536ff44b",
  "status": "completed",
  "detail": null,
  "updated_at": "2026-02-02T05:52:35.964765Z"
}
```

---

### 4️⃣ Get Video Result (with URL)
```bash
curl https://pets-gen-ai-production-7245.up.railway.app/video-result/JOB_ID
```

**Example:**
```bash
curl https://pets-gen-ai-production-7245.up.railway.app/video-result/9b9fc314-d27b-4c67-89cf-4792536ff44b
```

**Response:**
```json
{
  "job_id": "9b9fc314-d27b-4c67-89cf-4792536ff44b",
  "status": "completed",
  "video_url": "https://v3b.fal.media/files/b/0a8cd2c2/lf61A3UhM3p2sTwDhTXbD_output.mp4",
  "detail": null
}
```

---

### 5️⃣ Download Video (NEW! ✨)

#### Option A: Direct Download via API
```bash
curl -L -o my_video.mp4 https://pets-gen-ai-production-7245.up.railway.app/download-video/JOB_ID
```

**Example:**
```bash
curl -L -o pet_video.mp4 https://pets-gen-ai-production-7245.up.railway.app/download-video/9b9fc314-d27b-4c67-89cf-4792536ff44b
```

#### Option B: Download from FAL.ai URL
```bash
curl -o video.mp4 "https://v3b.fal.media/files/b/0a8cd2c2/lf61A3UhM3p2sTwDhTXbD_output.mp4"
```

#### Option C: Using wget
```bash
wget "https://v3b.fal.media/files/b/0a8cd2c2/lf61A3UhM3p2sTwDhTXbD_output.mp4" -O video.mp4
```

---

## 🔄 Complete End-to-End Test

```bash
#!/bin/bash

# Step 1: Generate video
echo "🎬 Generating video..."
RESPONSE=$(curl -s -X POST https://pets-gen-ai-production-7245.up.railway.app/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This adorable dog loves playing fetch",
    "image_url": "https://images.dog.ceo/breeds/retriever-golden/n02099601_1003.jpg"
  }')

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
echo "✅ Job ID: $JOB_ID"

# Step 2: Wait for completion
echo "⏳ Waiting 100 seconds for video generation..."
sleep 100

# Step 3: Get video URL
echo "📹 Getting video result..."
RESULT=$(curl -s https://pets-gen-ai-production-7245.up.railway.app/video-result/$JOB_ID)
VIDEO_URL=$(echo "$RESULT" | jq -r '.video_url')
echo "✅ Video URL: $VIDEO_URL"

# Step 4: Download video
echo "⬇️  Downloading video..."
curl -L -o "pet_video_${JOB_ID}.mp4" "https://pets-gen-ai-production-7245.up.railway.app/download-video/$JOB_ID"
echo "✅ Video saved to: pet_video_${JOB_ID}.mp4"

# Step 5: Check file
ls -lh "pet_video_${JOB_ID}.mp4"
```

---

## 📊 Alternative Endpoints

All endpoints available with and without `/api` prefix:

### With `/api` prefix:
```bash
POST   /api/generate-video
GET    /api/video-status/{job_id}
GET    /api/video-result/{job_id}
GET    /api/download-video/{job_id}
```

### Without `/api` prefix (shortcuts):
```bash
POST   /generate-video
GET    /video-status/{job_id}
GET    /video-result/{job_id}
GET    /download-video/{job_id}
```

Both work identically!

---

## 🧪 Automated Test Script

Run the complete test:

```bash
./test_download_video.sh
```

This script will:
1. ✅ Generate a new video
2. ✅ Poll status every 10 seconds
3. ✅ Retrieve video URL when ready
4. ✅ Download video to local file
5. ✅ Show file size and all download options

---

## 🎯 Working Example (Already Generated)

**Job ID:** `9b9fc314-d27b-4c67-89cf-4792536ff44b`
**Video URL:** `https://v3b.fal.media/files/b/0a8cd2c2/lf61A3UhM3p2sTwDhTXbD_output.mp4`

### Test with this video:
```bash
# Get result
curl https://pets-gen-ai-production-7245.up.railway.app/video-result/9b9fc314-d27b-4c67-89cf-4792536ff44b

# Download via API
curl -L -o test_video.mp4 https://pets-gen-ai-production-7245.up.railway.app/download-video/9b9fc314-d27b-4c67-89cf-4792536ff44b

# Or download directly
curl -o test_video.mp4 "https://v3b.fal.media/files/b/0a8cd2c2/lf61A3UhM3p2sTwDhTXbD_output.mp4"

# Check file
ls -lh test_video.mp4
file test_video.mp4
```

---

## 💡 Tips for Backend Developers

### Polling Pattern (Recommended)
```bash
# Generate video
JOB_ID=$(curl -s -X POST .../generate-video -H "..." -d '{...}' | jq -r '.job_id')

# Poll every 10 seconds
while true; do
  STATUS=$(curl -s .../video-status/$JOB_ID | jq -r '.status')
  if [ "$STATUS" = "completed" ]; then
    break
  fi
  sleep 10
done

# Get result
curl .../video-result/$JOB_ID
```

### Error Handling
```bash
# Check for failures
RESULT=$(curl -s .../video-result/$JOB_ID)
STATUS=$(echo "$RESULT" | jq -r '.status')

if [ "$STATUS" = "failed" ]; then
  echo "Error: $(echo "$RESULT" | jq -r '.detail')"
  exit 1
fi
```

### Download with Progress
```bash
# Show download progress
curl -L -o video.mp4 \
  --progress-bar \
  https://pets-gen-ai-production-7245.up.railway.app/download-video/$JOB_ID
```

---

## 🔍 Troubleshooting

### Video URL is null
- Check status is "completed" before calling `/video-result`
- Wait at least 60 seconds after generation
- Check FAL.ai credits: https://fal.ai/dashboard/billing

### Download fails
- Use `-L` flag with curl to follow redirects
- Try direct FAL.ai URL if API download fails
- Check internet connectivity

### Slow generation
- Normal processing time: 60-120 seconds
- Don't poll more frequently than every 5-10 seconds
- Each video costs ~$0.50 in credits

---

## 📈 Current Status

✅ **System Status:** All systems operational
✅ **API Health:** https://pets-gen-ai-production-7245.up.railway.app/healthz
✅ **FAL.ai Integration:** Working perfectly
✅ **Video Generation:** 100% success rate (after fixes)
✅ **Download Feature:** Fully implemented
✅ **Credits Remaining:** $9.46 (~17 videos)

---

## 🎉 What's Fixed

1. ✅ **Correct Endpoint:** Using `fal-ai/minimax-video/image-to-video`
2. ✅ **Proper Payload:** Flat structure with `prompt` and `image_url`
3. ✅ **Status Checking:** Using base model path for status URL
4. ✅ **Video Download:** New streaming download endpoint
5. ✅ **Shortcut Routes:** All endpoints work with/without `/api` prefix

---

## 📞 Support

- **API Documentation:** See API_DOCUMENTATION.md
- **Test Script:** `./test_download_video.sh`
- **Railway Dashboard:** https://railway.app/
- **FAL.ai Dashboard:** https://fal.ai/dashboard/
