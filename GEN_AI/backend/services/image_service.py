import fal_client
import os
import logging
import asyncio
from backend.config import settings

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        # Fal client automatically picks up FAL_KEY from env,
        # but we check settings to ensure it's there
        if not settings.FAL_KEY:
            logger.warning("FAL_KEY not set.")

    async def generate_image(self, prompt: str) -> str:
        """
        Generates an image using fal-ai/flux/schnell (Low Cost).
        Returns the image URL.
        """
        try:
            handler = await fal_client.submit_async(
                "fal-ai/flux/schnell",
                arguments={
                    "prompt": prompt,
                    "image_size": "portrait_4_3",
                    "num_inference_steps": 4
                },
            )
            result = await asyncio.wait_for(handler.get(), timeout=120.0)
            image_url = result["images"][0]["url"]
            return image_url
        except asyncio.TimeoutError:
            logger.error("Fal.ai image generation timed out after 120 seconds. Aborting.")
            raise Exception("Timeout: Image generation took longer than 120 seconds")
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
