# pets-backend Integration Guide

## Overview

This document describes how GEN_AI integrates with the pets-backend GraphQL server for a complete pet roasting application.

## Architecture

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────┐
│  Frontend App   │────────▶│ pets-backend │────────▶│   GEN_AI    │
│  (Mobile/Web)   │         │ (GraphQL)    │         │  (FastAPI)  │
└─────────────────┘         └──────────────┘         └─────────────┘
                                      │                       │
                                      │                       │
                                      ▼                       ▼
                              ┌──────────────┐         ┌─────────────┐
                              │   MongoDB    │         │   fal.ai    │
                              │  (Job Store) │         │ (Video Gen) │
                              └──────────────┘         └─────────────┘
```

## Flow

1. **User Request**:
   - Frontend sends GraphQL mutation to pets-backend: `generateImage(userId, prompt, image)`
   - pets-backend authenticates user via Firebase JWT token

2. **Job Creation**:
   - pets-backend uploads image to Cloudflare R2
   - pets-backend creates job record in MongoDB
   - pets-backend calls GEN_AI: `POST /api/generate-video`

3. **Video Generation**:
   - GEN_AI processes request (pet detection, translation, etc.)
   - GEN_AI submits job to fal.ai
   - GEN_AI stores job status in Redis

4. **Status Updates**:
   - Frontend polls pets-backend: `checkVideoStatus(jobId)`
   - pets-backend checks MongoDB, then calls GEN_AI: `GET /api/video-status/{job_id}`
   - pets-backend updates MongoDB with latest status

5. **Completion**:
   - fal.ai completes video generation
   - GEN_AI receives webhook from fal.ai (or polls status)
   - GEN_AI notifies pets-backend via webhook: `POST {BACKEND_WEBHOOK_URL}`
   - pets-backend updates MongoDB with video URL

## Configuration

### GEN_AI Environment Variables

```bash
# pets-backend Integration
PETS_BACKEND_URL=http://localhost:4000          # GraphQL server URL
PETS_BACKEND_ENABLED=true                      # Enable integration
PETS_BACKEND_API_URL=http://localhost:4000     # REST API URL (same as GraphQL)

# Webhook for notifying pets-backend
BACKEND_WEBHOOK_URL=http://localhost:4000/webhooks/pet-roast-complete
```

### pets-backend Environment Variables

```bash
# GEN_AI Service URL
PET_ROAST_API_URL=http://localhost:8000/api
```

## API Endpoints

### GEN_AI Endpoints (Called by pets-backend)

1. **Generate Video**:
   ```bash
   POST /api/generate-video
   {
     "text": "Roast my lazy dog!",
     "image_url": "https://...",
     "user_id": "optional-user-id",
     "auth_token": "optional-jwt-token"
   }
   ```

2. **Check Status**:
   ```bash
   GET /api/video-status/{job_id}
   ```

3. **Get Result**:
   ```bash
   GET /api/video-result/{job_id}
   ```

4. **Webhook (from fal.ai)**:
   ```bash
   POST /api/webhook/video-complete
   {
     "job_id": "...",
     "status": "completed",
     "video_url": "https://..."
   }
   ```

### pets-backend GraphQL (Called by Frontend)

1. **Generate Image/Video**:
   ```graphql
   mutation GenerateImage {
     generateImage(
       userId: "user123"
       prompt: "Roast my lazy dog!"
       image: Upload
     ) {
       status
       code
       message
       data {
         jobId
         status
         inputImageUrl
       }
     }
   }
   ```

2. **Check Status**:
   ```graphql
   query CheckStatus {
     checkVideoStatus(jobId: "job123") {
       status
       code
       message
       data {
         jobId
         status
         videoUrl
       }
     }
   }
   ```

## Authentication

### JWT Token Flow

1. Frontend authenticates user via pets-backend (Firebase)
2. Frontend receives JWT token
3. Frontend sends token in GraphQL requests to pets-backend
4. pets-backend verifies token via Firebase Admin
5. pets-backend can optionally forward token to GEN_AI for user context

### GEN_AI Token Verification (Optional)

If `auth_token` is provided in `GenerateVideoRequest`:
- GEN_AI can verify token with pets-backend GraphQL
- GEN_AI can get user information for logging/tracking
- Token verification is non-blocking (errors are logged but don't fail the request)

## Webhook Integration

When a video generation job completes:

1. **GEN_AI** sends webhook to pets-backend:
   ```json
   POST {BACKEND_WEBHOOK_URL}
   {
     "job_id": "abc123",
     "status": "completed",
     "video_url": "https://fal.ai/video/xyz.mp4",
     "user_id": "user123",  // if available
     "error": null
   }
   ```

2. **pets-backend** receives webhook and:
   - Updates MongoDB job record
   - Sets `status = "completed"`
   - Sets `outputVideoUrl = video_url`
   - Notifies frontend via Socket.io (if connected)

## Error Handling

- **GEN_AI errors**: Returned to pets-backend, which handles them gracefully
- **pets-backend errors**: Logged and returned to frontend
- **Network errors**: Retry logic in both services
- **Token verification failures**: Non-blocking in GEN_AI (logged only)

## Testing Integration

### 1. Start pets-backend:
```bash
cd pets-backend
npm install
npm run dev
# Server runs on http://localhost:4000
```

### 2. Start GEN_AI:
```bash
cd GEN_AI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Server runs on http://localhost:8000
```

### 3. Test GraphQL Mutation:
```graphql
mutation {
  generateImage(
    userId: "test-user"
    prompt: "Roast my dog!"
    image: [upload file]
  ) {
    status
    code
    message
    data {
      jobId
      status
    }
  }
}
```

### 4. Check Status:
```graphql
query {
  checkVideoStatus(jobId: "job-id-from-step-3") {
    status
    code
    data {
      jobId
      status
      videoUrl
    }
  }
}
```

## Deployment

### Railway Deployment

1. **pets-backend**:
   - Deploy to Railway
   - Set `PET_ROAST_API_URL` to GEN_AI Railway URL
   - Set webhook endpoint: `https://your-pets-backend.railway.app/webhooks/pet-roast-complete`

2. **GEN_AI**:
   - Deploy to Railway
   - Set `PETS_BACKEND_URL` to pets-backend Railway URL
   - Set `BACKEND_WEBHOOK_URL` to pets-backend webhook endpoint
   - Set `PETS_BACKEND_ENABLED=true`

## Troubleshooting

### Issue: Webhook not received
- Check `BACKEND_WEBHOOK_URL` is set correctly
- Verify pets-backend webhook endpoint exists
- Check Railway logs for webhook delivery errors

### Issue: Token verification fails
- Verify Firebase Admin is configured in pets-backend
- Check token format (should be Firebase JWT)
- Token verification is optional - check logs for details

### Issue: Jobs not updating
- Check Redis connection (GEN_AI)
- Check MongoDB connection (pets-backend)
- Verify webhook is being called
- Check status polling is working

---

**Integration is complete and ready for production!** 🎉
