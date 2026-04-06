"""Email notification: send daily digest after pipeline completes."""

import datetime
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader

from dailydrop.config import resolve_smtp, settings
from dailydrop.models import Item

def send_notification(
    reference_time: datetime.datetime,
    recent_items: list[Item],
) -> None:
    """Send daily digest email after pipeline completion.

    Raises RuntimeError if credentials are missing or delivery fails.
    Use --skip-email on the pipeline to opt out of email delivery entirely.

    Args:
        reference_time: UTC timestamp of the pipeline run.
        recent_items: Items from the last 24 hours fetched this run.
    """
    if not (
        settings.sender_email
        and settings.smtp_password
        and settings.receiver_email
    ):
        raise RuntimeError(
            "Email notification failed: SENDER_EMAIL, SMTP_PASSWORD, and "
            "RECEIVER_EMAIL must all be set. Use --skip-email to opt out."
        )

    tz = ZoneInfo(settings.notify.timezone)
    dt_local = reference_time.astimezone(tz)
    date_str = dt_local.date().isoformat()
    date_display = dt_local.strftime("%A, %B %-d")
    item_count = len(recent_items)

    ctx = {
        "date": date_display,
        "count": item_count,
        "all_finds": recent_items,
    }
    loader = FileSystemLoader(str(settings.paths.templates_dir))
    env = Environment(loader=loader, autoescape=False)
    subject = env.get_template("drop.subject.jinja2").render(
        date=date_str, count=item_count
    )
    text_body = env.get_template("drop.txt.jinja2").render(**ctx)
    html_body = (
        Environment(loader=loader, autoescape=True)
        .get_template("drop.html.jinja2")
        .render(**ctx)
    )

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.sender_email
    msg["To"] = settings.receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    smtp_host, smtp_port, smtp_security = resolve_smtp(
        settings.notify, settings.sender_email
    )
    context = ssl.create_default_context()
    if smtp_security == "ssl":
        conn = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
    else:
        conn = smtplib.SMTP(smtp_host, smtp_port)
        conn.starttls(context=context)
    with conn as server:
        server.login(settings.sender_email, settings.smtp_password)
        server.send_message(msg)
