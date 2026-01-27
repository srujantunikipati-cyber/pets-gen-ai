# 🚂 Railway Quick Start - 5 Minutes

## Step 1: Connect GitHub Repo (2 min)

1. Go to: https://railway.app/dashboard
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select: `srujantunikipati-cyber/pets-gen-ai`
4. Railway auto-detects `Dockerfile` ✅

## Step 2: Add Redis (1 min)

1. In project, click **"New"** → **"Database"** → **"Redis"**
2. Railway auto-sets `REDIS_URL` ✅

## Step 3: Set Environment Variables (2 min)

Go to **Service** → **Variables** → Add these:

```bash
FAL_API_KEY=0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a
FAL_BASE_URL=https://queue.fal.run
FAL_MODEL_ID=fal-ai/minimax-video
USE_REDIS=true
```

## Step 4: Deploy! 🚀

Railway automatically:
- Builds Docker image
- Deploys service
- Provides URL: `https://your-service.up.railway.app`

## Step 5: Test

```bash
curl https://your-service.up.railway.app/healthz
```

Should return: `{"status":"ok"}`

---

**That's it!** Your app is live! 🎉

For detailed setup, see `RAILWAY_DEPLOYMENT_GUIDE.md`
