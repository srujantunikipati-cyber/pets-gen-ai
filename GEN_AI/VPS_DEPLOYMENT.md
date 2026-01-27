# 🖥️ VPS Deployment Guide (DigitalOcean/Linode)

## Why VPS?

✅ **Full control**  
✅ **SSH access** (perfect remote)  
✅ **Most flexible**  
✅ **Cost-effective**  
✅ **No platform limitations**  

---

## Step 1: Create VPS

### DigitalOcean

1. Go to: https://digitalocean.com
2. Create Droplet:
   - **Image**: Ubuntu 22.04
   - **Size**: 2GB RAM minimum (4GB recommended)
   - **Region**: Choose closest
   - **Add SSH key** (recommended)

### Linode

1. Go to: https://linode.com
2. Create Linode:
   - **Distribution**: Ubuntu 22.04
   - **Plan**: 2GB RAM minimum
   - **Region**: Choose closest

---

## Step 2: SSH into VPS

```bash
ssh root@your-server-ip
```

Or with key:
```bash
ssh -i ~/.ssh/your-key root@your-server-ip
```

---

## Step 3: Initial Setup

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Install Git
apt install git -y
```

---

## Step 4: Clone Repository

```bash
cd /opt
git clone https://github.com/Chetupatil24/GEN_AI.git
cd GEN_AI
```

---

## Step 5: Create .env File

```bash
nano .env
```

Add:
```
FAL_API_KEY=0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a
FAL_BASE_URL=https://queue.fal.run
FAL_MODEL_ID=fal-ai/minimax-video
VIDEO_STORAGE_PATH=storage/videos
USE_REDIS=true
AI4BHARAT_BASE_URL=http://localhost:5000
AI4BHARAT_TRANSLATE_PATH=/translate
REQUEST_TIMEOUT_SECONDS=30.0
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=1.5
```

Save: `Ctrl+X`, then `Y`, then `Enter`

---

## Step 6: Build and Run

```bash
# Build Docker image
docker build -t gen-ai-app .

# Run container
docker run -d \
  --name gen-ai-app \
  --env-file .env \
  -p 80:8000 \
  --restart unless-stopped \
  gen-ai-app
```

---

## Step 7: Setup Nginx (Reverse Proxy)

```bash
# Install Nginx
apt install nginx -y

# Create config
nano /etc/nginx/sites-available/gen-ai
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:
```bash
ln -s /etc/nginx/sites-available/gen-ai /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## Step 8: Setup SSL (Let's Encrypt)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

---

## Step 9: Remote Access

### SSH Access

```bash
ssh root@your-server-ip
```

### View Logs

```bash
docker logs -f gen-ai-app
```

### Restart App

```bash
docker restart gen-ai-app
```

### Update App

```bash
cd /opt/GEN_AI
git pull
docker build -t gen-ai-app .
docker stop gen-ai-app
docker rm gen-ai-app
docker run -d --name gen-ai-app --env-file .env -p 80:8000 --restart unless-stopped gen-ai-app
```

---

## ✅ Advantages of VPS

- ✅ **Full SSH access** (perfect remote)
- ✅ **Complete control**
- ✅ **Cost-effective** ($5-10/month)
- ✅ **No platform limitations**
- ✅ **Custom configuration**

---

**✅ VPS is best for full control and SSH access!**
