"""Tests for dailydrop.config — settings loading and env var overrides."""

import pytest

from dailydrop.config import NotifySettings, Settings, resolve_smtp


def test_settings_notify_defaults():
    s = Settings()
    assert s.notify.smtp_host is None
    assert s.notify.smtp_port is None
    assert s.notify.timezone == "America/New_York"


def test_settings_pipeline_defaults():
    s = Settings()
    assert s.pipeline.log_level == "INFO"


def test_settings_paths_default_to_base_dir():
    s = Settings()
    assert s.paths.sources_yaml.name == "sources.yaml"
    assert s.paths.templates_dir.name == "templates"


def test_settings_secrets_default_empty(monkeypatch):
    monkeypatch.delenv("SENDER_EMAIL", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("RECEIVER_EMAIL", raising=False)
    s = Settings(_env_file=None)
    assert s.sender_email == ""
    assert s.smtp_password == ""
    assert s.receiver_email == ""


def test_notify_smtp_port_override_via_env(monkeypatch):
    monkeypatch.setenv("NOTIFY__SMTP_PORT", "587")
    s = Settings()
    assert s.notify.smtp_port == 587


def test_pipeline_log_level_override_via_env(monkeypatch):
    monkeypatch.setenv("PIPELINE__LOG_LEVEL", "DEBUG")
    s = Settings()
    assert s.pipeline.log_level == "DEBUG"


def test_sender_email_override_via_env(monkeypatch):
    monkeypatch.setenv("SENDER_EMAIL", "test@gmail.com")
    s = Settings()
    assert s.sender_email == "test@gmail.com"


# --- resolve_smtp tests ---

def test_resolve_smtp_gmail_domain():
    notify = NotifySettings()
    host, port, smtp_security = resolve_smtp(notify, "user@gmail.com")
    assert host == "smtp.gmail.com"
    assert port == 465
    assert smtp_security == "ssl"


def test_resolve_smtp_googlemail_domain():
    notify = NotifySettings()
    host, port, smtp_security = resolve_smtp(notify, "user@googlemail.com")
    assert host == "smtp.gmail.com"


def test_resolve_smtp_outlook_domain():
    notify = NotifySettings()
    host, port, smtp_security = resolve_smtp(notify, "user@outlook.com")
    assert host == "smtp-mail.outlook.com"
    assert port == 587
    assert smtp_security == "starttls"


def test_resolve_smtp_hotmail_domain():
    notify = NotifySettings()
    host, port, smtp_security = resolve_smtp(notify, "user@hotmail.com")
    assert host == "smtp-mail.outlook.com"


def test_resolve_smtp_manual_host_port_override_non465():
    notify = NotifySettings(smtp_host="smtp.corp.example.com", smtp_port=2525)
    host, port, smtp_security = resolve_smtp(notify, "user@corp.example.com")
    assert host == "smtp.corp.example.com"
    assert port == 2525
    assert smtp_security == "starttls"


def test_resolve_smtp_manual_host_port_override_465():
    notify = NotifySettings(smtp_host="smtp.corp.example.com", smtp_port=465)
    host, port, smtp_security = resolve_smtp(notify, "user@corp.example.com")
    assert host == "smtp.corp.example.com"
    assert port == 465
    assert smtp_security == "ssl"


def test_resolve_smtp_unknown_domain_raises():
    notify = NotifySettings()
    with pytest.raises(ValueError, match="Cannot determine SMTP settings"):
        resolve_smtp(notify, "user@unknown-domain.example")


def test_resolve_smtp_no_email_raises():
    notify = NotifySettings()
    with pytest.raises(ValueError, match="Cannot determine SMTP settings"):
        resolve_smtp(notify, "")
