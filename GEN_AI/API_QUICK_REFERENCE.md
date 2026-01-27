# 🚀 GEN_AI API - Quick Reference Card

**Base URL**: `http://localhost:8000` (local) | `https://your-service.up.railway.app` (production)

---

## 📋 Essential Endpoints

### 1. Generate Video
```bash
POST /api/generate-video
Content-Type: application/json

{
  "text": "Roast my lazy dog!",
  "image_url": "https://example.com/dog.jpg",
  "user_id": "optional-user-id"
}
```

**Response**:
```json
{
  "job_id": "abc123def456",
  "status": "queued"
}
```

---

### 2. Check Status
```bash
GET /api/video-status/{job_id}
```

**Response**:
```json
{
  "job_id": "abc123def456",
  "status": "processing",
  "detail": "Video is being generated...",
  "updated_at": "2026-01-23T10:30:00Z"
}
```

---

### 3. Get Video Result
```bash
GET /api/video-result/{job_id}
```

**Response**:
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://fal.ai/video/xyz.mp4"
}
```

---

## 🔄 Integration Flow

```
1. POST /api/generate-video → Get job_id
2. Poll GET /api/video-status/{job_id} every 5-10 seconds
3. When status = "completed" → GET /api/video-result/{job_id}
4. Use video_url to display/download video
```

---

## 📝 Request Modes

### Mode 1: Text + Image
```json
{
  "text": "Roast text here",
  "image_url": "https://...",
  // OR
  "image_data": "data:image/jpeg;base64,..."
}
```

### Mode 2: Video Input (Auto STT)
```json
{
  "video_url": "https://...",
  // OR
  "video_data": "data:video/mp4;base64,..."
}
```
*Audio extracted → Speech-to-Text → Content filtered → Video generated*

---

## ⚠️ Status Values

- `queued` - Waiting to process
- `processing` - Video being generated
- `completed` - Video ready (get from `/video-result`)
- `failed` - Job failed (check `detail`)

---

## 🔗 Full Documentation

See `API_DOCUMENTATION.md` for complete details.

---

**Quick Share**: Send this file to your backend developer! 📤
