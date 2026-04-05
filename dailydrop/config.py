"""Configuration constants and settings loader for dailydrop."""

from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Directory paths ---

BASE_DIR = Path(__file__).resolve().parent.parent  # repo root

# --- Settings models ---


class NotifySettings(BaseModel):
    """Email notification configuration."""

    timezone: str = "America/New_York"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465


class PipelineSettings(BaseModel):
    """Pipeline run configuration."""

    log_level: str = "INFO"


class PathSettings(BaseModel):
    """Filesystem paths for the pipeline."""

    sources_yaml: Path = BASE_DIR / "sources.yaml"
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
    sender_email: str = ""
    smtp_password: str = ""
    receiver_email: str = ""


settings = Settings()
