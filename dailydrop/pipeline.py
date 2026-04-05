"""Orchestrator: fetch → filter → notify → persist."""

import argparse
import datetime
import logging
import sys

from dailydrop.config import settings
from dailydrop.fetch import fetch_all_feeds, filter_recent_items
from dailydrop.notify import send_notification

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_log_level = getattr(logging, settings.pipeline.log_level.upper(), logging.INFO)
logging.basicConfig(level=_log_level, format=_LOG_FORMAT)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Daily Drop pipeline.")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Look-back window in hours (default: 24).",
    )
    parser.add_argument(
        "--reference-time",
        type=datetime.datetime.fromisoformat,
        default=None,
        metavar="DATETIME",
        help="Reference time in ISO 8601 format (default: now). E.g. 2026-04-04T08:00:00",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending the notification email.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the fetch stage of the pipeline."""
    args = _parse_args()
    if args.reference_time is not None:
        t0 = args.reference_time if args.reference_time.tzinfo is not None else args.reference_time.replace(tzinfo=datetime.timezone.utc)
    else:
        t0 = datetime.datetime.now(datetime.UTC)
    run_date = t0.date()
    logger.info("Pipeline start — run date: %s", run_date)

    try:
        all_items = fetch_all_feeds()
        logger.info("Fetched %d total items across all sources", len(all_items))
    except Exception:
        logger.exception("Fetch failed")
        sys.exit(1)

    recent_items = filter_recent_items(all_items, hours=args.hours, reference_time=t0)
    logger.info("%d items within the last 24 hours", len(recent_items))
    for item in recent_items:
        logger.debug(
            "\n  id:           %s"
            "\n  title:        %s"
            "\n  description:  %s"
            "\n  url:          %s"
            "\n  published_at: %s"
            "\n  source_name:  %s"
            "\n  source_url:   %s",
            item.id,
            item.title,
            item.description[:120] + "…" if len(item.description) > 120 else item.description,
            item.url,
            item.published_at,
            item.source_name,
            item.source_url,
        )

    # TODO: pass recent_items through an LLM enrichment/ranking step before
    #       notify/persist stages (e.g. score relevance, extract tags, summarise).

    if args.no_email:
        logger.info("Skipping email notification")
    else:
        send_notification(t0, recent_items)

    elapsed = (datetime.datetime.now(datetime.UTC) - t0).total_seconds()
    logger.info("Pipeline complete in %.1f seconds", elapsed)


if __name__ == "__main__":
    main()
