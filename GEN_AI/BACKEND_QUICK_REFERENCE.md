# 🎯 BACKEND DEVELOPER QUICK REFERENCE

## Production URL
```
https://pets-gen-ai-production-7245.up.railway.app
```

## API Endpoints (All use /api prefix)

### 1. Health Check
```bash
GET /healthz
Response: {"status": "ok"}
```

### 2. Generate Video - Text + Image Mode
```bash
POST /api/generate-video
Content-Type: multipart/form-data

Parameters:
- text: string (description)
- language: string (e.g., "en")
- image: file (pet image)

Response:
{
  "job_id": "abc123",
  "status": "processing",
  "message": "Video generation started"
}
```

### 3. Generate Video - Video Only Mode
```bash
POST /api/generate-video
Content-Type: multipart/form-data

Parameters:
- language: string (e.g., "en")
- video: file (video with audio)

Response:
{
  "job_id": "xyz789",
  "status": "processing",
  "message": "Video generation started"
}
```

### 4. Check Status
```bash
GET /api/status/{job_id}

Response (Processing):
{
  "job_id": "abc123",
  "status": "processing",
  "progress": "Generating video..."
}

Response (Completed):
{
  "job_id": "abc123",
  "status": "completed",
  "video_url": "https://..."
}

Response (Failed):
{
  "job_id": "abc123",
  "status": "failed",
  "error": "Error message"
}
```

### 5. Download Result
```bash
GET /api/result/{job_id}

Response: Video file (MP4)
```

---

## Python Integration (Copy-Paste Ready)

```python
import requests
import time

BASE_URL = "https://pets-gen-ai-production-7245.up.railway.app"

def generate_from_image(image_path, text, language="en"):
    """Generate roast video from image and text"""
    url = f"{BASE_URL}/api/generate-video"
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'text': text, 'language': language}
        response = requests.post(url, data=data, files=files)
    
    return response.json()['job_id']

def generate_from_video(video_path, language="en"):
    """Generate roast video from video with audio"""
    url = f"{BASE_URL}/api/generate-video"
    
    with open(video_path, 'rb') as f:
        files = {'video': f}
        data = {'language': language}
        response = requests.post(url, data=data, files=files)
    
    return response.json()['job_id']

def wait_for_completion(job_id, max_wait=300):
    """Poll status until completion (max 5 minutes)"""
    url = f"{BASE_URL}/api/status/{job_id}"
    start = time.time()
    
    while time.time() - start < max_wait:
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'completed':
            return data
        elif data['status'] == 'failed':
            raise Exception(f"Generation failed: {data['error']}")
        
        time.sleep(5)
    
    raise TimeoutError("Video generation timed out")

def download_video(job_id, output_path):
    """Download result video"""
    url = f"{BASE_URL}/api/result/{job_id}"
    response = requests.get(url)
    
    with open(output_path, 'wb') as f:
        f.write(response.content)

# Example usage
job_id = generate_from_image('pet.jpg', 'My lazy cat', 'en')
print(f"Job ID: {job_id}")

result = wait_for_completion(job_id)
print(f"Status: {result['status']}")

download_video(job_id, 'roast_video.mp4')
print("Video downloaded!")
```

---

## JavaScript Integration (Copy-Paste Ready)

```javascript
const BASE_URL = 'https://pets-gen-ai-production-7245.up.railway.app';

// Generate from image
async function generateFromImage(imageFile, text, language = 'en') {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('text', text);
    formData.append('language', language);
    
    const response = await fetch(`${BASE_URL}/api/generate-video`, {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    return data.job_id;
}

// Generate from video
async function generateFromVideo(videoFile, language = 'en') {
    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('language', language);
    
    const response = await fetch(`${BASE_URL}/api/generate-video`, {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    return data.job_id;
}

// Poll status
async function waitForCompletion(jobId, maxWait = 300000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWait) {
        const response = await fetch(`${BASE_URL}/api/status/${jobId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
            return data;
        } else if (data.status === 'failed') {
            throw new Error(`Generation failed: ${data.error}`);
        }
        
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
    
    throw new Error('Timeout waiting for video');
}

// Download video
async function downloadVideo(jobId, filename = 'roast_video.mp4') {
    const response = await fetch(`${BASE_URL}/api/result/${jobId}`);
    const blob = await response.blob();
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// Example usage
async function main() {
    try {
        // Get file from input
        const imageFile = document.getElementById('imageInput').files[0];
        
        // Generate video
        const jobId = await generateFromImage(imageFile, 'My lazy cat', 'en');
        console.log('Job ID:', jobId);
        
        // Wait for completion
        const result = await waitForCompletion(jobId);
        console.log('Status:', result.status);
        
        // Download
        await downloadVideo(jobId);
        console.log('Video downloaded!');
    } catch (error) {
        console.error('Error:', error);
    }
}
```

---

## cURL Testing Commands

```bash
# 1. Health check
curl https://pets-gen-ai-production-7245.up.railway.app/healthz

# 2. Generate from image
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -F "text=My lazy cat who sleeps all day" \
  -F "language=en" \
  -F "image=@pet_image.jpg"

# 3. Generate from video
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -F "language=en" \
  -F "video=@pet_video.mp4"

# 4. Check status
curl "https://pets-gen-ai-production-7245.up.railway.app/api/status/YOUR_JOB_ID"

# 5. Download result
curl "https://pets-gen-ai-production-7245.up.railway.app/api/result/YOUR_JOB_ID" \
  -o result_video.mp4
```

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | - |
| 400 | Bad Request | Check parameters (need text+image OR video) |
| 404 | Not Found | Job ID doesn't exist or expired |
| 500 | Server Error | Retry or contact support |
| 502 | Bad Gateway | AI service unavailable, retry |

---

## Validation Rules

**Text + Image Mode:**
- ✅ `text`: Required, non-empty string
- ✅ `language`: Required (e.g., "en", "hi", "ta")
- ✅ `image`: Required, JPG/PNG format

**Video Only Mode:**
- ✅ `language`: Required (e.g., "en", "hi", "ta")
- ✅ `video`: Required, MP4/AVI/MOV format with audio track

---

## Supported Languages

```
en  - English
hi  - Hindi
ta  - Tamil
te  - Telugu
bn  - Bengali
mr  - Marathi
gu  - Gujarati
kn  - Kannada
ml  - Malayalam
pa  - Punjabi
(and 12+ more Indian languages)
```

---

## Performance Notes

- **Cold Start**: First request may take 30-60 seconds
- **Generation Time**: 30-120 seconds typically
- **Polling Interval**: Check status every 5 seconds
- **Timeout**: Set max wait to 5 minutes
- **File Size Limits**:
  - Images: 10MB max (recommended)
  - Videos: 50MB max (recommended)

---

## Quick Troubleshooting

**Issue**: 502 Bad Gateway on first request
→ **Solution**: Wait 30 seconds and retry (cold start)

**Issue**: "No pets detected in image"
→ **Solution**: Ensure image clearly shows a dog or cat

**Issue**: "Failed to extract audio"
→ **Solution**: Ensure video has audio track

**Issue**: Job not found
→ **Solution**: Jobs may expire, check status immediately

---

## Complete Documentation

For detailed integration guide, see:
`COMPLETE_BACKEND_INTEGRATION_GUIDE.md`

For overall project status:
`EVERYTHING_PERFECT_SUMMARY.md`

---

## ✅ Status: PRODUCTION READY

All endpoints tested and working.
Railway deployment stable.
Ready for integration! 🚀
