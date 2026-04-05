"""Orchestrator: fetch → filter → notify → persist."""

import argparse
import datetime
import logging

from dailydrop.config import settings
from dailydrop.fetch import fetch_all_sources, filter_recent_items
from dailydrop.normalize import normalize_items
from dailydrop.notify import send_notification

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_log_level = getattr(
    logging, settings.pipeline.log_level.upper(), logging.INFO
)
logging.basicConfig(level=_log_level, format=_LOG_FORMAT)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Daily Drop pipeline."
    )
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
        help=(
            "Reference time in ISO 8601 format (default: now)."
            " E.g. 2026-04-04T08:00:00"
        ),
    )
    parser.add_argument(
        "--skip-email",
        action="store_true",
        help="Skip sending the notification email.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the full pipeline: fetch → filter → normalize → notify."""
    args = _parse_args()
    pipeline_start = datetime.datetime.now(datetime.UTC)
    if args.reference_time is not None:
        reference_time = (
            args.reference_time
            if args.reference_time.tzinfo is not None
            else args.reference_time.replace(tzinfo=datetime.UTC)
        )
    else:
        reference_time = pipeline_start
    run_date = reference_time.date()
    logger.info(
        "Pipeline start — run date: %s, reference time: %s,"
        " look-back: %d hours",
        run_date,
        reference_time.isoformat(),
        args.hours,
    )

    try:
        all_items = fetch_all_sources()
        logger.info(
            "Fetched %d total items across all sources", len(all_items)
        )

        recent_items = filter_recent_items(
            all_items, hours=args.hours, reference_time=reference_time
        )
        logger.info(
            "Filtered to %d items within the last %d hours (%d excluded)",
            len(recent_items),
            args.hours,
            len(all_items) - len(recent_items),
        )
        normalize_items(recent_items)
        logger.info("Normalization complete")
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
                item.description[:120] + "…"
                if len(item.description) > 120
                else item.description,
                item.url,
                item.published_at,
                item.source_name,
                item.source_url,
            )

        if args.skip_email:
            logger.info("Skipping email notification")
        else:
            logger.info(
                "Sending email notification for %d items", len(recent_items)
            )
            send_notification(reference_time, recent_items)

        elapsed = (
            datetime.datetime.now(datetime.UTC) - pipeline_start
        ).total_seconds()
        logger.info("Pipeline completed in %.1f seconds", elapsed)
    except Exception:
        elapsed = (
            datetime.datetime.now(datetime.UTC) - pipeline_start
        ).total_seconds()
        logger.exception("Pipeline failed after %.1f seconds", elapsed)
        raise


if __name__ == "__main__":
    main()
