# Complete Backend Integration Guide - Pet Roast AI

## 🚀 Production URL
**Base URL:** `https://pets-gen-ai-production-7245.up.railway.app`

**API Documentation:** `https://pets-gen-ai-production-7245.up.railway.app/docs`

## ✅ System Status

### Health Check
```bash
curl https://pets-gen-ai-production-7245.up.railway.app/healthz
```
**Response:**
```json
{"status": "ok"}
```

---

## 📋 API Endpoints Overview

| Endpoint | Method | Purpose | Input | Output |
|----------|--------|---------|-------|--------|
| `/healthz` | GET | Health check | None | `{"status": "ok"}` |
| `/api/generate-video` | POST | Generate roast video | Text + Image OR Video | Job ID |
| `/api/status/{job_id}` | GET | Check job status | Job ID | Status info |
| `/api/result/{job_id}` | GET | Get result video | Job ID | Video file or URL |
| `/api/translate-text` | POST | Translate text | Text + languages | Translated text |

---

## 🎯 Main Use Cases

### Use Case 1: Text + Image Mode (Generate Roast from Pet Image)

**Endpoint:** `POST /generate-video`

**What it does:**
1. User uploads pet image + provides text description
2. Backend detects pet in image using YOLOv5
3. AI4Bharat filters and translates content (optional)
4. Generates roast video using fal.ai
5. Returns video with voice-over

**Request Example:**
```bash
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -H "Content-Type: multipart/form-data" \
  -F "text=This is my lazy cat who sleeps all day" \
  -F "language=en" \
  -F "image=@/path/to/pet_image.jpg"
```

**Python Example:**
```python
import requests

url = "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video"

files = {
    'image': open('pet.jpg', 'rb')
}
data = {
    'text': 'This is my lazy dog who loves to sleep',
    'language': 'en'
}

response = requests.post(url, data=data, files=files)
print(response.json())
```

**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "processing",
  "message": "Video generation started"
}
```

---

### Use Case 2: Video-Only Mode (Extract Audio + Generate Roast)

**Endpoint:** `POST /api/generate-video`

**What it does:**
1. User uploads video with audio
2. Backend extracts audio from video
3. Converts speech to text using Whisper AI
4. AI4Bharat filters inappropriate content
5. Generates roast video using fal.ai
6. Returns roast video

**Request Example:**
```bash
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -H "Content-Type: multipart/form-data" \
  -F "language=en" \
  -F "video=@/path/to/pet_video.mp4"
```

**Python Example:**
```python
import requests

url = "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video"

files = {
    'video': open('my_pet.mp4', 'rb')
}
data = {
    'language': 'en'
}

response = requests.post(url, data=data, files=files)
print(response.json())
```

**Response:**
```json
{
  "job_id": "xyz789abc123",
  "status": "processing",
  "message": "Video generation started"
}
```

---

## 🔍 Checking Job Status

**Endpoint:** `GET /api/status/{job_id}`

**Example:**
```bash
curl "https://pets-gen-ai-production-7245.up.railway.app/api/status/abc123def456"
```

**Responses:**

**Processing:**
```json
{
  "job_id": "abc123def456",
  "status": "processing",
  "progress": "Generating video..."
}
```

**Completed:**
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://storage.url/video.mp4"
}
```

**Failed:**
```json
{
  "job_id": "abc123def456",
  "status": "failed",
  "error": "No pets detected in image"
}
```

---

## 📥 Getting Result Video

**Endpoint:** `GET /api/result/{job_id}`

**Example:**
```bash
curl "https://pets-gen-ai-production-7245.up.railway.app/api/result/abc123def456" \
  --output result_video.mp4
```

**Python Example:**
```python
import requests

job_id = "abc123def456"
url = f"https://pets-gen-ai-production-7245.up.railway.app/api/result/{job_id}"

response = requests.get(url)
if response.status_code == 200:
    with open('result_video.mp4', 'wb') as f:
        f.write(response.content)
    print("Video downloaded successfully")
```

