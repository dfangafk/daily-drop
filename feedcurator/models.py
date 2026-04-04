"""Core data types for feedcurator."""

import datetime
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Item:
    """A single content item fetched from an RSS source.

    Attributes:
        id: Stable unique identifier (typically the feed entry's ``id`` or
            ``link`` field so the same article never appears twice even if
            the feed rotates IDs).
        source_type: Feed type, e.g. ``"rss"``.
        source_name: Human-readable feed name from ``sources.yaml``.
        title: Entry title.
        url: Canonical link to the content.
        published_at: Publication timestamp (UTC).  ``None`` when the feed
            omits a date.
        description: First paragraph / summary from the feed entry.  May be
            empty.
    """

    id: str
    source_type: str
    source_name: str
    title: str
    url: str
    published_at: datetime.datetime | None
    description: str = ""


@dataclass
class RankResult:
    """Result of LLM ranking of a set of items.

    Attributes:
        picks: Ordered list of item IDs selected by the LLM (best first).
        rationale: One-sentence explanation per picked item, keyed by item ID.
        summary: Short paragraph describing today's batch of recommendations.
    """

    picks: list[str] = field(default_factory=list)
    rationale: dict[str, str] = field(default_factory=dict)
    summary: str = ""
