"""Configuration constants and settings loader for dailydrop."""

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# --- Directory paths ---

BASE_DIR = Path(__file__).resolve().parent.parent  # repo root

# --- Settings models ---


class FetchSettings(BaseModel):
    """HTTP fetch configuration."""

    timeout: int = 30
    user_agent: str = "dailydrop/0.1 (RSS curation pipeline)"


class NotifySettings(BaseModel):
    """Email notification configuration."""

    timezone: str = "America/Los_Angeles"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    subject_template: str = "dailydrop — {date} ({count} new items)"


class LLMSettings(BaseModel):
    """LLM provider and model configuration."""

    provider: str = "auto"
    models: list[str] = ["gemini/gemini-2.5-flash"]
    api_kwargs: dict[str, Any] = {"num_retries": 3}
    top_n: int = 5


class PipelineSettings(BaseModel):
    """Pipeline run configuration."""

    log_level: str = "INFO"
    save_logs: bool = True
    enable_llm: bool = True
    enable_notify: bool = True
    enable_archive: bool = True


class RankSettings(BaseModel):
    """LLM ranking prompt configuration."""

    prompt_template: str = """
You are a content curator helping a reader stay on top of the most relevant new content.

The reader's interests:
{interests}

New items published today ({n} total):
{items_text}

Select the top {top_n} items most likely to interest this reader. Rank them best-first.

Respond with valid JSON only, no markdown:
{{"summary": "<2-3 sentence overview of today's picks>", "picks": [{{"id": "<item id>", "rationale": "<one sentence why this fits the reader's interests>"}}]}}
"""


class PathSettings(BaseModel):
    """Filesystem paths for the pipeline."""

    sources_yaml: Path = BASE_DIR / "config" / "sources.yaml"
    interests_txt: Path = BASE_DIR / "config" / "interests.txt"
    seen_json: Path = BASE_DIR / "data" / "seen.json"
    archive_html: Path = BASE_DIR / "docs" / "archive.html"
    logs_output_dir: Path = BASE_DIR / "data" / "logs"
    templates_dir: Path = BASE_DIR / "dailydrop" / "templates"


class Settings(BaseSettings):
    """All tunable settings for dailydrop, loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    fetch: FetchSettings = FetchSettings()
    notify: NotifySettings = NotifySettings()
    pipeline: PipelineSettings = PipelineSettings()
    llm: LLMSettings = LLMSettings()
    rank: RankSettings = RankSettings()
    paths: PathSettings = PathSettings()

    # Secrets from .env
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    sender_gmail: str = ""
    gmail_app_password: str = ""
    receiver_email: str = ""


settings = Settings()

if settings.sender_gmail and not settings.sender_gmail.endswith("@gmail.com"):
    logger.warning(
        "sender_gmail=%r does not end with @gmail.com; SMTP login will likely fail",
        settings.sender_gmail,
    )
