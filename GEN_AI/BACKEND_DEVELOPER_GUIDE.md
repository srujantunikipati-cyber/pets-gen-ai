# 🚀 **PET ROAST AI - Backend Integration Guide**

## 📡 **Production API URL**
```
https://pets-gen-ai-production-7245.up.railway.app
```

---

## 🔗 **API Endpoints**

### 1. Health Check
```http
GET /healthz
```

**Response:**
```json
{
  "status": "ok"
}
```

---

### 2. Generate Video (Mode 1: Text + Image)

**Endpoint:** `POST /api/generate-video`

**Request Headers:**
```
Content-Type: application/json
```

**Request Payload:**
```json
{
  "text": "This lazy cat thinks he's royalty! Can't even catch a mouse!",
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA..."
}
```

**OR with image URL:**
```json
{
  "text": "This lazy cat thinks he's royalty!",
  "image_url": "https://example.com/pet-image.jpg"
}
```

**Optional Fields:**
```json
{
  "text": "Your roast text",
  "image_data": "data:image/jpeg;base64,...",
  "user_id": "user123",           // Optional: for tracking
  "auth_token": "Bearer xyz..."   // Optional: for authentication
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "abc123def456",
  "status": "queued"
}
```

**Flow:**
```
Image + Text → Pet Detection → Video Generation
```

---

### 3. Generate Video (Mode 2: Video Only)

**Endpoint:** `POST /api/generate-video`

**Request Payload (Video Data):**
```json
{
  "video_data": "data:video/mp4;base64,AAAAIGZ0eXBpc29t..."
}
```

**OR with video URL:**
```json
{
  "video_url": "https://example.com/pet-video.mp4"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "xyz789abc123",
  "status": "queued"
}
```

**Processing Flow:**
```
Video → Extract Audio → Speech-to-Text → 
AI4Bharat Filter → Extract Frame → 
Pet Detection → Video Generation → Done
```

**Features:**
- ✅ Automatic audio extraction
- ✅ Speech-to-text conversion (auto-detects language)
- ✅ Content filtering using AI4Bharat
- ✅ Pet validation using YOLOv5
- ✅ AI video generation using fal.ai

---

### 4. Check Video Status

**Endpoint:** `GET /api/video-status/{job_id}`

**Example:**
```http
GET /api/video-status/abc123def456
```

**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://fal.ai/files/video/xyz.mp4",
  "created_at": "2026-01-29T10:30:00Z",
  "updated_at": "2026-01-29T10:32:15Z"
}
```

**Status Values:**
- `queued` - Job submitted, waiting to process
- `processing` - Currently generating video
- `completed` - Video ready, check video_url
- `failed` - Generation failed, check error_message

---

### 5. Get Video Result

**Endpoint:** `GET /api/video-result/{job_id}`

**Example:**
```http
GET /api/video-result/abc123def456
```

**Response (Success):**
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://fal.ai/files/video/xyz.mp4",
  "text": "Processed roast text",
  "language": "en",
  "created_at": "2026-01-29T10:30:00Z"
}
```

**Response (Failed):**
```json
{
  "job_id": "abc123def456",
  "status": "failed",
  "error_message": "No pets detected in image"
}
```

---

### 6. Translate Text

**Endpoint:** `POST /api/translate-text`

**Request:**
```json
{
  "text": "Hello, how are you?",
  "source_lang": "en",
  "target_lang": "hi",
  "task": "translation"
}
```

**Response:**
```json
{
  "translated_text": "नमस्ते, आप कैसे हैं?",
  "source_language": "en",
  "target_language": "hi",
  "task": "translation"
}
```

---

## 🔧 **Complete Examples**

### Example 1: Text + Image (cURL)
```bash
curl -X POST https://pets-gen-ai-production-7245.up.railway.app/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This lazy furball sleeps all day!",
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  }'
```

### Example 2: Video Only (cURL)
```bash
curl -X POST https://pets-gen-ai-production-7245.up.railway.app/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/pet-video.mp4"
  }'
```

### Example 3: JavaScript/TypeScript
```typescript
const response = await fetch(
  'https://pets-gen-ai-production-7245.up.railway.app/api/generate-video',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: 'Your roast text here',
      image_data: 'data:image/jpeg;base64,...'
    })
  }
);

const result = await response.json();
console.log('Job ID:', result.job_id);

// Poll for status
const checkStatus = async (jobId: string) => {
  const statusResponse = await fetch(
    `https://pets-gen-ai-production-7245.up.railway.app/api/video-status/${jobId}`
  );
  return await statusResponse.json();
};
```

### Example 4: Python
```python
import requests
import base64

# Read and encode image
with open('pet.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# Generate video
response = requests.post(
    'https://pets-gen-ai-production-7245.up.railway.app/api/generate-video',
    json={
        'text': 'Your roast text',
        'image_data': f'data:image/jpeg;base64,{image_data}'
    }
)

job_id = response.json()['job_id']
print(f'Job ID: {job_id}')

# Check status
status = requests.get(
    f'https://pets-gen-ai-production-7245.up.railway.app/api/video-status/{job_id}'
).json()
print(f'Status: {status["status"]}')
```

---

## ❌ **Error Responses**

### No Pets Detected
```json
{
  "status_code": 400,
  "detail": {
    "error": "no_pets_detected",
    "message": "No pets found in the uploaded image/video.",
    "suggestion": "Try uploading a clear photo or video of your pet."
  }
}
```

### Missing Required Fields
```json
{
  "status_code": 400,
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Either provide (text + image_url/image_data) OR (video_url/video_data/video)."
    }
  ]
}
```

### Service Unavailable
```json
{
  "status_code": 503,
  "detail": "Video generation service is not configured."
}
```

---

## 📊 **Rate Limits & Best Practices**

1. **Polling Interval**: Check status every 2-5 seconds
2. **Timeout**: Video generation takes 30-120 seconds
3. **Image Size**: Recommended max 5MB
4. **Video Size**: Recommended max 50MB
5. **Text Length**: Max 5000 characters

---

## 🔐 **Authentication (Optional)**

If you have auth_token from pets-backend:

```json
{
  "text": "Your roast",
  "image_data": "data:image/jpeg;base64,...",
  "auth_token": "Bearer your-jwt-token",
  "user_id": "user123"
}
```

---

## 🧪 **Testing**

### Test Health
```bash
curl https://pets-gen-ai-production-7245.up.railway.app/healthz
```

### Test API Docs
```
https://pets-gen-ai-production-7245.up.railway.app/docs
```

---

## 📞 **Support**

- **API Docs**: https://pets-gen-ai-production-7245.up.railway.app/docs
- **Health Check**: https://pets-gen-ai-production-7245.up.railway.app/healthz
- **Status**: All services operational ✅

---

## 🎯 **Quick Integration Checklist**

- [ ] Test health endpoint
- [ ] Test text + image generation
- [ ] Test video-only generation
- [ ] Implement status polling
- [ ] Handle error responses
- [ ] Add loading states
- [ ] Test with real pet images/videos
- [ ] Deploy to production

---

**Generated**: January 29, 2026
**Version**: 1.0
**Base URL**: https://pets-gen-ai-production-7245.up.railway.app
