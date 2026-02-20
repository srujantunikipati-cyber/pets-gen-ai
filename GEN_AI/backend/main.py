from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.video_routes import router as video_router
from backend.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pet Roast AI - Low Cost Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Pet Roast AI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
