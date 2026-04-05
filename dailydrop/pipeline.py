"""Orchestrator: fetch → dedup → rank → notify → persist."""

import datetime
import json
import logging
import sys

from dailydrop.config import settings
from dailydrop.fetch import fetch_all_sources
from dailydrop.llm import build_complete_fn
from dailydrop.notify import NotifyFn, send_notification
from dailydrop.rank import rank_items

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
    5. Persist updated seen.json.

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
    seen_path = settings.paths.seen_json
    seen: set[str] = set()
    if seen_path.exists():
        seen = set(json.loads(seen_path.read_text()).get("ids", []))
    new_items = [item for item in all_items if item.id not in seen]
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

    # --- Persist seen IDs (always, even if LLM/notify failed) ---
    updated_seen = seen | {item.id for item in new_items}
    seen_path.parent.mkdir(parents=True, exist_ok=True)
    seen_path.write_text(json.dumps({"ids": sorted(updated_seen)}))
    logger.info("Persisted %d seen IDs", len(updated_seen))

    elapsed = (datetime.datetime.now(datetime.UTC) - t0).total_seconds()
    logger.info("Pipeline complete in %.1f seconds", elapsed)


if __name__ == "__main__":
    main()
