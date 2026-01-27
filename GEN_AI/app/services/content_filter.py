"""Service for filtering abusive content using LLM."""

import logging
from typing import Dict, Any, Optional
from app.clients.ai4bharat import AI4BharatClient
from app.core.exceptions import AI4BharatAPIError

_logger = logging.getLogger(__name__)


class ContentFilterError(Exception):
    """Raised when content filtering fails."""


class ContentFilterService:
    """Service for filtering abusive words using LLM."""

    def __init__(self, ai4bharat_client: AI4BharatClient):
        """Initialize content filter service.
        
        Args:
            ai4bharat_client: AI4Bharat client for LLM operations
        """
        self.ai4bharat_client = ai4bharat_client

    async def filter_abusive_content(
        self, text: str, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Filter abusive words from text using LLM.
        
        Args:
            text: Input text to filter
            language: Language of the text (for better filtering)
            
        Returns:
            Dict with 'filtered_text', 'original_text', 'language', and 'has_abusive_content'
        """
        try:
            # Create a prompt for content filtering
            # We'll use AI4Bharat's translation/analysis capabilities
            # to identify and remove abusive content
            
            # First, try to detect if there's abusive content
            # We can use sentiment analysis or create a custom prompt
            
            # For now, we'll use a simple approach:
            # 1. Ask AI4Bharat to analyze the text
            # 2. If abusive content is detected, replace it with safe alternatives
            # 3. Otherwise, return the original text
            
            # Create filtering prompt
            filter_prompt = f"""Please analyze the following text and remove or replace any abusive, offensive, or inappropriate words while keeping the meaning and tone. Return only the cleaned text without any explanation.

Original text: {text}

Cleaned text:"""
            
            try:
                # Use AI4Bharat for text processing
                # We'll use translation task with a special prompt
                result = await self.ai4bharat_client.translate_text(
                    text=filter_prompt,
                    source_language=language or "auto",
                    target_language=language or "en",  # Keep same language
                    task="translation",
                )
                
                # Extract filtered text
                filtered_text = result.get("translated_text") or result.get("text") or text
                
                # Check if text was modified (indicating filtering occurred)
                has_abusive_content = filtered_text.lower() != text.lower()
                
                return {
                    "filtered_text": filtered_text.strip(),
                    "original_text": text,
                    "language": language or "auto",
                    "has_abusive_content": has_abusive_content,
                }
                
            except AI4BharatAPIError as e:
                _logger.warning(f"AI4Bharat filtering failed, using original text: {e}")
                # Fallback: return original text if filtering fails
                return {
                    "filtered_text": text,
                    "original_text": text,
                    "language": language or "auto",
                    "has_abusive_content": False,
                }
                
        except Exception as e:
            _logger.exception("Failed to filter content")
            # Fallback: return original text
            return {
                "filtered_text": text,
                "original_text": text,
                "language": language or "auto",
                "has_abusive_content": False,
            }

    async def simple_filter_abusive_content(
        self, text: str, language: Optional[str] = None
    ) -> str:
        """Simple version that just returns filtered text.
        
        Args:
            text: Input text to filter
            language: Language of the text
            
        Returns:
            Filtered text
        """
        result = await self.filter_abusive_content(text, language)
        return result["filtered_text"]


def get_content_filter_service(
    ai4bharat_client: AI4BharatClient
) -> ContentFilterService:
    """Get content filter service instance."""
    return ContentFilterService(ai4bharat_client)
