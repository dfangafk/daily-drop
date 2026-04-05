"""Normalize raw feed data into canonical Item field values."""

import datetime
import html
import logging
import re
from zoneinfo import ZoneInfo

from dailydrop.config import settings
from dailydrop.models import Item

logger = logging.getLogger(__name__)


def _normalize_description(raw: str, max_chars: int = 300) -> str:
    """Strip HTML tags, unescape entities, collapse whitespace, and truncate.

    Args:
        raw: Raw description string, potentially containing HTML markup.
        max_chars: Maximum number of characters to keep.  Truncation breaks on
            a word boundary and appends ``…``.

    Returns:
        Plain-text description, at most ``max_chars`` characters long.
    """
    text = re.sub(r"<[^>]+>", "", raw)
    text = html.unescape(text)
    text = " ".join(text.split())
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "…"
    return text


def _normalize_published_at(
    dt: datetime.datetime | None,
) -> datetime.datetime | None:
    """Convert a UTC datetime to the configured notification timezone.

    Args:
        dt: Timezone-aware UTC datetime, or ``None``.

    Returns:
        The same instant expressed in ``settings.notify.timezone``, or ``None``
        if ``dt`` is ``None``.
    """
    if dt is None:
        return None
    return dt.astimezone(ZoneInfo(settings.notify.timezone))


def normalize_items(items: list[Item]) -> list[Item]:
    """Normalize items in-place: clean descriptions and convert timestamps to
    configured timezone.

    Args:
        items: Items to normalize.

    Returns:
        The same list with fields normalized.
    """
    for item in items:
        item.description = _normalize_description(item.description)
        item.published_at = _normalize_published_at(item.published_at)
    return items
