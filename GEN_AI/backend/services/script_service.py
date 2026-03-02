import os
import json
import logging
from typing import Dict, Any, Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a hilarious roast comedian specialising in funny, friendly pet roasts. "
    "You write SHORT punchy roast scripts (10-15 seconds spoken) that are funny but never mean or abusive. "
    "You always reply exclusively with valid JSON — no markdown fences, no extra prose."
)

_USER_TEMPLATE = """Write a short, hilarious roast script about this pet topic: "{topic}".
{context_hint}
Constraints:
1. Duration: Exactly 10-15 seconds when spoken aloud (≈ 30-45 words).
2. Tone: Funny, roasting, but friendly — never mean, never abusive.
3. The "image_prompt" field must be a rich, detailed prompt for an AI image generator (Flux Schnell).
   It MUST include: pet species/breed appearance, funny action or expression, scene/background,
   photographic style qualifiers like "photorealistic", "cinematic lighting", "shallow depth of field",
   "4K", "high detail", "funny expression", "vibrant colors". Keep it under 120 words.
4. Return ONLY valid JSON matching this exact structure:
{{
    "script": "The full roast text (30-45 words).",
    "captions": [
        {{"text": "First sentence", "start": 0.0, "end": 2.5}},
        {{"text": "Second sentence", "start": 2.5, "end": 5.5}}
    ],
    "image_prompt": "Rich detailed Flux Schnell image generation prompt here."
}}"""


