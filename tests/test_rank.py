"""Tests for feedcurator.rank — LLM-based item ranking."""

import json
from pathlib import Path

import pytest

from feedcurator.models import RankResult
from feedcurator.rank import load_interests, rank_items

_VALID_RESPONSE = json.dumps({
    "summary": "Great AI content today.",
    "picks": [
        {"id": "https://example.com/a", "rationale": "Directly about AI research."},
        {"id": "https://example.com/c", "rationale": "Economics angle is relevant."},
    ],
})


def test_rank_items_success(sample_items):
    complete = lambda _: _VALID_RESPONSE
    result = rank_items(sample_items, complete, interests="AI research")

    assert isinstance(result, RankResult)
    assert result.summary == "Great AI content today."
    assert "https://example.com/a" in result.picks
    assert result.rationale["https://example.com/a"] == "Directly about AI research."


def test_rank_items_empty_list_returns_empty_result():
    complete = lambda _: _VALID_RESPONSE
    result = rank_items([], complete, interests="AI research")

    assert result.picks == []
    assert result.summary == ""


def test_rank_items_llm_not_called_for_empty_items(mocker):
    mock_complete = mocker.Mock()
    rank_items([], mock_complete, interests="AI research")
    mock_complete.assert_not_called()


def test_rank_items_malformed_json_raises(sample_items):
    complete = lambda _: "not valid json {{{"
    with pytest.raises(ValueError, match="non-JSON"):
        rank_items(sample_items, complete, interests="AI")


def test_rank_items_missing_required_keys_raises(sample_items):
    complete = lambda _: json.dumps({"unexpected": "shape"})
    with pytest.raises(ValueError, match="missing required keys"):
        rank_items(sample_items, complete, interests="AI")


def test_rank_items_propagates_complete_exception(sample_items):
    def bad_complete(_):
        raise RuntimeError("LLM unavailable")

    with pytest.raises(RuntimeError, match="LLM unavailable"):
        rank_items(sample_items, bad_complete, interests="AI")


def test_load_interests_reads_file(tmp_path):
    f = tmp_path / "interests.txt"
    f.write_text("machine learning\nstartups\n")
    result = load_interests(path=f)
    assert "machine learning" in result
    assert "startups" in result


def test_load_interests_strips_whitespace(tmp_path):
    f = tmp_path / "interests.txt"
    f.write_text("  AI research  \n")
    result = load_interests(path=f)
    assert result == result.strip()


def test_rank_items_uses_default_interests_path(mocker, sample_items):
    mocker.patch("feedcurator.rank.load_interests", return_value="AI")
    complete = lambda _: _VALID_RESPONSE
    result = rank_items(sample_items, complete)
    assert isinstance(result, RankResult)
