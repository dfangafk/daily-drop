"""Tests for dailydrop.config — settings loading and env var overrides."""

from dailydrop.config import Settings


def test_settings_notify_defaults():
    s = Settings()
    assert s.notify.smtp_host == "smtp.gmail.com"
    assert s.notify.smtp_port == 465
    assert s.notify.timezone == "America/New_York"


def test_settings_pipeline_defaults():
    s = Settings()
    assert s.pipeline.log_level == "INFO"


def test_settings_paths_default_to_base_dir():
    s = Settings()
    assert s.paths.sources_yaml.name == "sources.yaml"
    assert s.paths.templates_dir.name == "templates"


def test_settings_secrets_default_empty(monkeypatch):
    monkeypatch.delenv("SENDER_GMAIL", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    monkeypatch.delenv("RECEIVER_EMAIL", raising=False)
    s = Settings(_env_file=None)
    assert s.sender_gmail == ""
    assert s.gmail_app_password == ""
    assert s.receiver_email == ""


def test_notify_smtp_port_override_via_env(monkeypatch):
    monkeypatch.setenv("NOTIFY__SMTP_PORT", "587")
    s = Settings()
    assert s.notify.smtp_port == 587


def test_pipeline_log_level_override_via_env(monkeypatch):
    monkeypatch.setenv("PIPELINE__LOG_LEVEL", "DEBUG")
    s = Settings()
    assert s.pipeline.log_level == "DEBUG"


def test_sender_gmail_override_via_env(monkeypatch):
    monkeypatch.setenv("SENDER_GMAIL", "test@gmail.com")
    s = Settings()
    assert s.sender_gmail == "test@gmail.com"
