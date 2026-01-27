# 🐾 GEN_AI API Documentation

> Complete API reference for Pet Roast AI Service (FastAPI)

**Base URL**: `http://localhost:8000` (local) or `https://your-service.up.railway.app` (production)

**API Version**: v1

---

## 📋 Table of Contents

- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Generate Video](#generate-video)
  - [Check Video Status](#check-video-status)
  - [Get Video Result](#get-video-result)
  - [Translate Text](#translate-text)
  - [Webhook (Internal)](#webhook-internal)
- [Request/Response Examples](#requestresponse-examples)
- [Error Handling](#error-handling)
- [Integration Guide](#integration-guide)

---

## 🔐 Authentication

Currently, the API does not require authentication for basic endpoints. However, for pets-backend integration:

- **Optional**: Include `auth_token` (JWT) in request body for user context
- **Optional**: Include `user_id` in request body for job tracking

---

## 📡 Endpoints

### Health Check

Check if the service is running.

**Endpoint**: `GET /healthz`

**Response**:
```json
{
  "status": "ok"
}
```

**Example**:
```bash
curl http://localhost:8000/healthz
```

---

### Generate Video

Submit a new video generation job.

**Endpoint**: `POST /api/generate-video`

**Content-Type**: `application/json`

**Request Body**:

```json
{
  // Mode 1: Text + Image
  "text": "Roast my lazy dog!",
  "image_url": "https://example.com/dog.jpg",
  // OR
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  
  // Mode 2: Video Input (audio extracted automatically)
  "video_url": "https://example.com/video.mp4",
  // OR
  "video_data": "data:video/mp4;base64,AAAAIGZ0eXBpc29t...",
  
  // Optional: pets-backend integration
  "user_id": "user123",
  "auth_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Conditional* | Roast text (required for Mode 1) |
| `image_url` | string | Conditional* | URL of pet image (required for Mode 1) |
| `image_data` | string | Conditional* | Base64 encoded image (required for Mode 1) |
| `video_url` | string | Conditional* | URL of video file (required for Mode 2) |
| `video_data` | string | Conditional* | Base64 encoded video (required for Mode 2) |
| `user_id` | string | Optional | User ID for job tracking |
| `auth_token` | string | Optional | JWT token for authentication |

*Either provide (text + image) OR (video). For video input, audio is extracted and converted to text automatically.

**Response** (202 Accepted):

```json
{
  "job_id": "abc123def456",
  "status": "queued"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Unique job identifier |
| `status` | string | Job status: `queued`, `processing`, `completed`, `failed` |

**Example**:

```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Roast my lazy dog!",
    "image_url": "https://example.com/dog.jpg",
    "user_id": "user123"
  }'
```

**Error Responses**:

- `400 Bad Request`: Missing required fields or no pets detected
- `502 Bad Gateway`: External service error (fal.ai, AI4Bharat)
- `503 Service Unavailable`: Audio/STT services not available

---

### Check Video Status

Get the current status of a video generation job.

**Endpoint**: `GET /api/video-status/{job_id}`

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | Job identifier from generate-video response |

**Response** (200 OK):

```json
{
  "job_id": "abc123def456",
  "status": "processing",
  "detail": "Video is being generated...",
  "updated_at": "2026-01-23T10:30:00Z"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Job identifier |
| `status` | string | Current status: `queued`, `processing`, `completed`, `failed` |
| `detail` | string | Optional status message |
| `updated_at` | string | Last update timestamp (ISO 8601) |

**Example**:

```bash
curl http://localhost:8000/api/video-status/abc123def456
```

**Status Values**:

- `queued`: Job is waiting to be processed
- `processing`: Video is being generated
- `completed`: Video is ready
- `failed`: Job failed (check `detail` for error)

---

### Get Video Result

Get the final video URL once generation is complete.

**Endpoint**: `GET /api/video-result/{job_id}`

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | Job identifier |

**Response** (200 OK):

```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://fal.ai/video/xyz.mp4",
  "detail": null
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Job identifier |
| `status` | string | Job status (should be `completed`) |
| `video_url` | string | URL to download/watch the video |
| `detail` | string | Optional message or error |

**Example**:

```bash
curl http://localhost:8000/api/video-result/abc123def456
```

**Error Responses**:

- `404 Not Found`: Job ID not found
- `409 Conflict`: Video not ready yet (status is not `completed`)
- `502 Bad Gateway`: Error fetching from fal.ai

**Note**: Video is automatically downloaded and saved to `storage/videos/` directory when available.

---

### Translate Text

Translate or analyze text using AI4Bharat translation service.

**Endpoint**: `POST /api/translate-text`

**Content-Type**: `application/json`

**Request Body**:

```json
{
  "text": "Hello, how are you?",
  "source_lang": "eng_Latn",
  "target_lang": "hin_Deva",
  "task": "translation"
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to translate |
| `source_lang` | string | No | Source language code (default: `auto`) |
| `target_lang` | string | Yes | Target language code |
| `task` | string | No | Task type: `translation` (default) |

**Supported Languages**:

- `eng_Latn` - English
- `hin_Deva` - Hindi
- `tel_Telu` - Telugu
- `tam_Taml` - Tamil
- `kan_Knda` - Kannada
- `mal_Mlym` - Malayalam
- `guj_Gujr` - Gujarati
- `mar_Deva` - Marathi
- `ben_Beng` - Bengali
- `pan_Guru` - Punjabi
- And more...

**Response** (200 OK):

```json
{
  "translated_text": "नमस्ते, आप कैसे हैं?",
  "source_language": "eng_Latn",
  "target_language": "hin_Deva",
  "task": "translation",
  "provider_metadata": {
    "detected_language": "eng_Latn"
  }
}
```

**Example**:

```bash
curl -X POST http://localhost:8000/api/translate-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "source_lang": "eng_Latn",
    "target_lang": "hin_Deva"
  }'
```

---

### Webhook (Internal)

Webhook endpoint for fal.ai to notify when video generation completes.

**Endpoint**: `POST /api/webhook/video-complete`

**Content-Type**: `application/json`

**Request Body**:

```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://fal.ai/video/xyz.mp4",
  "error": null
}
```

**Note**: This endpoint is primarily for internal use (fal.ai webhooks). For checking status, use `/api/video-status/{job_id}`.

---

## 📝 Request/Response Examples

### Example 1: Generate Video with Image URL

**Request**:
```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your dog is so lazy, it makes sloths look productive!",
    "image_url": "https://example.com/dog.jpg",
    "user_id": "user123"
  }'
```

**Response**:
```json
{
  "job_id": "1605b5dd-405b-4811-917c-9297328ef611",
  "status": "queued"
}
```

### Example 2: Generate Video with Base64 Image

**Request**:
```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Roast my cat!",
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  }'
```

**Response**:
```json
{
  "job_id": "abc123def456",
  "status": "queued"
}
```

### Example 3: Generate Video from Video Input

**Request**:
```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/pet-video.mp4",
    "user_id": "user123"
  }'
```

**Response**:
```json
{
  "job_id": "xyz789ghi012",
  "status": "queued"
}
```

**Note**: For video input, the service will:
1. Extract audio from video
2. Convert speech to text (STT)
3. Filter abusive content (LLM-based)
4. Preserve original language
5. Generate video with the processed text

### Example 4: Check Status

**Request**:
```bash
curl http://localhost:8000/api/video-status/1605b5dd-405b-4811-917c-9297328ef611
```

**Response** (Processing):
```json
{
  "job_id": "1605b5dd-405b-4811-917c-9297328ef611",
  "status": "processing",
  "detail": "Video is being generated...",
  "updated_at": "2026-01-23T10:35:00Z"
}
```

**Response** (Completed):
```json
{
  "job_id": "1605b5dd-405b-4811-917c-9297328ef611",
  "status": "completed",
  "detail": null,
  "updated_at": "2026-01-23T10:40:00Z"
}
```

### Example 5: Get Video Result

**Request**:
```bash
curl http://localhost:8000/api/video-result/1605b5dd-405b-4811-917c-9297328ef611
```

**Response**:
```json
{
  "job_id": "1605b5dd-405b-4811-917c-9297328ef611",
  "status": "completed",
  "video_url": "https://fal.ai/video/xyz.mp4",
  "detail": null
}
```

---

## ⚠️ Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `202` | Accepted | Job created, processing started |
| `400` | Bad Request | Invalid request (missing fields, no pets detected) |
| `404` | Not Found | Job ID not found |
| `409` | Conflict | Video not ready yet |
| `502` | Bad Gateway | External service error (fal.ai, AI4Bharat) |
| `503` | Service Unavailable | Required service not available (STT, audio extraction) |
| `500` | Internal Server Error | Unexpected server error |

### Common Errors

#### No Pets Detected

```json
{
  "detail": {
    "error": "no_pets_detected",
    "message": "No pets found in the uploaded image. Please upload an image or video containing pets (dogs, cats, birds, etc.) to generate a roast video.",
    "suggestion": "Try uploading a clear photo or video of your pet."
  }
}
```

#### Missing Required Fields

```json
{
  "detail": "Either provide (text + image_url/image_data) OR (video_url/video_data). For video input, audio will be extracted and converted to text automatically."
}
```

#### Video Not Ready

```json
{
  "detail": "Video asset not ready yet. Please try again in a few moments."
}
```

#### External Service Error

```json
{
  "detail": "fal.ai create job failed: Route not found"
}
```

---

## 🔗 Integration Guide

### For pets-backend Integration

#### 1. Generate Video

```typescript
// TypeScript example for pets-backend
const response = await axios.post(
  `${process.env.PET_ROAST_API_URL}/generate-video`,
  {
    text: prompt,
    image_url: imageUrl,
    user_id: userId,  // Optional: for tracking
    auth_token: token // Optional: for authentication
  },
  {
    headers: { 'Content-Type': 'application/json' }
  }
);

const { job_id, status } = response.data;
```

#### 2. Poll Status

```typescript
const checkStatus = async (jobId: string) => {
  const response = await axios.get(
    `${process.env.PET_ROAST_API_URL}/video-status/${jobId}`
  );
  
  return response.data; // { job_id, status, detail, updated_at }
};
```

#### 3. Get Result

```typescript
const getResult = async (jobId: string) => {
  const response = await axios.get(
    `${process.env.PET_ROAST_API_URL}/video-result/${jobId}`
  );
  
  return response.data; // { job_id, status, video_url, detail }
};
```

#### 4. Webhook Setup

Configure webhook URL in GEN_AI environment:

```bash
BACKEND_WEBHOOK_URL=https://your-pets-backend.railway.app/webhooks/pet-roast-complete
```

GEN_AI will automatically send webhook when video completes:

```json
POST {BACKEND_WEBHOOK_URL}
{
  "job_id": "abc123",
  "status": "completed",
  "video_url": "https://fal.ai/video/xyz.mp4",
  "user_id": "user123",
  "error": null
}
```

### Polling Strategy

**Recommended**: Poll every 5-10 seconds while status is `queued` or `processing`:

```typescript
const pollUntilComplete = async (jobId: string, maxAttempts = 60) => {
  for (let i = 0; i < maxAttempts; i++) {
    const status = await checkStatus(jobId);
    
    if (status.status === 'completed') {
      const result = await getResult(jobId);
      return result.video_url;
    }
    
    if (status.status === 'failed') {
      throw new Error(`Job failed: ${status.detail}`);
    }
    
    await sleep(5000); // Wait 5 seconds
  }
  
  throw new Error('Job timeout');
};
```

---

## 🌐 API Base URLs

### Local Development
```
http://localhost:8000
```

### Production (Railway)
```
https://your-service.up.railway.app
```

### Swagger UI (Interactive Docs)
```
http://localhost:8000/docs
```

### ReDoc (Alternative Docs)
```
http://localhost:8000/redoc
```

---

## 📊 Rate Limits

Currently, there are no rate limits. However, for production:

- Consider implementing rate limiting per user/IP
- Monitor API usage
- Set appropriate timeouts

---

## 🔒 Security Notes

1. **API Keys**: Keep `FAL_API_KEY` secure (never expose in frontend)
2. **Webhooks**: Validate webhook signatures if implemented
3. **CORS**: Configure `CORS_ORIGINS` for production
4. **Tokens**: JWT tokens are optional but recommended for user tracking

---

## 📞 Support

For issues or questions:
- Check logs: Railway dashboard → Logs tab
- API Docs: Visit `/docs` endpoint
- GitHub: https://github.com/srujantunikipati-cyber/pets-gen-ai

---

## 🎯 Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/healthz` | GET | Health check |
| `/api/generate-video` | POST | Create video job |
| `/api/video-status/{job_id}` | GET | Check job status |
| `/api/video-result/{job_id}` | GET | Get video URL |
| `/api/translate-text` | POST | Translate text |
| `/api/webhook/video-complete` | POST | Webhook (internal) |
| `/docs` | GET | Swagger UI |

---

**Last Updated**: 2026-01-23  
**API Version**: 1.0  
**Service**: Pet Roast AI (GEN_AI)
