"""Fetch new items from all configured RSS sources."""

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


def fetch_feed(source: dict) -> list[Item]:
    """Fetch a single RSS/Atom feed and return a list of Items.

    Never raises — on parse failure, logs a warning and returns an empty list.

    Args:
        source: A source dict loaded from ``sources.yaml``.

    Returns:
        List of ``Item`` objects parsed from the feed.
    """
    ...


def fetch_all_sources(sources: list[dict] | None = None) -> list[Item]:
    """Fetch all configured sources and return the combined item list.

    Args:
        sources: Override source list.  Defaults to ``load_sources()``.

    Returns:
        Flat list of ``Item`` objects from all sources, sorted by
        ``published_at`` descending (newest first, ``None`` dates last).
    """
    ...


def _parse_entry(entry: feedparser.FeedParserDict, source: dict) -> Item:
    """Convert a single feedparser entry to an ``Item``.

    Derives a stable ``id`` from ``entry.id`` if present, otherwise from
    ``entry.link``.  Parses ``published_parsed`` or ``updated_parsed`` for
    the timestamp.

    Args:
        entry: A feedparser entry dict.
        source: The source dict this entry came from.

    Returns:
        A populated ``Item`` dataclass.
    """
    ...