class ScriptService:
    """Generates pet roast scripts via OpenAI GPT-4o-mini."""

    def __init__(self) -> None:
        self.api_key: str = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set — script generation will use fallback templates.")
            self._client: AsyncOpenAI | None = None
        else:
            self._client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Cost-effective, fast, high quality

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_script(
        self,
        topic: str,
        *,
        pet_type: Optional[str] = None,
        detected_language: Optional[str] = None,
        pet_emotion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a funny roast script for *topic*.

        Args:
            topic:             Cleaned English description of the pet/situation.
            pet_type:          YOLO-detected class label, e.g. "dog", "cat" (optional).
            detected_language: Whisper-detected source language code, e.g. "hi" (optional).

        Returns:
            dict with keys: ``script``, ``captions``, ``image_prompt``
        """
        if not self._client:
            logger.info("No OPENAI_API_KEY — returning fallback script.")
            return self._fallback_script(topic, pet_type=pet_type, pet_emotion=pet_emotion)

        # Build optional context hint
        context_parts = []
        if pet_type:
            context_parts.append(f"The pet is a {pet_type}.")
        if pet_emotion:
            context_parts.append(f"The pet looks {pet_emotion} in the video.")
        if detected_language and detected_language != "en":
            context_parts.append(
                f"The original audio was in language code '{detected_language}' "
                f"— keep the roast in English."
            )
        context_hint = ("\nContext: " + " ".join(context_parts) + "\n") if context_parts else ""

        prompt = _USER_TEMPLATE.format(topic=topic, context_hint=context_hint)
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            self._validate_script_data(data, topic)
            return data
        except json.JSONDecodeError as exc:
            logger.error(f"OpenAI returned non-JSON response: {exc}")
            return self._fallback_script(topic, pet_type=pet_type, pet_emotion=pet_emotion)
        except Exception as exc:
            logger.error(f"Script generation failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # fal.ai prompt builders
    # ------------------------------------------------------------------

    @staticmethod
    def build_fal_image_prompt(gpt_image_prompt: str, topic: str, pet_type: Optional[str] = None, pet_emotion: Optional[str] = None) -> str:
        """
        Build an optimised Flux Schnell prompt from the GPT-generated image_prompt.

        Flux Schnell produces best results with:
        - Concrete visual descriptions (not narrative)
        - Photographic/cinematic style qualifiers
        - Subject → action → setting → style ordering

        Args:
            gpt_image_prompt: Raw image_prompt string from GPT.
            topic:            Cleaned topic text (used as fallback).
            pet_type:         Detected pet type for visual grounding.

        Returns:
            Enhanced prompt string (≤ 200 words).
        """
        # Strip any leading/trailing quotes GPT might add
        base = gpt_image_prompt.strip().strip('"').strip("'")
        if not base:
            emotion_desc = f" looking {pet_emotion}" if pet_emotion else " looking dramatic"
            base = f"A funny {pet_type or 'pet'}{emotion_desc}, {topic}"

        # Inject emotion into base if not already present
        if pet_emotion and pet_emotion.lower() not in base.lower():
            base = base.rstrip(".") + f", {pet_emotion} expression"

        # Append quality modifiers if not already present
        qualifiers = [
            "photorealistic",
            "cinematic lighting",
            "shallow depth of field",
            "4K",
            "vibrant colors",
            "high detail",
            "funny expression",
        ]
        lower_base = base.lower()
        missing = [q for q in qualifiers if q.lower() not in lower_base]
        if missing:
            base = base.rstrip(".") + ", " + ", ".join(missing) + "."

        return base

    @staticmethod
    def build_fal_video_prompt(image_prompt: str, script: str) -> str:
        """
        Build an optimised Kling 1.6 video-generation prompt from the image prompt and roast script.

        Kling works best with motion-oriented, cinematic descriptions.

        Args:
            image_prompt: The Flux Schnell image prompt (already enhanced).
            script:       The roast script (used to extract subject/mood).

        Returns:
            Kling-optimised video prompt (≤ 150 words).
        """
        # Extract first sentence of script as mood reference
        first_sentence = script.split(".")[0].strip() if script else ""

        # Build a cinematic motion description
        motion_prompt = (
            f"{image_prompt.rstrip('.')}. "
            f"The pet reacts with exaggerated comedic expression. "
            f"Slow cinematic zoom-in, soft bokeh background, playful motion, "
            f"warm golden-hour lighting, high quality, smooth camera movement."
        )
        # Keep within ~150 words
        words = motion_prompt.split()
        if len(words) > 150:
            motion_prompt = " ".join(words[:150]) + "."

        return motion_prompt

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_script(topic: str, *, pet_type: Optional[str] = None, pet_emotion: Optional[str] = None) -> Dict[str, Any]:
        """Template-based fallback when no API key is available."""
        animal = pet_type or "pet"
        emotion_desc = f"{pet_emotion} and" if pet_emotion else ""
        image_prompt = (
            f"A hilariously {emotion_desc} dramatic {animal}, funny expression, comedic pose, "
            f"related to: {topic}. Photorealistic, cinematic lighting, shallow depth of field, "
            f"4K, vibrant colors, high detail."
        )
        return {
            "script": (
                f"Oh wow, look at this {animal}! "
                "This little furball has more drama than a reality TV show. "
                "Absolutely legendary chaos in pet form!"
            ),
            "captions": [
                {"text": f"Oh wow, look at this {animal}!", "start": 0.0, "end": 2.5},
                {"text": "More drama than a reality TV show.", "start": 2.5, "end": 5.5},
                {"text": "Absolutely legendary chaos in pet form!", "start": 5.5, "end": 9.0},
            ],
            "image_prompt": image_prompt,
        }

    @staticmethod
    def _validate_script_data(data: Dict[str, Any], topic: str) -> None:
        """Ensure required keys are present; fill defaults if missing."""
        if "script" not in data or not data["script"]:
            data["script"] = f"Funny roast about {topic}."
        if "captions" not in data or not isinstance(data["captions"], list) or not data["captions"]:
            data["captions"] = [{"text": data["script"], "start": 0.0, "end": 9.0}]
        if "image_prompt" not in data or not data["image_prompt"]:
            data["image_prompt"] = (
                f"A funny photorealistic pet, comedic expression, cinematic lighting, "
                f"4K, high detail, related to: {topic}."
            )
