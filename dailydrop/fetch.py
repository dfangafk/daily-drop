"""Fetch new items from all configured RSS sources."""

import datetime
import logging
from pathlib import Path

import feedparser
import yaml

from dailydrop.config import settings
from dailydrop.models import Item

logger = logging.getLogger(__name__)


def load_sources(path: Path | None = None) -> list[dict]:
    """Load and return the list of source dicts from sources.yaml.

    Args:
        path: Override path to ``sources.yaml``.  Defaults to
            ``settings.paths.sources_yaml``.

    Returns:
        List of raw source dicts, each with ``name``, ``type``, ``url``,
        and ``category`` keys.
    """
    resolved = path or settings.paths.sources_yaml
    with open(resolved) as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


def _parse_entry(entry: feedparser.FeedParserDict) -> Item:
    """Convert a single feedparser entry to an ``Item``.

    Derives a stable ``id`` from ``entry.id`` if present, otherwise from
    ``entry.link``.  Parses ``published_parsed`` for the timestamp.

    Args:
        entry: A feedparser entry dict.

    Returns:
        A populated ``Item`` dataclass.
    """
    ts = entry.get("published_parsed")
    return Item(
        id=entry.get("id") or entry.get("link", ""),
        title=entry.get("title", ""),
        url=entry.get("link", ""),
        published_at=datetime.datetime(*ts[:6], tzinfo=datetime.timezone.utc) if ts else None,
        description=entry.get("summary", ""),
    )


def fetch_feed(url: str) -> list[Item]:
    """Fetch a single RSS/Atom feed and return a list of Items.

    Never raises — on parse failure, logs a warning and returns an empty list.

    Args:
        url: URL of the RSS/Atom feed.

    Returns:
        List of ``Item`` objects parsed from the feed.
    """
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            raise feed.bozo_exception
        return [_parse_entry(entry) for entry in feed.entries]
    except Exception as exc:
        logger.warning("Failed to fetch feed %r: %s", url, exc)
        return []


def filter_recent(
    items: list[Item],
    hours: int = 24,
    reference_time: datetime.datetime | None = None,
) -> list[Item]:
    """Return only items published within the last ``hours`` hours.

    Items with no ``published_at`` are excluded.

    Args:
        items: List of ``Item`` objects to filter.
        hours: Lookback window in hours.  Defaults to 24.
        reference_time: Reference time for the cutoff.  Defaults to the current UTC time.

    Returns:
        Filtered list of ``Item`` objects.
    """
    if reference_time is None:
        reference_time =datetime.datetime.now(tz=datetime.timezone.utc)
    cutoff = reference_time - datetime.timedelta(hours=hours)
    return [item for item in items if item.published_at is not None and item.published_at >= cutoff]


def fetch_all_sources(urls: list[str] | None = None) -> list[Item]:
    """Fetch all configured sources and return the combined item list.

    Args:
        urls: Override list of feed URLs.  Defaults to URLs from ``load_sources()``.

    Returns:
        Flat list of ``Item`` objects from all sources, sorted by
        ``published_at`` descending (newest first, ``None`` dates last).
    """
    if urls is None:
        urls = [s["url"] for s in load_sources()]
    items = []
    for url in urls:
        items.extend(fetch_feed(url))
    items.sort(key=lambda item: item.published_at or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
    return items



