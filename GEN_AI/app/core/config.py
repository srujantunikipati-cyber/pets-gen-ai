"""Application settings and configuration helpers."""

from functools import lru_cache
from typing import List, Optional
import json
import os

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BanubaFilterConfig(BaseModel):
    """Represents a Banuba AR filter entry exposed to clients."""

    id: str
    name: str
    description: str


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # IndicTrans2 inference server configuration
    ai4bharat_base_url: str = "http://localhost:5000"
    ai4bharat_translate_path: str = "/translate"
    ai4bharat_api_key: Optional[str] = None

    # pets-backend GraphQL server configuration
    pets_backend_url: str = "http://localhost:4000"  # GraphQL server URL
    pets_backend_enabled: bool = False  # Enable/disable pets-backend integration

    # fal.ai API configuration for video generation
    fal_api_key: str = Field(default=...)
    fal_base_url: str = "https://queue.fal.run"  # fal.ai queue endpoint
    fal_model_id: str = "fal-ai/minimax-video"
    fal_webhook_secret: Optional[str] = None

    banuba_filters: List[BanubaFilterConfig] = Field(
        default_factory=lambda: [
            BanubaFilterConfig(
                id="desi-fire",
                name="Desi Fire",
                description="Adds spicy overlays and glow effects for dramatic roasts.",
            ),
            BanubaFilterConfig(
                id="pet-maharaja",
                name="Pet Maharaja",
                description="Turns pets into regal royalty with ornate accessories.",
            ),
            BanubaFilterConfig(
                id="bollywood-burn",
                name="Bollywood Burn",
                description="Provides cinematic lighting and spark particles.",
            ),
        ]
    )

    request_timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.5
    # Video storage configuration
    video_storage_path: str = "storage/videos"  # Local directory for storing videos


    # Redis configuration for persistent job storage
    redis_url: str = "redis://localhost:6379/0"
    use_redis: bool = True
    redis_job_ttl_seconds: int = 86400 * 7  # 7 days

    # Backend webhook configuration (for notifying Railway backend)
    backend_webhook_url: Optional[str] = None  # Set to your Railway backend URL

    # CORS origins (add your Railway backend URL)
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"]  # In production, specify exact origins
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    @model_validator(mode="before")
    @classmethod
    def remove_invalid_cors_origins(cls, data):
        """Remove invalid CORS_ORIGINS from environment before parsing."""
        if isinstance(data, dict) and "CORS_ORIGINS" in data:
            cors_val = data["CORS_ORIGINS"]
            # Remove if it's an invalid format
            if isinstance(cors_val, str) and cors_val in ["[*]", "[*", "*]", "*"]:
                data.pop("CORS_ORIGINS", None)
        # Also remove from os.environ if it exists and is invalid
        if "CORS_ORIGINS" in os.environ:
            cors_val = os.environ["CORS_ORIGINS"]
            if cors_val in ["[*]", "[*", "*]", "*"]:
                os.environ.pop("CORS_ORIGINS", None)
        return data


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance for dependency injection."""
    # Clear cache if environment variables changed (for development)
    # In production, this cache improves performance
    return Settings()

def clear_settings_cache():
    """Clear the settings cache (useful for testing/reloading)."""
    get_settings.cache_clear()