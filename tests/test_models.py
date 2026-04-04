"""Tests for dailydrop.models — Item and RankResult construction."""

import datetime

import pytest

from dailydrop.models import Item, RankResult


def test_item_construction():
    item = Item(
        id="https://example.com/1",
        source_type="rss",
        source_name="Test Feed",
        title="Test Title",
        url="https://example.com/1",
        published_at=datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC),
    )
    assert item.id == "https://example.com/1"
    assert item.description == ""  # default


def test_item_none_published_at():
    item = Item(
        id="x",
        source_type="rss",
        source_name="Feed",
        title="Title",
        url="https://example.com",
        published_at=None,
    )
    assert item.published_at is None


def test_rank_result_defaults():
    result = RankResult()
    assert result.picks == []
    assert result.rationale == {}
    assert result.summary == ""


def test_rank_result_construction():
    result = RankResult(
        picks=["id1", "id2"],
        rationale={"id1": "Relevant to AI.", "id2": "About startups."},
        summary="Today's top picks focus on AI and startups.",
    )
    assert len(result.picks) == 2
    assert result.rationale["id1"] == "Relevant to AI."
