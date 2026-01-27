# 🚀 Render Deployment Guide - RECOMMENDED

## Why Render?

✅ **Easiest alternative to Railway**  
✅ **Free tier available**  
✅ **Auto-deploy from GitHub**  
✅ **Docker support**  
✅ **CLI for remote access**  
✅ **No credit card needed**  

---

## Step 1: Create Render Account

1. Go to: https://render.com
2. Click: "Get Started for Free"
3. Sign up with GitHub (recommended)
4. Verify email

---

## Step 2: Create New Web Service

1. **In Render Dashboard**, click **"New +"**
2. **Select**: "Web Service"
3. **Connect**: Your GitHub account
4. **Select Repository**: `Chetupatil24/GEN_AI`
5. **Click**: "Connect"

---

## Step 3: Configure Service

### Basic Settings

- **Name**: `gen-ai-app` (or any name)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave empty (or `/`)

### Build & Deploy

- **Environment**: `Docker`
- **Dockerfile Path**: `Dockerfile` (auto-detected)
- **Docker Context**: Leave empty

### Start Command

**Leave empty** - Render uses Dockerfile CMD

---

## Step 4: Set Environment Variables

Click **"Environment"** tab → Add these variables:

### Required Variables

```
FAL_API_KEY=0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a
```

```
FAL_BASE_URL=https://queue.fal.run
```

```
FAL_MODEL_ID=fal-ai/minimax-video
```

```
VIDEO_STORAGE_PATH=storage/videos
```

```
USE_REDIS=true
```

### Optional Variables

```
AI4BHARAT_BASE_URL=http://localhost:5000
AI4BHARAT_TRANSLATE_PATH=/translate
REQUEST_TIMEOUT_SECONDS=30.0
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=1.5
```

---

## Step 5: Deploy

1. **Click**: "Create Web Service"
2. **Render will**:
   - Build Docker image
   - Deploy your app
   - Provide public URL
3. **Wait for**: "Live" status (3-5 minutes)

---

## Step 6: Get Your URL

Your app will be available at:
```
https://gen-ai-app.onrender.com
```
(Or your custom domain if configured)

---

## Step 7: Remote Access via Render CLI

### Install Render CLI

```bash
npm install -g render-cli
```

### Login

```bash
render login
# Opens browser - authenticate
```

### View Logs

```bash
render logs --service gen-ai-app
```

### View Services

```bash
render services list
```

### Set Variables via CLI

```bash
render env set FAL_API_KEY="0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a" --service gen-ai-app
```

---

## Step 8: Test Deployment

```bash
curl https://gen-ai-app.onrender.com/healthz
```

Expected: `{"status":"ok"}`

---

## ✅ Advantages of Render

- ✅ **Free tier** (no credit card)
- ✅ **Auto-deploy** on git push
- ✅ **Easy CLI** for remote access
- ✅ **Docker support**
- ✅ **Simple interface**
- ✅ **Good documentation**

---

## 📋 Render CLI Commands

```bash
# Login
render login

# List services
render services list

# View logs
render logs --service <service-name>

# Set environment variable
render env set KEY="value" --service <service-name>

# View environment variables
render env list --service <service-name>

# Restart service
render services restart <service-id>
```

---

**✅ Render is the easiest alternative to Railway!**
