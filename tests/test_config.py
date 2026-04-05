"""Tests for dailydrop.config — settings loading and env var overrides."""

import pytest

import dailydrop.config as cfg
from dailydrop.config import Settings


def test_settings_fetch_defaults():
    s = Settings()
    assert s.fetch.timeout == 30
    assert "dailydrop" in s.fetch.user_agent


def test_settings_notify_defaults():
    s = Settings()
    assert s.notify.smtp_host == "smtp.gmail.com"
    assert s.notify.smtp_port == 465
    assert "{date}" in s.notify.subject_template
    assert "{count}" in s.notify.subject_template


def test_settings_llm_defaults():
    s = Settings()
    assert s.llm.provider == "auto"
    assert isinstance(s.llm.models, list)
    assert len(s.llm.models) > 0
    assert s.llm.top_n == 5


def test_settings_pipeline_defaults():
    s = Settings()
    assert s.pipeline.enable_llm is True
    assert s.pipeline.enable_notify is True
    assert s.pipeline.save_logs is True


def test_settings_secrets_default_empty():
    s = Settings()
    assert s.gemini_api_key == ""
    assert s.sender_gmail == ""
    assert s.receiver_email == ""


def test_pipeline_override_via_env(monkeypatch):
    monkeypatch.setenv("PIPELINE__ENABLE_LLM", "false")
    s = Settings()
    assert s.pipeline.enable_llm is False


def test_llm_provider_override_via_env(monkeypatch):
    monkeypatch.setenv("LLM__PROVIDER", "api")
    s = Settings()
    assert s.llm.provider == "api"


def test_llm_top_n_override_via_env(monkeypatch):
    monkeypatch.setenv("LLM__TOP_N", "10")
    s = Settings()
    assert s.llm.top_n == 10


def test_fetch_timeout_override_via_env(monkeypatch):
    monkeypatch.setenv("FETCH__TIMEOUT", "60")
    s = Settings()
    assert s.fetch.timeout == 60


def test_notify_smtp_port_override_via_env(monkeypatch):
    monkeypatch.setenv("NOTIFY__SMTP_PORT", "587")
    s = Settings()
    assert s.notify.smtp_port == 587


def test_gemini_api_key_override_via_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    s = Settings()
    assert s.gemini_api_key == "test-key-123"


def test_paths_default_to_base_dir():
    s = Settings()
    assert s.paths.sources_yaml.name == "sources.yaml"
    assert s.paths.interests_txt.name == "interests.txt"
    assert s.paths.seen_json.name == "seen.json"
