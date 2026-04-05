"""Core data types for dailydrop."""

import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Item:
    """A single content item fetched from an RSS source.

    Attributes:
        id: Stable unique identifier (typically the feed entry's ``id`` or
            ``link`` field so the same article never appears twice even if
            the feed rotates IDs).
        source_url: Canonical URL of the source feed or channel.
        source_name: Human-readable feed name from ``sources.yaml``.
        title: Entry title.
        url: Canonical link to the content.
        published_at: Publication timestamp (UTC).  ``None`` when the feed
            omits a date.
        description: First paragraph / summary from the feed entry.  May be
            empty.
    """

    id: str
    title: str
    url: str
    published_at: datetime.datetime | None
    description: str = ""
    source_name: str = ""
    source_url: str = ""
