"""Orchestrator: fetch → dedup → rank → notify → archive → persist."""

import datetime
import logging
import sys

from feedcurator.archive import build_archive_context, render_archive, write_archive
from feedcurator.config import settings
from feedcurator.dedup import filter_new, load_seen, save_seen
from feedcurator.fetch import fetch_all_sources
from feedcurator.llm import build_complete_fn
from feedcurator.notify import NotifyFn, send_notification
from feedcurator.rank import rank_items

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_log_level = getattr(logging, settings.pipeline.log_level.upper(), logging.INFO)
logging.basicConfig(level=_log_level, format=_LOG_FORMAT)
logger = logging.getLogger(__name__)


def _add_file_handler(run_date: datetime.date) -> None:
    """Attach a date-stamped FileHandler to the root logger."""
    settings.paths.logs_output_dir.mkdir(parents=True, exist_ok=True)
    log_file = settings.paths.logs_output_dir / f"{run_date.isoformat()}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logging.getLogger().addHandler(file_handler)


def main(notify_fn: NotifyFn | None = None) -> None:
    """Run the full curation pipeline.

    Pipeline stages:
    1. Fetch all RSS sources.
    2. Deduplicate against seen.json.
    3. Optionally rank with LLM.
    4. Send email notification.
    5. Generate and write archive HTML.
    6. Persist updated seen.json.

    Args:
        notify_fn: Injectable notification callable for testing.
            Defaults to ``send_notification``.
    """
    # --- Setup ---
    t0 = datetime.datetime.now(datetime.UTC)
    run_date = t0.date()
    if settings.pipeline.save_logs:
        _add_file_handler(run_date)
    logger.info("Pipeline start — run date: %s", run_date)

    # --- Fetch ---
    try:
        all_items = fetch_all_sources()
        logger.info("Fetched %d total items across all sources", len(all_items))
    except Exception:
        logger.exception("Fetch failed")
        sys.exit(1)

    # --- Dedup ---
    seen = load_seen()
    new_items = filter_new(all_items, seen)
    logger.info("%d new items after deduplication", len(new_items))

    # --- LLM ranking (optional) ---
    rank_result = None
    if settings.pipeline.enable_llm:
        complete = build_complete_fn()
        if complete is not None:
            try:
                rank_result = rank_items(new_items, complete)
                logger.info(
                    "Ranking complete: %d picks, summary %d chars",
                    len(rank_result.picks),
                    len(rank_result.summary),
                )
            except Exception:
                logger.warning("LLM ranking failed; skipping", exc_info=True)
        else:
            logger.info("No LLM provider available; skipping ranking")
    else:
        logger.info("LLM ranking disabled (PIPELINE__ENABLE_LLM=false)")

    # --- Email notification (optional) ---
    if settings.pipeline.enable_notify:
        notifier = notify_fn if notify_fn is not None else send_notification
        notifier(t0, new_items, rank_result)
    else:
        logger.info("Email notification disabled (PIPELINE__ENABLE_NOTIFY=false)")

    # --- Archive (optional) ---
    if settings.pipeline.enable_archive:
        try:
            ctx = build_archive_context(new_items, rank_result, run_date.isoformat())
            html = render_archive(ctx)
            write_archive(html)
            logger.info("Archive written to %s", settings.paths.archive_html)
        except Exception:
            logger.warning("Archive generation failed; skipping", exc_info=True)
    else:
        logger.info("Archive disabled (PIPELINE__ENABLE_ARCHIVE=false)")

    # --- Persist seen IDs (always, even if LLM/notify failed) ---
    updated_seen = seen | {item.id for item in new_items}
    save_seen(updated_seen)
    logger.info("Persisted %d seen IDs", len(updated_seen))

    elapsed = (datetime.datetime.now(datetime.UTC) - t0).total_seconds()
    logger.info("Pipeline complete in %.1f seconds", elapsed)


if __name__ == "__main__":
    main()
