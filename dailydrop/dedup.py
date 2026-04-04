"""Deduplication via a persistent seen-items journal."""

import json
import logging
from pathlib import Path

from dailydrop.config import settings
from dailydrop.models import Item

logger = logging.getLogger(__name__)


def load_seen(path: Path | None = None) -> set[str]:
    """Load the set of already-seen item IDs from the journal file.

    Returns an empty set if the file does not exist yet.

    Args:
        path: Override path.  Defaults to ``settings.paths.seen_json``.

    Returns:
        Set of previously seen item ID strings.
    """
    ...


def save_seen(seen: set[str], path: Path | None = None) -> None:
    """Persist the seen-ID set back to the journal file.

    Creates parent directories if they do not exist.

    Args:
        seen: Full set of IDs to write.
        path: Override path.  Defaults to ``settings.paths.seen_json``.
    """
    ...


def filter_new(items: list[Item], seen: set[str]) -> list[Item]:
    """Return only items whose ``id`` is not in ``seen``.

    Args:
        items: All fetched items.
        seen: Previously seen IDs loaded from the journal.

    Returns:
        Subset of ``items`` that have not been seen before.
    """
    ...
