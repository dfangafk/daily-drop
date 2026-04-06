"""Tests for dailydrop.pipeline — orchestrator end-to-end."""

import argparse

import pytest

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


