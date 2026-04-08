"""Fetch new items from all configured RSS sources."""

import datetime
import logging
import time
from pathlib import Path

import feedparser
import yaml

from dailydrop.config import settings
from dailydrop.models import Item

logger = logging.getLogger(__name__)

_FETCH_RETRIES = 3
_FETCH_RETRY_BASE_DELAY = 2  # seconds; doubles each attempt (2, 4)


def _load_sources(path: Path | None = None) -> list[dict]:
    """Load and return the list of source dicts from sources.yaml.

    Args:
        path: Override path to ``sources.yaml``.  Defaults to
            ``settings.paths.sources_yaml``.

    Returns:
        List of raw source dicts, each with ``name`` and ``url`` keys.
    """
    resolved = path or settings.paths.sources_yaml
    with open(resolved) as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


def _fetch_feed(url: str) -> list[Item]:
    """Fetch a single RSS/Atom feed and return a list of Items.

    Never raises — on parse failure, logs a warning and returns an empty list.
    Retries up to ``_FETCH_RETRIES`` times on transient errors.

    Args:
        url: URL of the RSS/Atom feed.

    Returns:
        List of ``Item`` objects parsed from the feed.
    """
    last_exc: Exception | None = None
    for attempt in range(1, _FETCH_RETRIES + 1):
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                raise feed.bozo_exception
            source_name = feed.feed.get("title", "")
            source_url = feed.feed.get("link", "")
            items = [
                Item(
                    id=entry.get("id") or entry.get("link", ""),
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    published_at=datetime.datetime(
                        *ts[:6], tzinfo=datetime.UTC
                    )
                    if (
                        ts := entry.get("published_parsed")
                        or entry.get("updated_parsed")
                        or entry.get("created_parsed")
                    )
                    else None,
                    description=entry.get("summary", ""),
                    source_name=source_name,
                    source_url=source_url,
                )
                for entry in feed.entries
            ]
            if attempt > 1:
                logger.info("Feed %r succeeded on attempt %d", url, attempt)
            return items
        except Exception as exc:
            last_exc = exc
            if attempt < _FETCH_RETRIES:
                delay = _FETCH_RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.debug(
                    "Feed %r attempt %d/%d failed (%s), retrying in %ds…",
                    url,
                    attempt,
                    _FETCH_RETRIES,
                    exc,
                    delay,
                )
                time.sleep(delay)
    logger.warning(
        "Failed to fetch feed %r after %d attempts: %s",
        url,
        _FETCH_RETRIES,
        last_exc,
    )
    return []


def _fetch_page(url: str) -> list[Item]:
    """Fetch a single web page and return a list of Items.

    Not yet implemented.

    Args:
        url: URL of the web page to scrape.

    Returns:
        List of ``Item`` objects parsed from the page.
    """
    raise NotImplementedError


def fetch_all_sources(urls: list[str] | None = None) -> list[Item]:
    """Fetch all configured sources and return the combined item list.

    Args:
        urls: Override list of feed URLs.  Defaults to URLs
            from ``load_sources()``.

    Returns:
        Flat list of ``Item`` objects from all sources, sorted by
        ``published_at`` descending (newest first, ``None`` dates last).
    """
    if urls is None:
        # TODO: handle non-RSS/Atom sources via fetch_page
        urls = [s["url"] for s in _load_sources()]
    items = []
    for url in urls:
        items.extend(_fetch_feed(url))
    items.sort(
        key=lambda item: (
            item.published_at
            or datetime.datetime.min.replace(tzinfo=datetime.UTC)
        ),
        reverse=True,
    )
    return items


def filter_recent_items(
    items: list[Item],
    lookback_hours: int = 24,
    reference_time: datetime.datetime | None = None,
) -> list[Item]:
    """Return only items published within the last ``lookback_hours`` hours.

    Items with no ``published_at`` are excluded.

    Args:
        items: List of ``Item`` objects to filter.
        lookback_hours: Lookback window in hours.  Defaults to 24.
        reference_time: Reference time for the cutoff.
            Defaults to the current UTC time.

    Returns:
        Filtered list of ``Item`` objects.
    """
    if reference_time is None:
        reference_time = datetime.datetime.now(tz=datetime.UTC)
    cutoff = reference_time - datetime.timedelta(hours=lookback_hours)
    recent_items = [
        item
        for item in items
        if item.published_at and cutoff <= item.published_at <= reference_time
    ]
    return recent_items
