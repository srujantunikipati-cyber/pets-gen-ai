# 🚀 Fly.io Deployment Guide

## Why Fly.io?

✅ **Excellent Docker support**  
✅ **Global edge deployment**  
✅ **Free tier available**  
✅ **CLI-based (perfect for remote)**  
✅ **Fast deployments**  
✅ **Great for production**  

---

## Step 1: Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
```

Or via package manager:
```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh
```

---

## Step 2: Login to Fly.io

```bash
fly auth login
# Opens browser - authenticate
```

---

## Step 3: Create Fly App

```bash
cd /home/chetan-patil/myprojects/1/GEN_AI
fly launch
```

**Follow prompts:**
- App name: `gen-ai-app` (or auto-generated)
- Region: Choose closest
- PostgreSQL: No (unless needed)
- Redis: Yes (optional, recommended)

---

## Step 4: Configure fly.toml

Fly will create `fly.toml`. Update it:

```toml
app = "gen-ai-app"
primary_region = "iad"  # Your region

[build]
  dockerfile = "Dockerfile"

[env]
  FAL_API_KEY = "0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a"
  FAL_BASE_URL = "https://queue.fal.run"
  FAL_MODEL_ID = "fal-ai/minimax-video"
  VIDEO_STORAGE_PATH = "storage/videos"
  USE_REDIS = "true"

[[services]]
  internal_port = 8000
  protocol = "tcp"
```

---

## Step 5: Set Secrets (Environment Variables)

```bash
fly secrets set FAL_API_KEY="0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a"
fly secrets set FAL_BASE_URL="https://queue.fal.run"
fly secrets set FAL_MODEL_ID="fal-ai/minimax-video"
fly secrets set VIDEO_STORAGE_PATH="storage/videos"
fly secrets set USE_REDIS="true"
```

---

## Step 6: Deploy

```bash
fly deploy
```

Fly will:
- Build Docker image
- Deploy to edge locations
- Provide public URL

---

## Step 7: Get Your URL

```bash
fly status
```

Your app will be at:
```
https://gen-ai-app.fly.dev
```

---

## Step 8: Remote Access Commands

```bash
# View logs
fly logs

# SSH into container
fly ssh console

# View status
fly status

# Scale app
fly scale count 1

# View metrics
fly metrics
```

---

## ✅ Advantages of Fly.io

- ✅ **Global edge deployment** (fast worldwide)
- ✅ **Excellent CLI** (perfect remote access)
- ✅ **Free tier** available
- ✅ **Great for Docker**
- ✅ **Production-ready**

---

**✅ Fly.io is excellent for Docker apps with CLI access!**
