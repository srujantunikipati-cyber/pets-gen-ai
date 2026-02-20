from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from arq import create_pool
from arq.connections import RedisSettings
from backend.config import settings
import uuid
import logging

from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

class GenerateRequest(BaseModel):
    topic: Optional[str] = None
    image_url: Optional[str] = Field(default=None, validation_alias="imageUrl")
    video_url: Optional[str] = Field(default=None, validation_alias="videoUrl")
    user_id: Optional[str] = Field(default=None, validation_alias="userId")
    
class GenerateResponse(BaseModel):
    job_id: str
    status: str = "processing"

@router.post("/generate-video", response_model=GenerateResponse)
async def generate_video(req: GenerateRequest):
    """
    Starts a video generation job.
    """
    if not req.topic and not req.image_url and not req.video_url:
        raise HTTPException(status_code=400, detail="Topic, Image URL, or Video URL required")
        
    job_id = str(uuid.uuid4())
    
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        await redis.enqueue_job("generate_video_job", req.model_dump(), _job_id=job_id)
        await redis.close()
        
        return {"job_id": job_id, "status": "processing"}
    except Exception as e:
        logger.error(f"Failed to enqueue job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video-result/{id}")
async def get_video_result(id: str):
    """
    Checks job status.
    """
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        # arq doesn't have a simple "get status without waiting" if the result isn't ready, except checking raw redis
        
        from arq.jobs import Job
        job_def = Job(id, redis)
        status = await job_def.status()
        info = await job_def.info()
        result = await job_def.result(timeout=0.1) if status == "complete" else None
        
        await redis.close()
        
        # Format the response specifically for the pets-backend expectations
        status_val = status.value if hasattr(status, 'value') else str(status).split('.')[-1]
        str_status = "completed" if status_val == "complete" else status_val
        
        response_data = {
            "job_id": id,
            "status": str_status
        }
        
        if result and isinstance(result, dict):
            response_data.update(result)
            
        return response_data
        
    except Exception as e:
        # Timeout on result is expected if not done
        return {"job_id": id, "status": "processing", "error": str(e)}
