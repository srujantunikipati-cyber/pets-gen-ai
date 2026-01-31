"""Pet detection service - Simplified version without YOLO."""

import logging
from typing import List, Tuple, Any, Optional
import httpx

_logger = logging.getLogger(__name__)


class PetDetectionService:
    """
    Simplified pet detection service.
    Assumes all images/videos contain pets - FAL AI will validate during generation.
    """

    def __init__(self, model_name: str = "none", confidence_threshold: float = 0.5, model_path: Optional[str] = None):
        """Initialize simplified pet detection service."""
        _logger.info("✅ Pet detection service initialized (validation delegated to FAL AI)")

    async def detect_pets_in_image_url(
        self,
        image_source: str,
        client: Optional[httpx.AsyncClient] = None
    ) -> Tuple[bool, List[str], Any]:
        """
        Simplified pet detection - always returns True.
        Actual pet validation will be done by FAL AI during video generation.
        
        Args:
            image_source: Image URL or base64 data
            client: Optional HTTP client
            
        Returns:
            Tuple of (has_pets: bool, detected_pets: List[str], confidence: Any)
        """
        _logger.info("🔍 Pet detection called - assuming pets present (will be validated by FAL AI)")
        return (True, ["pet"], None)

    async def detect_pets_in_video(
        self,
        video_path: str
    ) -> Tuple[bool, List[str], Any]:
        """
        Simplified video pet detection - always returns True.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (has_pets: bool, detected_pets: List[str], confidence: Any)
        """
        _logger.info("🔍 Video pet detection called - assuming pets present")
        return (True, ["pet"], None)


# Singleton instance
_pet_detector_instance: Optional[PetDetectionService] = None


def get_pet_detector() -> PetDetectionService:
    """Get or create the singleton pet detector instance."""
    global _pet_detector_instance
    if _pet_detector_instance is None:
        _pet_detector_instance = PetDetectionService()
    return _pet_detector_instance
