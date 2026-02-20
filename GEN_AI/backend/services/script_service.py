import google.generativeai as genai
import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ScriptService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. Script generation will fail.")
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_script(self, topic: str) -> Dict[str, Any]:
        """
        Generates a funny roast script based on the topic.
        Returns JSON: { "script": str, "captions": list, "image_prompt": str }
        """
        prompt = f"""
        You are a funny roast comedian. Write a short, hilarious roast script about: "{topic}".
        
        Constraints:
        1. Duration: Exactly 10-15 seconds when spoken.
        2. Tone: Funny, roasting, but friendly.
        3. Format: Return ONLY valid JSON.
        
        JSON Structure:
        {{
            "script": "The full text of the roast.",
            "captions": [
                {{"text": "First sentence", "start": 0.0, "end": 2.0}},
                {{"text": "Second sentence", "start": 2.0, "end": 4.5}}
            ],
            "image_prompt": "A detailed image generation prompt for a funny visual related to the roast."
        }}
        """
        
        if not self.api_key:
            logger.info("No GEMINI_API_KEY, returning mock script.")
            return {
                "script": f"Wow, {topic}. That's hilarious.",
                "captions": [
                    {"text": f"Wow, {topic}.", "start": 0.0, "end": 1.5},
                    {"text": "That's hilarious.", "start": 1.5, "end": 3.0}
                ],
                "image_prompt": f"A funny high quality photo of a pet doing {topic}"
            }
        
        try:
            response = self.model.generate_content(prompt)
            # Clean up potential markdown code blocks
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            raise
