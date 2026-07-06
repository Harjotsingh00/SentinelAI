"""
config.py

Centralized application configuration for SentinelAI backend.
Loads values from environment variables / .env file using pydantic-settings.
"""

import os

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings, loaded once and cached."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Server ---
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # --- Google Gemini ---
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # --- NVIDIA NIM ---
    NVIDIA_API_KEY: str = ""
    NVIDIA_NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_NIM_MODEL: str = "meta/llama-3.1-70b-instruct"

    # --- Weather ---
    OPENWEATHER_API_KEY: str = ""

    @property
    def cors_origins(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton pattern) and make sure
    downstream libraries that read directly from os.environ (google-genai,
    litellm) can see the same values."""
    settings = Settings()

    if settings.GOOGLE_API_KEY:
        os.environ.setdefault("GOOGLE_API_KEY", settings.GOOGLE_API_KEY)
        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

    if settings.NVIDIA_API_KEY:
        os.environ.setdefault("NVIDIA_API_KEY", settings.NVIDIA_API_KEY)

    return settings
