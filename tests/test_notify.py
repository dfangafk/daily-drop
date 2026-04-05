"""Tests for dailydrop.notify — email building and SMTP sending."""

import datetime
import smtplib

import pytest

import dailydrop.notify as notify_module
from dailydrop.notify import send_notification


def test_send_notification_skips_when_no_credentials(mocker, sample_items):
    mocker.patch.object(notify_module.settings, "sender_gmail", "")
    mocker.patch.object(notify_module.settings, "gmail_app_password", "")
    mocker.patch.object(notify_module.settings, "receiver_email", "")
    mock_smtp = mocker.patch("dailydrop.notify.smtplib.SMTP_SSL")

    t0 = datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC)
    send_notification(t0, sample_items, None)

    mock_smtp.assert_not_called()


def test_send_notification_calls_smtp(mocker, sample_items):
    mocker.patch.object(notify_module.settings, "sender_gmail", "test@gmail.com")
    mocker.patch.object(notify_module.settings, "gmail_app_password", "app-pass")
    mocker.patch.object(notify_module.settings, "receiver_email", "recv@example.com")
    mock_smtp_instance = mocker.MagicMock()
    mocker.patch("dailydrop.notify.smtplib.SMTP_SSL", return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__ = mocker.Mock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = mocker.Mock(return_value=False)
    mock_env = mocker.MagicMock()
    mock_env.get_template.return_value.render.return_value = ""
    mocker.patch("dailydrop.notify.Environment", return_value=mock_env)

    t0 = datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC)
    send_notification(t0, sample_items, None)

    mock_smtp_instance.login.assert_called_once_with("test@gmail.com", "app-pass")
    mock_smtp_instance.send_message.assert_called_once()


def test_send_notification_subject_contains_date_and_count(mocker, sample_items):
    mocker.patch.object(notify_module.settings, "sender_gmail", "test@gmail.com")
    mocker.patch.object(notify_module.settings, "gmail_app_password", "app-pass")
    mocker.patch.object(notify_module.settings, "receiver_email", "recv@example.com")
    mock_smtp_instance = mocker.MagicMock()
    mocker.patch("dailydrop.notify.smtplib.SMTP_SSL", return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__ = mocker.Mock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = mocker.Mock(return_value=False)
    mock_env = mocker.MagicMock()
    mock_env.get_template.return_value.render.return_value = ""
    mocker.patch("dailydrop.notify.Environment", return_value=mock_env)

    t0 = datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC)
    send_notification(t0, sample_items, None)

    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert "2026-04-01" in sent_msg["Subject"]
    assert str(len(sample_items)) in sent_msg["Subject"]
