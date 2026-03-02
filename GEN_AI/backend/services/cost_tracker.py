import logging

logger = logging.getLogger(__name__)

class CostTracker:
    # Estimated costs (USD) per request
    COSTS = {
        "flux_schnell":      0.003,    # fal.ai Flux Schnell — per image
        "kling_video":       0.10,     # fal.ai Kling 1.6 — per 3s clip
        "openai_gpt4o_mini": 0.0002,  # GPT-4o-mini — ~500 tokens in+out
        "edge_tts":          0.0,      # free (Microsoft Edge TTS)
        "whisper":           0.0,      # free (self-hosted faster-whisper)
        "indictrans2":       0.0,      # free (self-hosted)
    }

    @staticmethod
    def calculate_cost(steps: dict) -> float:
        total = 0.0
        if steps.get("image_generated"):
            total += CostTracker.COSTS["flux_schnell"]
        if steps.get("video_generated"):
            total += CostTracker.COSTS["kling_video"]
        if steps.get("script_generated"):
            total += CostTracker.COSTS["openai_gpt4o_mini"]

        logger.info(f"Estimated cost for job: ${total:.4f}")
        return total
