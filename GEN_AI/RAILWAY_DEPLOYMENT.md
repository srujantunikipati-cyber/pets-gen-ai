# 🚂 Railway Deployment Guide

Complete guide to deploy the Pet Roast AI service on Railway.

## 📋 Prerequisites

1. Railway account: https://railway.app
2. GitHub repository: https://github.com/Chetupatil24/GEN_AI
3. fal.ai API key

## 🚀 Deployment Steps

### Step 1: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select repository: **Chetupatil24/GEN_AI**
6. Railway will automatically detect the Dockerfile

### Step 2: Add Environment Variables

Go to your Railway project → **Variables** tab and add:

#### Required Variables:

```bash
FAL_API_KEY=0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a
FAL_BASE_URL=https://queue.fal.run
FAL_MODEL_ID=fal-ai/minimax-video
```

#### Optional but Recommended:

```bash
USE_REDIS=true
VIDEO_STORAGE_PATH=storage/videos
REQUEST_TIMEOUT_SECONDS=30.0
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=1.5
```

#### CORS Configuration:

```bash
CORS_ORIGINS=["*"]
```

### Step 3: Add Redis Service (Optional but Recommended)

1. In Railway project, click **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway will automatically set `REDIS_URL` environment variable
3. Set `USE_REDIS=true` in variables

### Step 4: Deploy

1. Railway will automatically start building and deploying
2. Monitor the **Deployments** tab for build logs
3. Check **Logs** tab for runtime logs

### Step 5: Get Your Public URL

1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"** to get a public URL
3. Your API will be available at: `https://your-app.railway.app`

## 🔧 Troubleshooting

### Build Fails

**Issue**: Docker build fails
**Solution**: 
- Check build logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Dockerfile syntax

### Application Crashes

**Issue**: App starts but crashes immediately
**Solution**:
- Check runtime logs
- Verify all required environment variables are set
- Ensure `FAL_API_KEY` is correct

### Redis Connection Error

**Issue**: `Redis connection failed`
**Solution**:
- Verify Redis service is added
- Check `REDIS_URL` is set automatically
- Set `USE_REDIS=false` to use in-memory storage temporarily

### Video Generation Not Working

**Issue**: Videos show status but don't generate
**Solution**:
- Verify `FAL_API_KEY` is correct
- Check `FAL_BASE_URL` is `https://queue.fal.run`
- Check `FAL_MODEL_ID` is `fal-ai/minimax-video`
- Review application logs for fal.ai API errors

## 📊 Monitoring

### Health Check

Your API health endpoint:
```
GET https://your-app.railway.app/healthz
```

Expected response:
```json
{"status": "ok"}
```

### API Documentation

Access Swagger UI:
```
https://your-app.railway.app/docs
```

## 🔐 Security Notes

1. **Never commit API keys** to GitHub
2. Use Railway's **Variables** for sensitive data
3. Set `CORS_ORIGINS` to specific domains in production
4. Consider adding authentication for production use

## 📝 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `FAL_API_KEY` | ✅ Yes | fal.ai API key |
| `FAL_BASE_URL` | No | fal.ai API URL (default: `https://queue.fal.run`) |
| `FAL_MODEL_ID` | No | fal.ai model ID (default: `fal-ai/minimax-video`) |
| `USE_REDIS` | No | Enable Redis (default: `true`) |
| `REDIS_URL` | Auto | Set automatically by Railway Redis addon |
| `VIDEO_STORAGE_PATH` | No | Video storage directory (default: `storage/videos`) |

## 🎯 Post-Deployment

1. Test health endpoint: `GET /healthz`
2. Test video generation: `POST /api/generate-video`
3. Monitor logs for any errors
4. Check video storage directory (if persistent volumes enabled)

## 📞 Support

- Railway Docs: https://docs.railway.app
- GitHub Issues: https://github.com/Chetupatil24/GEN_AI/issues
- Railway Support: support@railway.app

---

**Happy Deploying! 🚀**
