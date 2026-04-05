"""Configuration constants and settings loader for dailydrop."""

import logging
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# --- Directory paths ---

BASE_DIR = Path(__file__).resolve().parent.parent  # repo root

# --- Settings models ---


class NotifySettings(BaseModel):
    """Email notification configuration."""

    timezone: str = "America/New_York"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    subject_template: str = "dailydrop — {date} ({count} new items)"


class PipelineSettings(BaseModel):
    """Pipeline run configuration."""

    log_level: str = "INFO"
    save_logs: bool = True


class PathSettings(BaseModel):
    """Filesystem paths for the pipeline."""

    sources_yaml: Path = BASE_DIR / "config" / "sources.yaml"
    logs_output_dir: Path = BASE_DIR / "data" / "logs"
    templates_dir: Path = BASE_DIR / "dailydrop" / "templates"


class Settings(BaseSettings):
    """All tunable settings for dailydrop, loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    notify: NotifySettings = NotifySettings()
    pipeline: PipelineSettings = PipelineSettings()
    paths: PathSettings = PathSettings()

    # Secrets from .env
    sender_gmail: str = ""
    gmail_app_password: str = ""
    receiver_email: str = ""


settings = Settings()

if settings.sender_gmail and not settings.sender_gmail.endswith("@gmail.com"):
    logger.warning(
        "sender_gmail=%r does not end with @gmail.com; SMTP login will likely fail",
        settings.sender_gmail,
    )
