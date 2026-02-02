"""Pydantic schemas for FastAPI request and response payloads."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

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
    2. Video Input: Provide video, video_url, or video_data (audio extracted and converted to text)
    
    Accepts common payload field names: video, videoUrl, video_url, videoData, video_data.
    """

    model_config = {"extra": "ignore"}  # Ignore unknown fields from backend

    # Text input (optional if video is provided)
    text: Optional[str] = Field(None, min_length=1, max_length=5000)
    
    # Image input (optional if video is provided)
    image_url: Optional[str] = Field(None, alias="imageUrl")
    image_data: Optional[str] = Field(None, description="Base64 image (data:image/...;base64,...)", alias="imageData")
    
    # Video input - accept multiple field names for backend compatibility
    video_url: Optional[str] = Field(None, description="URL to video file", alias="videoUrl")
    video_data: Optional[str] = Field(None, description="Base64 video (data:video/...;base64,...)", alias="videoData")
    video: Optional[str] = Field(None, description="Video URL or data (alias for video_url)")
    
    # Audio options
    audio_enabled: bool = Field(default=True, description="Enable audio generation")
    audio_voice: str = Field(default="en-US-Neural2-F", description="Voice ID: en-US-Neural2-F (female) or en-US-Neural2-D (male)")
    
    # pets-backend integration fields (optional)
    user_id: Optional[str] = Field(None, alias="userId")
    auth_token: Optional[str] = Field(None, alias="authToken")
    
    @field_validator("image_data", "video_data", "video", mode="before")
    @classmethod
    def validate_data(cls, v):
        """Validate data fields."""
        return v
    
    @model_validator(mode="after")
    def normalize_video_and_validate(self):
        """Map 'video' to video_url or video_data and ensure valid input."""
        if self.video and not (self.video_url or self.video_data):
            if self.video.startswith("http://") or self.video.startswith("https://"):
                object.__setattr__(self, "video_url", self.video)
            elif self.video.startswith("data:video/") or self.video.startswith("data:application/"):
                object.__setattr__(self, "video_data", self.video)
            else:
                object.__setattr__(self, "video_url", self.video)
        
        # Check what we have (ignore empty strings)
        has_text = bool(self.text and self.text.strip())
        has_image = bool((self.image_url and str(self.image_url).strip()) or 
                        (self.image_data and self.image_data.strip()))
        has_video = bool((self.video_url and str(self.video_url).strip()) or 
                        (self.video_data and self.video_data.strip()))
        
        # Valid combinations:
        # 1. Text + Image (for roast video generation)
        # 2. Video only (extract audio, STT, filter, generate)
        if has_text and has_image:
            return self
        if has_video:
            return self
        
        # Provide clear error messages for each case
        if has_text and not has_image:
            raise ValueError(
                "When providing 'text', you must also provide either 'imageUrl'/'imageData' or 'image_url'/'image_data'. "
                "Example: {\"text\": \"Roast this dog\", \"imageUrl\": \"https://example.com/dog.jpg\"}"
            )
        
        if has_image and not has_text:
            raise ValueError(
                "When providing an image, you must also provide 'text'. "
                "Example: {\"text\": \"Roast this cute pet\", \"imageUrl\": \"https://example.com/pet.jpg\"}"
            )
        
        raise ValueError(
            "Invalid input. Please provide one of the following:\n"
            "1. Text + Image: {\"text\": \"...\", \"imageUrl\": \"...\"} OR {\"text\": \"...\", \"imageData\": \"data:image/...\"}\n"
            "2. Video only: {\"videoUrl\": \"...\"} OR {\"videoData\": \"data:video/...\"} OR {\"video\": \"...\"}\n"
            "For video input, audio will be automatically extracted and converted to text."
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
