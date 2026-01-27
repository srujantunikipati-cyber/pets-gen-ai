"""Pydantic schemas for FastAPI request and response payloads."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.services.job_store import JobStatus

SUPPORTED_LANGUAGES = {"hi", "te", "ta", "ml", "bn", "gu", "mr", "pa", "en"}


class TranslateTextRequest(BaseModel):
    """Payload for submitting text to the AI4Bharat translation endpoint."""

    text: str = Field(..., min_length=1, max_length=5000)
    source_lang: str = Field(..., description="ISO 639-1 code such as hi, te, ta, en.")
    target_lang: str = Field(
        default="en",
        description="Target language for translation; defaults to English.",
    )
    task: str = Field(
        default="translation",
        description="Inference mode, e.g. translation or sentiment-analysis.",
        max_length=64,
    )

    @field_validator("source_lang")
    def validate_source_language(cls, value: str) -> str:
        if value.lower() not in SUPPORTED_LANGUAGES:
            raise ValueError("Unsupported source language code.")
        return value.lower()

    @field_validator("target_lang")
    def validate_target_language(cls, value: str) -> str:
        return value.lower()


class TranslateTextResponse(BaseModel):
    """Response from the AI4Bharat translation endpoint."""

    translated_text: str
    source_language: str
    target_language: str
    task: str
    provider_metadata: Optional[Dict[str, Any]] = None


class GenerateVideoRequest(BaseModel):
    """Request body for submitting a new video generation job.
    
    Supports two modes:
    1. Text + Image: Provide text and image_url/image_data
    2. Video Input: Provide video_data or video_url (audio will be extracted and converted to text)
    """

    # Text input (optional if video is provided)
    text: Optional[str] = Field(None, min_length=1, max_length=5000)
    
    # Image input (optional if video is provided)
    image_url: Optional[str] = None  # Changed from HttpUrl to str to accept data URLs
    image_data: Optional[str] = Field(None, description="Base64 encoded image data (data:image/...;base64,...)")
    
    # Video input (new - for audio extraction and STT)
    video_url: Optional[str] = Field(None, description="URL to video file")
    video_data: Optional[str] = Field(None, description="Base64 encoded video data (data:video/...;base64,...)")
    
    @field_validator("image_data", "video_data", mode="before")
    @classmethod
    def validate_data(cls, v):
        """Validate data fields."""
        return v
    
    def model_post_init(self, __context):
        """Ensure either (text + image) or video is provided."""
        has_text = bool(self.text)
        has_image = bool(self.image_url or self.image_data)
        has_video = bool(self.video_url or self.video_data)
        
        # Mode 1: Text + Image
        if has_text and has_image:
            return  # Valid
        
        # Mode 2: Video input (will extract audio and convert to text)
        if has_video:
            return  # Valid
        
        # Invalid: missing required inputs
        raise ValueError(
            "Either provide (text + image_url/image_data) OR (video_url/video_data). "
            "For video input, audio will be extracted and converted to text automatically."
        )


class GenerateVideoResponse(BaseModel):
    """Response payload containing the queued job identifier."""

    job_id: str
    status: JobStatus


class VideoStatusResponse(BaseModel):
    """Represents the status of an asynchronous video job."""

    job_id: str
    status: JobStatus
    detail: Optional[str] = None
    updated_at: Optional[datetime] = None


class VideoResultResponse(BaseModel):
    """Contains the final video result location, if available."""

    job_id: str
    status: JobStatus
    video_url: Optional[str] = None
    detail: Optional[str] = None


class BanubaFilter(BaseModel):
    """Represents a Banuba AR filter exposed to the client."""

    id: str
    name: str
    description: str


class BanubaFiltersResponse(BaseModel):
    """Collection of Banuba filter descriptors."""

    filters: List[BanubaFilter]


class RevidWebhookEvent(BaseModel):
    """Incoming webhook payload from fal.ai (kept name for backwards compatibility)."""

    job_id: str
    status: JobStatus
    video_url: Optional[str] = None
    detail: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
