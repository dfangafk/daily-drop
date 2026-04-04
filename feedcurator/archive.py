"""Generate the static HTML archive page for GitHub Pages."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from feedcurator.config import settings
from feedcurator.models import Item, RankResult

logger = logging.getLogger(__name__)


def build_archive_context(
    new_items: list[Item],
    rank_result: RankResult | None,
    run_date: str,
) -> dict:
    """Build the Jinja2 context dict for the archive template.

    Args:
        new_items: All new (deduplicated) items from this run.
        rank_result: LLM picks, or ``None`` if LLM was skipped.
        run_date: ISO date string for the run header.

    Returns:
        Context dict for ``archive.html.jinja2``.
    """
    ...


def render_archive(ctx: dict) -> str:
    """Render the archive HTML template with the given context.

    Returns:
        Rendered HTML string.
    """
    ...


def write_archive(html: str, path: Path | None = None) -> None:
    """Write rendered HTML to disk, creating parent directories as needed.

    Args:
        html: Rendered HTML string.
        path: Override output path.  Defaults to ``settings.paths.archive_html``.
    """
    ...
