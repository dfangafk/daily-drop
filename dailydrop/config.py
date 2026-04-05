"""Configuration constants and settings loader for dailydrop."""

from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Directory paths ---

BASE_DIR = Path(__file__).resolve().parent.parent  # repo root

# --- SMTP provider registry ---

# (host, port, use_ssl) — use_ssl=True means SMTP_SSL; False means SMTP + STARTTLS
SMTP_PROVIDERS: dict[str, tuple[str, int, bool]] = {
    "gmail":    ("smtp.gmail.com",          465, True),
    "outlook":  ("smtp-mail.outlook.com",   587, False),
    "yahoo":    ("smtp.mail.yahoo.com",     465, True),
    "icloud":   ("smtp.mail.me.com",        587, False),
    "fastmail": ("smtp.fastmail.com",       465, True),
}

DOMAIN_TO_PROVIDER: dict[str, str] = {
    "gmail.com":      "gmail",
    "googlemail.com": "gmail",
    "outlook.com":    "outlook",
    "hotmail.com":    "outlook",
    "live.com":       "outlook",
    "msn.com":        "outlook",
    "yahoo.com":      "yahoo",
    "yahoo.co.uk":    "yahoo",
    "ymail.com":      "yahoo",
    "icloud.com":     "icloud",
    "me.com":         "icloud",
    "mac.com":        "icloud",
    "fastmail.com":   "fastmail",
    "fastmail.fm":    "fastmail",
}

# --- Settings models ---


class NotifySettings(BaseModel):
    """Email notification configuration."""

    timezone: str = "America/New_York"
    smtp_host: str | None = None       # manual escape hatch
    smtp_port: int | None = None       # manual escape hatch
    smtp_use_ssl: bool | None = None   # True=SMTP_SSL (465), False=SMTP+STARTTLS (587); inferred from port if unset


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


def resolve_smtp(notify: NotifySettings, sender_email: str) -> tuple[str, int, bool]:
    """Return (host, port, use_ssl) for the given settings and sender address.

    Priority:
    1. Manual smtp_host + smtp_port override (both must be set).
    2. Auto-detection from the sender_email domain.
    """
    # 1. Full manual override
    if notify.smtp_host is not None and notify.smtp_port is not None:
        use_ssl = notify.smtp_use_ssl if notify.smtp_use_ssl is not None else notify.smtp_port == 465
        return notify.smtp_host, notify.smtp_port, use_ssl

    # 2. Auto-detect from domain
    if "@" in sender_email:
        domain = sender_email.split("@")[-1].lower()
        provider = DOMAIN_TO_PROVIDER.get(domain)
        if provider is not None:
            return SMTP_PROVIDERS[provider]

    raise ValueError(
        f"Cannot determine SMTP settings for {sender_email!r}. "
        "Set NOTIFY__SMTP_HOST and NOTIFY__SMTP_PORT, or use a recognised email domain."
    )


settings = Settings()
