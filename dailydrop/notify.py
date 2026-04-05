"""Email notification: send daily digest after pipeline completes."""

import datetime
import functools
import logging
import smtplib
import ssl
from collections.abc import Callable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader

from dailydrop.config import settings
from dailydrop.models import Item

NotifyFn = Callable[[datetime.datetime, list[Item], "dict | None"], None]

logger = logging.getLogger(__name__)


def _to_display_time(dt: datetime.datetime | None) -> str:
    """Format a UTC-aware datetime for display in the configured timezone.

    Returns an empty string if ``dt`` is ``None``.
    """
    if dt is None:
        return ""
    tz = ZoneInfo(settings.notify.timezone)
    local = dt.astimezone(tz)
    return f"{local.strftime('%b')} {local.day}, {local.year}, {local.hour % 12 or 12}:{local.strftime('%M')} {'AM' if local.hour < 12 else 'PM'}"


@functools.lru_cache(maxsize=2)
def _get_jinja_env(templates_dir: str, autoescape: bool) -> Environment:
    """Return a cached Jinja2 Environment for the given directory."""
    return Environment(loader=FileSystemLoader(templates_dir), autoescape=autoescape)


def send_notification(
    reference_time: datetime.datetime,
    new_items: list[Item],
    rank_result: dict | None,
) -> None:
    """Send daily digest email after pipeline completion.

    Skips silently if SENDER_GMAIL, GMAIL_APP_PASSWORD, or RECEIVER_EMAIL are
    not set.  Catches and logs all exceptions to avoid failing the pipeline.

    Args:
        reference_time: UTC timestamp of the pipeline run.
        new_items: All new (deduplicated) items fetched this run.
        rank_result: LLM-ranked picks, or ``None`` if ranking was skipped.
    """
    if not (settings.sender_gmail and settings.gmail_app_password and settings.receiver_email):
        logger.info("Email notification skipped (credentials not set)")
        return

    tz = ZoneInfo(settings.notify.timezone)
    date_str = reference_time.astimezone(tz).date().isoformat()
    item_count = len(new_items)

    subject = settings.notify.subject_template.format(date=date_str, count=item_count)
    ctx = build_template_context(date_str, new_items, rank_result)
    text_body = render_text(ctx)
    html_body = render_html(ctx)

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.sender_gmail
    msg["To"] = settings.receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.notify.smtp_host, settings.notify.smtp_port, context=context) as server:
            server.login(settings.sender_gmail, settings.gmail_app_password)
            server.send_message(msg)
        _email = settings.receiver_email
        _masked = _email[:2] + "***" + _email[_email.index("@"):]
        logger.info("Notification email sent to %s", _masked)
    except Exception:
        logger.warning("Failed to send notification email", exc_info=True)


def build_template_context(
    date_str: str,
    new_items: list[Item],
    rank_result: dict | None,
) -> dict:
    """Assemble the context dict passed to both Jinja2 email templates.

    Args:
        date_str: ISO date string for the run (display purposes).
        new_items: All new items fetched this run.
        rank_result: LLM-ranked picks, or ``None``.

    Returns:
        Context dict with ``date``, ``picks``, ``all_items``, and ``summary``.
    """
    ...


def render_text(ctx: dict) -> str:
    """Render the plain-text email template with the given context."""
    env = _get_jinja_env(str(settings.paths.templates_dir), autoescape=False)
    return env.get_template("digest.txt.jinja2").render(**ctx)


def render_html(ctx: dict) -> str:
    """Render the HTML email template with the given context."""
    env = _get_jinja_env(str(settings.paths.templates_dir), autoescape=True)
    return env.get_template("digest.html.jinja2").render(**ctx)
