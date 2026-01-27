# 🐾 Pet Roast AI Service

> AI-powered pet roasting service with YOLOv5 pet detection, multi-language translation, and video generation capabilities.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)](https://www.python.org/)
[![Railway](https://img.shields.io/badge/Deploy%20on-Railway-blueviolet?style=flat&logo=railway)](https://railway.app)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Local Development Setup](#-local-development-setup)
- [Railway Deployment](#-railway-deployment)
- [API Endpoints](#-api-endpoints)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Contributing](#-contributing)

---

## ✨ Features

- 🤖 **AI-Powered Pet Detection** - Uses YOLOv5 to detect and identify pets in images
- 🌐 **Multi-Language Support** - Translates roasts using AI4Bharat/Sarvam APIs
- 🎬 **Video Generation** - Creates engaging roast videos via fal.ai
- 📦 **Job Management** - Redis-backed persistent job storage with TTL
- 🔔 **Webhook System** - Notifies backend when video processing completes
- ⚡ **Async Processing** - Non-blocking video generation with status tracking
- 🎨 **Streamlit UI** - Interactive web interface for local testing

---

## 🛠 Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | FastAPI, Uvicorn, Python 3.10+ |
| **AI/ML** | PyTorch, YOLOv5, Torchvision, OpenCV |
| **Database** | Redis (job storage & caching) |
| **APIs** | fal.ai, AI4Bharat, Sarvam |
| **Deployment** | Railway, Docker |
| **Testing** | Pytest, Pytest-asyncio |

---

## 🚀 Local Development Setup

### Prerequisites

- **Python**: 3.10 or higher
- **Redis**: Running instance (localhost:6379)
- **Git**: Version control
- **API Keys**: 
  - fal.ai API key (required)
  - AI4Bharat API key (optional)
  - Sarvam API key (optional)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Chetupatil24/GEN_AI.git
cd GEN_AI
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Note**: PyTorch installation may vary based on your system. Visit [PyTorch.org](https://pytorch.org/get-started/locally/) for specific installation commands.

### Step 4: Install and Start Redis

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

**macOS:**
```bash
brew install redis
brew services start redis

# Verify
redis-cli ping
```

**Windows:**
```bash
# Use WSL or download from: https://redis.io/download
```

### Step 5: Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# AI4Bharat Translation Configuration
AI4BHARAT_BASE_URL=http://localhost:5000
AI4BHARAT_TRANSLATE_PATH=/translate
AI4BHARAT_API_KEY=your_ai4bharat_key_here

# fal.ai API Configuration (Required for video generation)
FAL_API_KEY=your_fal_api_key_here
FAL_BASE_URL=https://api.fal.ai
FAL_MODEL_ID=fal-ai/minimax-video/image-to-video

# Redis Configuration (Local)
REDIS_URL=redis://localhost:6379/0
USE_REDIS=false
REDIS_JOB_TTL_SECONDS=86400

# Server Configuration
HOST=0.0.0.0
PORT=8000
REQUEST_TIMEOUT_SECONDS=30.0

# Webhook & CORS
BACKEND_WEBHOOK_URL=http://localhost:3000/webhooks/video-complete
CORS_ORIGINS=["http://localhost:3000","http://localhost:8501"]

# Retry Configuration
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=2.0
```

### Step 6: Start the Backend Server

```bash
# Start FastAPI server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Server will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
```

### Step 7: Start Streamlit UI (Optional)

In a new terminal:

```bash
# Activate virtual environment
source venv/bin/activate

# Start Streamlit
streamlit run streamlit_app.py

# UI will be available at:
# - http://localhost:8501
```

### Step 8: Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/healthz

# Should return: {"status":"ok"}
```

---

## 🚂 Railway Deployment

### Quick Deploy to Railway

1. **Fork/Clone this repository** to your GitHub account

2. **Go to Railway Dashboard**
   ```
   https://railway.app/dashboard
   ```

3. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked repository
   - Railway will auto-detect the `Dockerfile` ✅

4. **Add Redis Service**
   - In your project, click "New"
   - Select "Database" → "Redis"
   - Railway will automatically set `REDIS_URL` environment variable

5. **Configure Environment Variables**
   
   In Railway project settings, add these variables:

   ```env
   FAL_API_KEY=your_fal_api_key
   FAL_BASE_URL=https://api.fal.ai
   FAL_MODEL_ID=fal-ai/minimax-video/image-to-video
   AI4BHARAT_BASE_URL=http://localhost:5000
   AI4BHARAT_TRANSLATE_PATH=/translate
   AI4BHARAT_API_KEY=your_ai4bharat_key
   USE_REDIS=false
   REDIS_JOB_TTL_SECONDS=86400
   BACKEND_WEBHOOK_URL=https://your-backend.railway.app/webhooks/video-complete
   CORS_ORIGINS=["https://your-backend.railway.app"]
   ```

   **Note**: Railway automatically sets `REDIS_URL` when you add Redis service.

6. **Deploy**
   - Railway automatically deploys on every git push
   - Get your deployment URL: `https://your-service.up.railway.app`

7. **Verify Deployment**
   ```bash
   curl https://your-service.up.railway.app/healthz
   ```

### Railway Configuration Files

The project includes these Railway-specific files:

- **`Dockerfile`** - Container configuration for Railway
- **`railway.json`** - Railway build and deploy settings
- **`.env.railway`** - Environment variable template

### Continuous Deployment

```bash
# Make changes and push
git add .
git commit -m "Update feature"
git push origin main

# Railway automatically redeploys
```

---

## 📡 API Endpoints

### Health Check
```http
GET /healthz
```
**Response:**
```json
{"status": "ok"}
```

### Generate Video
```http
POST /api/generate-video
Content-Type: application/json

{
  "text": "Roast my lazy dog!",
  "image_url": "https://example.com/dog.jpg",
  "webhook_url": "https://optional-webhook.com/callback"
}
```
**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "processing"
}
```

### Check Video Status
```http
GET /api/video-status/{job_id}
```
**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://fal.ai/video/xyz.mp4",
  "created_at": "2026-01-10T10:30:00Z"
}
```

### Get Video Result
```http
GET /api/video-result/{job_id}
```
**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://revid.ai/video/xyz.mp4"
}
```

### Translate Text
```http
POST /api/translate-text
Content-Type: application/json

{
  "text": "Hello, how are you?",
  "source_language": "eng_Latn",
  "target_language": "hin_Deva"
}
```

### Video Completion Webhook (Internal)
```http
POST /api/webhook/video-complete
Content-Type: application/json

{
  "job_id": "abc123def456",
  "status": "completed",
  "video_url": "https://revid.ai/video/xyz.mp4"
}
```

📚 **Full API Documentation**: Visit `/docs` endpoint when server is running

---

## 🔐 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FAL_API_KEY` | fal.ai API key for video generation | ✅ Yes | - |
| `FAL_BASE_URL` | fal.ai API base URL | No | `https://api.fal.ai` |
| `FAL_MODEL_ID` | fal.ai model identifier | No | `fal-ai/minimax-video/image-to-video` |
| `AI4BHARAT_BASE_URL` | AI4Bharat translation server URL | No | `http://localhost:5000` |
| `AI4BHARAT_TRANSLATE_PATH` | AI4Bharat translation endpoint path | No | `/translate` |
| `AI4BHARAT_API_KEY` | AI4Bharat translation API key | ⚠️ Optional | - |
| `SARVAM_API_KEY` | Sarvam translation API key | ⚠️ Optional | - |
| `REDIS_URL` | Redis connection URL | ✅ Yes | `redis://localhost:6379` |
| `USE_REDIS` | Enable Redis job storage | No | `true` |
| `REDIS_JOB_TTL_SECONDS` | Job expiration time in Redis | No | `86400` (24h) |
| `BACKEND_WEBHOOK_URL` | Backend webhook for notifications | No | - |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | No | `["*"]` |
| `HOST` | Server host | No | `0.0.0.0` |
| `PORT` | Server port | No | `8000` |
| `REQUEST_TIMEOUT_SECONDS` | HTTP request timeout | No | `30.0` |
| `MAX_RETRIES` | API retry attempts | No | `3` |
| `RETRY_BACKOFF_FACTOR` | Retry backoff multiplier | No | `2.0` |

---

## 📁 Project Structure

```
pet_roasts/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── dependencies.py            # Dependency injection
│   ├── schemas.py                 # Pydantic models
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # API route handlers
│   │
│   ├── clients/
│   │   ├── ai4bharat.py           # AI4Bharat translation client
│   │   ├── fal.py                 # fal.ai video generation client
│   │   ├── revid.py               # Revid video generation client (deprecated)
│   │   └── sarvam.py              # Sarvam translation client
│   │
│   ├── core/
│   │   ├── config.py              # Configuration management
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── webhook.py             # Webhook utilities
│   │
│   └── services/
│       ├── job_store.py           # In-memory job storage
│       ├── redis_job_store.py     # Redis job storage
│       └── pet_detection.py       # YOLOv5 pet detection
│
├── IndicTrans2/                   # Translation model (submodule)
├── .env.example                   # Environment template
├── .env.railway                   # Railway env template
├── .gitignore                     # Git ignore rules
├── Dockerfile                     # Docker container config
├── railway.json                   # Railway deployment config
├── requirements.txt               # Python dependencies
├── streamlit_app.py               # Streamlit web UI
└── README.md                      # This file
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest test_integration.py -v
```

### Manual Testing with cURL

**Generate Video:**
```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Roast my lazy cat!",
    "image_url": "https://example.com/cat.jpg"
  }'
```

**Check Status:**
```bash
curl http://localhost:8000/api/video-status/YOUR_JOB_ID
```

### Using Streamlit UI

1. Start Streamlit: `streamlit run streamlit_app.py`
2. Open browser: http://localhost:8501
3. Upload pet image and enter roast text
4. Click "Generate Roast Video"
5. Monitor status and download video when ready

---

## 🔧 Troubleshooting

### Redis Connection Failed

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
sudo systemctl start redis-server

# Check Redis logs
sudo journalctl -u redis-server -n 50
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### PyTorch Installation Issues

```bash
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CPU only
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Railway Deployment Issues

1. **Check build logs** in Railway dashboard
2. **Verify environment variables** are set correctly
3. **Ensure Redis addon** is connected
4. **Check application logs** for runtime errors

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [YOLOv5](https://github.com/ultralytics/yolov5) - Pet detection model
- [fal.ai](https://fal.ai/) - Video generation API
- [AI4Bharat](https://ai4bharat.org/) - Translation services
- [Railway](https://railway.app/) - Deployment platform

---

## 📧 Contact & Support

- **GitHub Issues**: [Create an issue](https://github.com/Chetupatil24/GEN_AI/issues)
- **GitHub Repository**: https://github.com/Chetupatil24/GEN_AI
- **Documentation**: Check `/docs` endpoint when server is running

---

## 🎯 Roadmap

- [ ] Add support for multiple pets in single image
- [ ] Implement video caching for repeated roasts
- [ ] Add more translation language pairs
- [ ] Create mobile app integration
- [ ] Add rate limiting and authentication
- [ ] Implement batch video generation

---

**Made with ❤️ by the Pet Roast AI Team**
