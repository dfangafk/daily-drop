"""LLM-based ranking: pick top-N items matching user interests."""

import json
import logging
from collections.abc import Callable
from pathlib import Path

from dailydrop.config import settings
from dailydrop.models import Item, RankResult

logger = logging.getLogger(__name__)


def load_interests(path: Path | None = None) -> str:
    """Read interests.txt and return its content as a single string.

    Args:
        path: Override path.  Defaults to ``settings.paths.interests_txt``.

    Returns:
        Raw text of the interests file, stripped of leading/trailing whitespace.
    """
    ...


def rank_items(
    items: list[Item],
    complete: Callable[[str], str],
    interests: str | None = None,
) -> RankResult:
    """Send new items to the LLM and return the ranked top-N picks.

    Builds a numbered list of items with title + description, inserts the
    user's interest profile, and calls ``complete`` once.  Parses the
    returned JSON into a ``RankResult``.

    If ``items`` is empty, returns an empty ``RankResult`` without calling
    the LLM.

    Args:
        items: New (deduplicated) items to rank.
        complete: LLM callable from ``build_complete_fn()``.
        interests: Override interest text.  Defaults to ``load_interests()``.

    Returns:
        ``RankResult`` with ``picks``, ``rationale``, and ``summary``.

    Raises:
        ValueError: If the LLM response is not valid JSON or is missing
            required keys (``summary`` / ``picks``).
        Exception: Any exception from ``complete`` propagates to the caller.
    """
    ...
