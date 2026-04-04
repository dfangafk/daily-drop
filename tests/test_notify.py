"""Tests for feedcurator.notify — email building and SMTP sending."""

import datetime
import smtplib

import pytest

import feedcurator.notify as notify_module
from feedcurator.models import RankResult
from feedcurator.notify import build_template_context, send_notification


def test_send_notification_skips_when_no_credentials(mocker, sample_items):
    mocker.patch.object(notify_module.settings, "sender_gmail", "")
    mocker.patch.object(notify_module.settings, "gmail_app_password", "")
    mocker.patch.object(notify_module.settings, "receiver_email", "")
    mock_smtp = mocker.patch("feedcurator.notify.smtplib.SMTP_SSL")

    t0 = datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC)
    send_notification(t0, sample_items, None)

    mock_smtp.assert_not_called()


def test_send_notification_calls_smtp(mocker, sample_items):
    mocker.patch.object(notify_module.settings, "sender_gmail", "test@gmail.com")
    mocker.patch.object(notify_module.settings, "gmail_app_password", "app-pass")
    mocker.patch.object(notify_module.settings, "receiver_email", "recv@example.com")
    mock_smtp_instance = mocker.MagicMock()
    mocker.patch("feedcurator.notify.smtplib.SMTP_SSL", return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__ = mocker.Mock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = mocker.Mock(return_value=False)
    mocker.patch("feedcurator.notify.render_text", return_value="plain text")
    mocker.patch("feedcurator.notify.render_html", return_value="<html></html>")
    mocker.patch("feedcurator.notify.build_template_context", return_value={})

    t0 = datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC)
    send_notification(t0, sample_items, None)

    mock_smtp_instance.login.assert_called_once_with("test@gmail.com", "app-pass")
    mock_smtp_instance.send_message.assert_called_once()


def test_send_notification_subject_contains_date_and_count(mocker, sample_items):
    mocker.patch.object(notify_module.settings, "sender_gmail", "test@gmail.com")
    mocker.patch.object(notify_module.settings, "gmail_app_password", "app-pass")
    mocker.patch.object(notify_module.settings, "receiver_email", "recv@example.com")
    mock_smtp_instance = mocker.MagicMock()
    mocker.patch("feedcurator.notify.smtplib.SMTP_SSL", return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__ = mocker.Mock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = mocker.Mock(return_value=False)
    mocker.patch("feedcurator.notify.render_text", return_value="plain")
    mocker.patch("feedcurator.notify.render_html", return_value="<html></html>")

    t0 = datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC)
    send_notification(t0, sample_items, None)

    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert "2026-04-01" in sent_msg["Subject"]
    assert str(len(sample_items)) in sent_msg["Subject"]


def test_build_template_context_no_rank_result(sample_items):
    ctx = build_template_context("2026-04-01", sample_items, None)

    assert ctx["date"] == "2026-04-01"
    assert "all_items" in ctx
    assert ctx["picks"] == []
    assert ctx["summary"] == ""


def test_build_template_context_with_rank_result(sample_items):
    rank = RankResult(
        picks=[sample_items[0].id],
        rationale={sample_items[0].id: "Great AI article."},
        summary="Today's top pick is about AI.",
    )
    ctx = build_template_context("2026-04-01", sample_items, rank)

    assert ctx["summary"] == "Today's top pick is about AI."
    assert len(ctx["picks"]) == 1
    assert ctx["picks"][0]["rationale"] == "Great AI article."


def test_rendered_text_contains_urls(mocker, sample_items):
    mocker.patch("feedcurator.notify.settings.paths.templates_dir", __import__("pathlib").Path(
        __import__("feedcurator.config", fromlist=["BASE_DIR"]).BASE_DIR
    ) / "feedcurator" / "templates")
    ctx = build_template_context("2026-04-01", sample_items, None)
    from feedcurator.notify import render_text
    text = render_text(ctx)
    assert "https://example.com/a" in text
