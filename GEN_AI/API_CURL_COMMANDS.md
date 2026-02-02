# API Testing Guide - CURL Commands

## Railway Deployment
**URL:** https://pets-gen-ai-production-7245.up.railway.app

## Available Endpoints

### 1. Generate Video (POST)
**Endpoint:** `/api/generate-video`

#### Option A: With Base64 Image
```bash
# Encode image to base64
IMAGE_B64=$(base64 -w 0 /path/to/your/image.jpeg)

# Send request
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"A beautiful animated pet scene\",
    \"image_data\": \"$IMAGE_B64\"
  }"
```

#### Option B: With Image URL
```bash
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A playful pet enjoying fun moments",
    "image_url": "https://example.com/pet.jpg"
  }'
```

#### Option C: Text Only (No Image)
```bash
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A cute cat playing with a ball"
  }'
```

### 2. Check Video Status (GET)
**Endpoint:** `/api/video-result/{job_id}`

```bash
# Replace YOUR_JOB_ID with the job_id from the generate-video response
curl "https://pets-gen-ai-production-7245.up.railway.app/api/video-result/YOUR_JOB_ID"
```

## Response Format

### Generate Video Response
```json
{
  "job_id": "abc123-def456-...",
  "status": "processing",
  "message": "Video generation started"
}
```

### Video Status Response (Processing)
```json
{
  "status": "processing",
  "progress": 50
}
```

### Video Status Response (Completed)
```json
{
  "status": "completed",
  "video_url": "https://v3b.fal.media/files/.../video.mp4",
  "thumbnail_url": "https://v3b.fal.media/files/.../thumbnail.jpg"
}
```

### Video Status Response (Failed)
```json
{
  "status": "failed",
  "error": "Error message here"
}
```

## Testing Script

Run the automated test script:
```bash
./TEST_API_CURL.sh
```

## Cost Information
- **Model Used:** fast-animatediff
- **Cost per video:** $0.02
- **Duration:** Videos are 3 seconds (looped to 10 seconds locally with background music)

## Local Generated Files
- **Input Image:** `storage/videos/input_image.jpeg`
- **Generated Video (10 sec with music):** `storage/videos/generated_video_with_music.mp4`

## Notes
- Video generation typically takes 10-90 seconds
- Videos are generated at 8 fps, 128x256 resolution
- Background music is added locally using FFmpeg (not on Railway)
