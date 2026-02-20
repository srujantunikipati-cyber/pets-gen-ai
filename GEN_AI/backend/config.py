import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Pet Roast AI"
    
    # AI Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    FAL_KEY: str = os.getenv("FAL_KEY", "")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Paths
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "storage")
    TEMP_DIR: str = os.path.join(STORAGE_DIR, "temp")
    OUTPUT_DIR: str = os.path.join(STORAGE_DIR, "output")

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
