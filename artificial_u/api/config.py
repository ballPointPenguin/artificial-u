from functools import lru_cache
from typing import List, Optional
from pydantic import AnyHttpUrl, Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    API configuration settings loaded from environment variables
    """

    # API settings
    api_prefix: str = "/api/v1"
    debug: bool = False

    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:8000", "http://localhost:3000"]
    )

    # Database settings
    DATABASE_URL: str

    # Logging settings
    LOG_LEVEL: str = "INFO"

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Storage paths
    AUDIO_STORAGE_PATH: str
    AUDIO_PATH: str = "audio"
    TEXT_EXPORT_PATH: str = "exports"

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


@lru_cache
def get_settings() -> Settings:
    """
    Creates settings only once then caches it
    """
    return Settings()
