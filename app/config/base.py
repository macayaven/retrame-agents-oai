"""Configuration settings for re-frame backend."""

import base64
import logging
import sys
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    _instance: "Settings | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "Settings":
        if cls._instance is None:
            try:
                cls._instance = super().__new__(cls)
            except Exception as e:
                logger.error(f"ERROR: Failed to load required environment variables: {e}")
                logger.error("\nRequired environment variables:")
                logger.error("  - GOOGLE_API_KEY")
                logger.error("  - LANGFUSE_HOST")
                logger.error("  - LANGFUSE_PUBLIC_KEY")
                logger.error("  - LANGFUSE_SECRET_KEY")
                logger.error("\nOptional environment variables:")
                logger.error("  - SUPABASE_REFRAME_DB_CONNECTION_STRING")
                logger.error("  - ARIZE_SPACE_ID")
                logger.error("  - ARIZE_API_KEY")
                sys.exit(1)
        return cls._instance

    # App Configuration
    app_name: str = "reframe_assistant"

    # API Configuration
    api_title: str = "re-frame agentic woriflow"
    api_version: str = "0.1.0"
    api_description: str = "AI-assisted cognitive reframing support tool for AvPD"

    # Google AI Configuration (REQUIRED)
    google_ai_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_ai_model: str = "gemini-2.0-flash-lite"
    google_ai_temperature: float = 0.7
    google_ai_max_tokens: int = 1024

    # GCS Artifact Storage Configuration (OPTIONAL)
    gcs_bucket_name: str = Field(default="re-frame", alias="GCS_BUCKET_NAME")
    gcs_project_id: str = Field(default="", alias="GOOGLE_API_KEY")

    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "https://re-frame.social"]

    # Rate Limiting
    rate_limit_requests: int = 10
    rate_limit_period: int = 3600  # 1 hour in seconds

    # Logging
    log_level: str = "INFO"

    # Security & Abuse Prevention
    content_filter_threshold: float = 2.8
    perspective_api_key: str | None = Field(default=None, alias="PERSPECTIVE_API_KEY")
    toxicity_threshold: float = 0.7
    enable_perspective_api: bool = False

    # Supabase Configuration (OPTIONAL)
    supabase_connection_string: str | None = Field(
        default=None, alias="SUPABASE_REFRAME_DB_CONNECTION_STRING"
    )

    # Langfuse Configuration (REQUIRED)
    langfuse_host: str = Field(default="", alias="LANGFUSE_HOST")
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")

    # Arize AX Configuration (OPTIONAL)
    arize_space_id: str | None = Field(default=None, alias="ARIZE_SPACE_ID")
    arize_api_key: str | None = Field(default=None, alias="ARIZE_API_KEY")

    @property
    def langfuse_bearer_token(self) -> str:
        """Generate a bearer token for Langfuse."""
        return base64.b64encode(
            f"{self.langfuse_public_key}:{self.langfuse_secret_key}".encode()
        ).decode()

    class Config:
        """Pydantic settings configuration."""

        case_sensitive = False
        populate_by_name = True
        # Removed: env_file = ".env"

    @field_validator(
        "google_ai_api_key", "langfuse_host", "langfuse_public_key", "langfuse_secret_key"
    )
    @classmethod
    def validate_required(cls, v: str, info: Any) -> str:
        """Ensure required fields are not empty."""
        if not v:
            field_name = info.field_name
            raise ValueError(f"{field_name} is required but not set in environment")
        return v