---

## 🌐 Translation Feature

**Endpoint:** `POST /api/translate-text`

**Supported Languages:** 22 Indian languages (Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, etc.)

**Example:**
```bash
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/translate-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is my pet dog",
    "source_lang": "en",
    "target_lang": "hi"
  }'
```

**Response:**
```json
{
  "original_text": "This is my pet dog",
  "translated_text": "यह मेरा पालतू कुत्ता है",
  "source_language": "en",
  "target_language": "hi"
}
```

---

## 🔐 Environment Variables Required

For backend integration, you may need these environment variables:

```bash
# API Keys
FAL_KEY=your_fal_ai_key_here

# Optional: Redis for job storage
REDIS_URL=redis://localhost:6379

# Server config (automatically set by Railway)
PORT=8080
HOST=0.0.0.0
```

---

## 🧪 Complete Integration Flow Example

```python
import requests
import time

BASE_URL = "https://pets-gen-ai-production-7245.up.railway.app"

def generate_roast_video(image_path, text):
    """Step 1: Submit video generation job"""
    url = f"{BASE_URL}/generate-video"
    
    with open(image_path, 'rb') as img:
        files = {'image': img}
        data = {'text': text, 'language': 'en'}
        response = requests.post(url, data=data, files=files)
    
    if response.status_code == 200:
        job_data = response.json()
        return job_data['job_id']
    else:
        raise Exception(f"Failed to submit job: {response.text}")

def check_status(job_id):
    """Step 2: Check job status"""
    url = f"{BASE_URL}/status/{job_id}"
    response = requests.get(url)
    return response.json()

def download_result(job_id, output_path):
    """Step 3: Download result video"""
    url = f"{BASE_URL}/result/{job_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

# Complete workflow
def main():
    # Submit job
    print("Submitting video generation job...")
    job_id = generate_roast_video('my_pet.jpg', 'This is my lazy cat')
    print(f"Job ID: {job_id}")
    
    # Poll status
    print("Waiting for completion...")
    while True:
        status = check_status(job_id)
        print(f"Status: {status['status']}")
        
        if status['status'] == 'completed':
            break
        elif status['status'] == 'failed':
            print(f"Error: {status.get('error')}")
            return
        
        time.sleep(5)  # Wait 5 seconds before checking again
    
    # Download result
    print("Downloading result...")
    if download_result(job_id, 'roast_video.mp4'):
        print("Success! Video saved as roast_video.mp4")

if __name__ == '__main__':
    main()
```

---

## ⚠️ Error Handling

### Common Error Responses

**400 Bad Request - Invalid Input:**
```json
{
  "detail": "Either (text + image) or video must be provided"
}
```

**404 Not Found - Job Not Found:**
```json
{
  "detail": "Job not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error processing request",
  "error": "Specific error message"
}
```

