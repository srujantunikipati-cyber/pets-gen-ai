# Deployment Guide: Low-Cost Video Pipeline

## Prerequisites
- Ubuntu 22.04 VPS (e.g., DigitalOcean, Hetzner)
- Docker & Docker Compose
- Redis (can be run via Docker)
- FFmpeg (installed on host or inside Docker)

## Installation

1.  **Clone Repository**
    ```bash
    git clone <repo_url>
    cd GEN_AI/backend
    ```

2.  **Environment Setup**
    Copy `.env.example` to `.env` and fill in your keys.
    ```bash
    cp .env.example .env
    ```

3.  **Run with Docker Compose**
    ```bash
    docker-compose up -d --build
    ```

## Manual Run (No Docker)

1.  **Start Redis**
    ```bash
    redis-server
    ```

2.  **Start Worker**
    ```bash
    arq backend.workers.video_worker.WorkerSettings
    ```

3.  **Start API**
    ```bash
    uvicorn backend.main:app --reload
    ```

## Usage

**Generate Video (POST)**
```http
POST http://localhost:8000/api/generate
Content-Type: application/json

{
  "topic": "roast my cat for sleeping all day"
}
```

**Check Status (GET)**
```http
GET http://localhost:8000/api/jobs/{job_id}
```
