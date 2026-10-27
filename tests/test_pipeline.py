"""Tests for dailydrop.pipeline — orchestrator end-to-end."""

import argparse

import pytest

from dailydrop.models import Item
from dailydrop.pipeline import main

_VIDEO = Item(
    id="v",
    title="Video",
    url="https://www.youtube.com/watch?v=bxcnCOej764",
    published_at=None,
)
_SHORT = Item(
    id="s",
    title="Short",
    url="https://www.youtube.com/shorts/BI5sVUq5Z2Y",
    published_at=None,
)


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


@pytest.mark.parametrize(
    ("exclude_shorts", "expected"),
    [(True, [_VIDEO]), (False, [_VIDEO, _SHORT])],
)
def test_main_exclude_youtube_shorts_setting(mocker, exclude_shorts, expected):
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
        return_value=[_VIDEO, _SHORT],
    )
    mocker.patch(
        "dailydrop.pipeline.settings.pipeline.exclude_youtube_shorts",
        exclude_shorts,
    )
    mock_filter_recent = mocker.patch(
        "dailydrop.pipeline.filter_recent_items", return_value=[]
    )

    main()

    assert mock_filter_recent.call_args.args[0] == expected
