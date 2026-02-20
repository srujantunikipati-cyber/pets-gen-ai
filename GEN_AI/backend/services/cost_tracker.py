import logging

logger = logging.getLogger(__name__)

class CostTracker:
    # Estimated costs (USD) - rough approximation
    COSTS = {
        "flux_schnell": 0.003, # per image
        "kling_video": 0.10,    # per 5s (approx)
        "gemini_flash": 0.0001, # per request
        "edge_tts": 0.0,
        "compute": 0.0          # Local
    }
    
    @staticmethod
    def calculate_cost(steps: dict) -> float:
        total = 0.0
        if steps.get("image_generated"):
            total += CostTracker.COSTS["flux_schnell"]
        if steps.get("video_generated"):
            total += CostTracker.COSTS["kling_video"]
        if steps.get("script_generated"):
            total += CostTracker.COSTS["gemini_flash"]
            
        logger.info(f"Estimated cost for job: ${total:.4f}")
        return total
