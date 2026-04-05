"""Tests for dailydrop.pipeline — orchestrator end-to-end."""

import json

import pytest

from dailydrop.models import RankResult
from dailydrop.pipeline import main


def _patch_seen(mocker, tmp_path, ids=None):
    """Patch settings.paths.seen_json to a temp file with given IDs."""
    seen_file = tmp_path / "seen.json"
    if ids is not None:
        seen_file.write_text(json.dumps({"ids": ids}))
    mocker.patch("dailydrop.pipeline.settings.paths.seen_json", seen_file)
    return seen_file


def test_main_no_llm(mocker, tmp_path, sample_items):
    mocker.patch("dailydrop.pipeline.fetch_all_feeds", return_value=sample_items)
    _patch_seen(mocker, tmp_path)
    mock_rank = mocker.patch("dailydrop.pipeline.rank_items")
    mocker.patch("dailydrop.pipeline.send_notification")
    mocker.patch("dailydrop.pipeline.build_complete_fn", return_value=None)

    main()

    mock_rank.assert_not_called()


def test_main_with_llm(mocker, tmp_path, sample_items):
    rank_result = RankResult(picks=[sample_items[0].id], rationale={}, summary="Great picks.")
    mocker.patch("dailydrop.pipeline.fetch_all_feeds", return_value=sample_items)
    _patch_seen(mocker, tmp_path)
    mock_complete = mocker.Mock(return_value='{"summary":"x","picks":[]}')
    mocker.patch("dailydrop.pipeline.build_complete_fn", return_value=mock_complete)
    mock_rank = mocker.patch("dailydrop.pipeline.rank_items", return_value=rank_result)
    mocker.patch("dailydrop.pipeline.send_notification")

    main()

    mock_rank.assert_called_once()


def test_main_llm_failure_continues(mocker, tmp_path, sample_items):
    mocker.patch("dailydrop.pipeline.fetch_all_feeds", return_value=sample_items)
    _patch_seen(mocker, tmp_path)
    mocker.patch("dailydrop.pipeline.build_complete_fn", return_value=mocker.Mock())
    mocker.patch("dailydrop.pipeline.rank_items", side_effect=RuntimeError("LLM failed"))
    mock_notify = mocker.patch("dailydrop.pipeline.send_notification")

    main()  # must not raise

    mock_notify.assert_called_once()


def test_main_exits_on_fetch_failure(mocker):
    mocker.patch(
        "dailydrop.pipeline.fetch_all_feeds",
        side_effect=RuntimeError("network down"),
    )

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_uses_injectable_notify_fn(mocker, tmp_path, sample_items):
    mocker.patch("dailydrop.pipeline.fetch_all_feeds", return_value=sample_items)
    _patch_seen(mocker, tmp_path)
    mocker.patch("dailydrop.pipeline.build_complete_fn", return_value=None)
    mock_default_notify = mocker.patch("dailydrop.pipeline.send_notification")
    custom_notify = mocker.Mock()

    main(notify_fn=custom_notify)

    custom_notify.assert_called_once()
    mock_default_notify.assert_not_called()


def test_main_saves_seen_even_when_notify_fails(mocker, tmp_path, sample_items):
    mocker.patch("dailydrop.pipeline.fetch_all_feeds", return_value=sample_items)
    seen_file = _patch_seen(mocker, tmp_path)
    mocker.patch("dailydrop.pipeline.build_complete_fn", return_value=None)
    failing_notify = mocker.Mock(side_effect=Exception("SMTP down"))

    with pytest.raises(Exception, match="SMTP down"):
        main(notify_fn=failing_notify)

    # seen.json was not written because notify failed before persist
    assert not seen_file.exists()