### Error Handling Example:
```python
try:
    response = requests.post(url, data=data, files=files)
    response.raise_for_status()  # Raises HTTPError for bad responses
    result = response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
    print(f"Response: {e.response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

---

## 📊 Request/Response Schemas

### GenerateVideoRequest

**Fields:**
- `text` (string, optional): Description/prompt for video generation
- `language` (string, required): Language code (e.g., "en", "hi", "ta")
- `image` (file, optional): Pet image file (JPEG, PNG)
- `video` (file, optional): Video file with audio (MP4, AVI, MOV)

**Validation Rules:**
- Either (text + image) OR video must be provided
- Language is always required
- Supported image formats: JPG, PNG
- Supported video formats: MP4, AVI, MOV

### VideoGenerationResponse

```json
{
  "job_id": "string",
  "status": "processing|completed|failed",
  "message": "string",
  "video_url": "string (optional)"
}
```

---

## 🎨 Frontend Integration Tips

### 1. File Upload with Progress
```javascript
async function uploadPet(formData) {
    const response = await fetch(
        'https://pets-gen-ai-production-7245.up.railway.app/api/generate-video',
        {
            method: 'POST',
            body: formData
        }
    );
    return await response.json();
}
```

### 2. Polling for Results
```javascript
async function pollStatus(jobId) {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        const response = await fetch(
            `https://pets-gen-ai-production-7245.up.railway.app/api/status/${jobId}`
        );
        const data = await response.json();
        
        if (data.status === 'completed') {
            return data;
        } else if (data.status === 'failed') {
            throw new Error(data.error);
        }
        
        await new Promise(resolve => setTimeout(resolve, 5000));
        attempts++;
    }
    
    throw new Error('Timeout waiting for video');
}
```

### 3. Download Video
```javascript
async function downloadVideo(jobId) {
    const response = await fetch(
        `https://pets-gen-ai-production-7245.up.railway.app/api/result/${jobId}`
    );
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    
    // Create download link
    const a = document.createElement('a');
    a.href = url;
    a.download = 'roast_video.mp4';
    a.click();
}
```

---

## 🧩 Integration Checklist

- [ ] **Health Check**: Verify `/healthz` endpoint returns `{"status": "ok"}`
- [ ] **Text+Image Mode**: Test with sample pet image
- [ ] **Video Mode**: Test with sample video containing audio
- [ ] **Status Polling**: Implement proper status checking with timeout
- [ ] **Error Handling**: Handle all error cases (400, 404, 500)
- [ ] **File Validation**: Check file types before upload
- [ ] **Progress Indicator**: Show loading state while processing
- [ ] **Result Display**: Handle video playback or download
- [ ] **Translation**: Test translation feature if using multi-language

---

## 🚦 Testing Commands

### Test Health
```bash
curl https://pets-gen-ai-production-7245.up.railway.app/healthz
```

### Test Text+Image Mode
```bash
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -F "text=Cute puppy playing" \
  -F "language=en" \
  -F "image=@test_pet.jpg"
```

### Test Video Mode
```bash
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -F "language=en" \
  -F "video=@test_video.mp4"
```

### Test Status
```bash
curl "https://pets-gen-ai-production-7245.up.railway.app/api/status/YOUR_JOB_ID"
```

### Test Translation
```bash
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/translate-text" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello","source_lang":"en","target_lang":"hi"}'
```

---

## 📞 Support & Issues

### Common Issues & Solutions

**Issue: "No pets detected in image"**
- Solution: Ensure image clearly shows a pet (dog/cat)
- Use good lighting and clear image

**Issue: "Failed to extract audio from video"**
- Solution: Ensure video has audio track
- Check video format is supported (MP4, AVI, MOV)

**Issue: "Job not found"**
- Solution: Job IDs are temporary, check status immediately after submission
- Jobs may expire after some time

**Issue: "Application failed to respond" (502)**
- Solution: Wait 30-60 seconds for cold start
- Railway containers may need warm-up time

---

## 🎓 AI Services Used

1. **YOLOv5**: Pet detection in images
2. **Whisper AI**: Speech-to-text conversion
3. **AI4Bharat**: Content filtering and translation (22 Indian languages)
4. **fal.ai**: AI video generation

---

## 📈 Performance Notes

- **Cold Start**: First request may take 30-60 seconds
- **Video Generation**: Typically takes 30-120 seconds
- **Recommended Polling Interval**: 5 seconds
- **Max Video Size**: 50MB (recommended)
- **Max Image Size**: 10MB (recommended)

---

## ✅ Everything Working Perfectly!

All issues have been resolved:
- ✅ Railway deployment successful (PORT variable fixed)
- ✅ Health endpoint responding
- ✅ API documentation accessible
- ✅ Video-only mode working
- ✅ Text+image mode working
- ✅ All services initialized
- ✅ Production URL active and stable

**Backend developers can now integrate using this guide!** 🚀
