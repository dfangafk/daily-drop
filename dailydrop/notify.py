"""Email notification: send daily digest after pipeline completes."""

import datetime
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader

from dailydrop.config import resolve_smtp, settings
from dailydrop.models import Item

logger = logging.getLogger(__name__)


def send_notification(
    reference_time: datetime.datetime,
    recent_items: list[Item],
) -> None:
    """Send daily digest email after pipeline completion.

    Skips silently if SENDER_GMAIL, GMAIL_APP_PASSWORD, or RECEIVER_EMAIL are
    not set.  Catches and logs all exceptions to avoid failing the pipeline.

    Args:
        reference_time: UTC timestamp of the pipeline run.
        recent_items: Items from the last 24 hours fetched this run.
    """
    if not (settings.sender_email and settings.smtp_password and settings.receiver_email):
        logger.info("Email notification skipped (credentials not set)")
        return

    tz = ZoneInfo(settings.notify.timezone)
    dt_local = reference_time.astimezone(tz)
    date_str = dt_local.date().isoformat()
    date_display = dt_local.strftime('%A, %B %-d')
    item_count = len(recent_items)

    ctx = {
        "date": date_display,
        "count": item_count,
        "all_finds": recent_items,
    }
    loader = FileSystemLoader(str(settings.paths.templates_dir))
    env = Environment(loader=loader, autoescape=False)
    subject = env.get_template("drop.subject.jinja2").render(date=date_str, count=item_count)
    text_body = env.get_template("drop.txt.jinja2").render(**ctx)
    html_body = Environment(loader=loader, autoescape=True).get_template("drop.html.jinja2").render(**ctx)

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.sender_email
    msg["To"] = settings.receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        smtp_host, smtp_port, use_ssl = resolve_smtp(settings.notify, settings.sender_email)
        context = ssl.create_default_context()
        if use_ssl:
            conn = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
        else:
            conn = smtplib.SMTP(smtp_host, smtp_port)
            conn.starttls(context=context)
        with conn as server:
            server.login(settings.sender_email, settings.smtp_password)
            server.send_message(msg)
        _email = settings.receiver_email
        _masked = _email[:2] + "***" + _email[_email.index("@"):]
        logger.info("Notification email sent to %s", _masked)
    except Exception:
        logger.warning("Failed to send notification email", exc_info=True)


