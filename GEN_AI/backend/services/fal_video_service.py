import fal_client
import os
import logging
import asyncio
from backend.config import settings

logger = logging.getLogger(__name__)

class FalVideoService:
    def __init__(self):
        self.api_key = settings.FAL_KEY
        if not self.api_key:
            logger.warning("FAL_KEY not set. Video generation will fail.")

    async def generate_video(self, image_url: str, prompt: str) -> str:
        """
        Generates a 3-second video using Kling 1.6 Standard.
        Cost Optimized: Only 3 seconds.
        """
        try:
            logger.info(f"Submitting Kling video job for image: {image_url}")
            handler = await fal_client.submit_async(
                "fal-ai/kling-video/v1.6/standard/image-to-video",
                arguments={
                    "prompt": prompt,
                    "image_url": image_url,
                    "duration": "3",
                    "width": 512,
                    "height": 512,
                    "num_inference_steps": 16
                },
            )
            # 120 Second Timeout implementation
            result = await asyncio.wait_for(handler.get(), timeout=120.0)
            video_url = result["video"]["url"]
            return video_url
        except asyncio.TimeoutError:
            logger.error("Fal.ai video generation timed out after 120 seconds. Aborting.")
            raise Exception("Timeout: Video generation took longer than 120 seconds")
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
