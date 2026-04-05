"""Tests for dailydrop.pipeline — orchestrator end-to-end."""

import pytest

from dailydrop.pipeline import main


def test_main_exits_on_fetch_failure(mocker):
    mocker.patch(
        "dailydrop.pipeline.fetch_all_sources",
        side_effect=RuntimeError("network down"),
    )

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
