"""Tests for dailydrop.pipeline — orchestrator end-to-end."""

import argparse
import datetime
import logging

import pytest

import dailydrop.pipeline as pipeline_module
from dailydrop.pipeline import main


def test_main_exits_on_fetch_failure(mocker):
    mocker.patch(
        "dailydrop.pipeline._parse_args",
        return_value=argparse.Namespace(
            lookback_hours=24,
            reference_time=None,
            skip_email=True,
        ),
    )
    mocker.patch(
        "dailydrop.pipeline.fetch_all_sources",
        side_effect=RuntimeError("network down"),
    )

    with pytest.raises(RuntimeError, match="network down"):
        main()


def test_main_debug_logging_redacts_item_contents(
    mocker, sample_items, caplog
):
    mocker.patch(
        "dailydrop.pipeline._parse_args",
        return_value=argparse.Namespace(
            lookback_hours=24,
            reference_time=datetime.datetime(
                2026, 4, 1, 13, 0, tzinfo=datetime.UTC
            ),
            skip_email=True,
        ),
    )
    mocker.patch("dailydrop.pipeline.fetch_all_sources", return_value=[])
    mocker.patch(
        "dailydrop.pipeline.filter_recent_items",
        return_value=sample_items[:1],
    )
    mocker.patch("dailydrop.pipeline.normalize_items")
    pipeline_module.logger.setLevel(logging.DEBUG)

    with caplog.at_level(logging.DEBUG, logger="dailydrop.pipeline"):
        main()

    assert "Article A" not in caplog.text
    assert "First article about AI." not in caplog.text
    assert "https://example.com/a" not in caplog.text
    assert "https://example.com/feed.xml" not in caplog.text
    assert "title_chars=9" in caplog.text
    assert "description_chars=23" in caplog.text
