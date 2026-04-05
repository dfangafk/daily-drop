"""Tests for dailydrop.normalize."""

import datetime

from dailydrop.models import Item
from dailydrop.normalize import (
    _normalize_description,
    _normalize_published_at,
    normalize_items,
)

# ---------------------------------------------------------------------------
# _normalize_description
# ---------------------------------------------------------------------------


def test_normalize_description_strips_html():
    assert _normalize_description("<p>Hello <b>world</b></p>") == "Hello world"


def test_normalize_description_unescapes_entities():
    assert (
        _normalize_description("AT&amp;T &mdash; &lt;tech&gt;")
        == "AT&T — <tech>"
    )


def test_normalize_description_collapses_whitespace():
    assert (
        _normalize_description("  too   many   spaces  ") == "too many spaces"
    )


def test_normalize_description_truncates_at_word_boundary():
    raw = "one two three four five"
    result = _normalize_description(raw, max_chars=12)
    assert result.endswith("…")
    assert len(result) <= 13  # 12 chars + ellipsis


def test_normalize_description_no_truncation_when_short():
    raw = "short"
    assert _normalize_description(raw, max_chars=300) == "short"


def test_normalize_description_empty_string():
    assert _normalize_description("") == ""


# ---------------------------------------------------------------------------
# _normalize_published_at
# ---------------------------------------------------------------------------


def test_normalize_published_at_none_returns_none():
    assert _normalize_published_at(None) is None


def test_normalize_published_at_converts_timezone(mocker):
    mocker.patch(
        "dailydrop.normalize.settings.notify.timezone", "America/New_York"
    )
    utc_dt = datetime.datetime(2026, 4, 5, 12, 0, tzinfo=datetime.UTC)
    result = _normalize_published_at(utc_dt)
    assert result.tzname() == "EDT"
    assert result.hour == 8  # UTC-4 during EDT


def test_normalize_published_at_preserves_instant(mocker):
    mocker.patch(
        "dailydrop.normalize.settings.notify.timezone", "America/Los_Angeles"
    )
    utc_dt = datetime.datetime(2026, 4, 5, 12, 0, tzinfo=datetime.UTC)
    result = _normalize_published_at(utc_dt)
    assert result.utctimetuple()[:6] == utc_dt.utctimetuple()[:6]


# ---------------------------------------------------------------------------
# normalize_items
# ---------------------------------------------------------------------------


def test_normalize_items_modifies_in_place(mocker, sample_items):
    mocker.patch("dailydrop.normalize.settings.notify.timezone", "UTC")
    original_list = sample_items
    returned = normalize_items(sample_items)
    assert returned is original_list


def test_normalize_items_cleans_descriptions(mocker, sample_items):
    mocker.patch("dailydrop.normalize.settings.notify.timezone", "UTC")
    sample_items[0].description = "<p>Raw <b>HTML</b></p>"
    normalize_items(sample_items)
    assert sample_items[0].description == "Raw HTML"


def test_normalize_items_converts_published_at(mocker, sample_items):
    mocker.patch(
        "dailydrop.normalize.settings.notify.timezone", "America/New_York"
    )
    normalize_items(sample_items)
    for item in sample_items:
        if item.published_at is not None:
            assert item.published_at.tzname() in ("EST", "EDT")


def test_normalize_items_handles_none_published_at(mocker):
    mocker.patch("dailydrop.normalize.settings.notify.timezone", "UTC")
    item = Item(
        id="x",
        title="X",
        url="https://example.com/x",
        published_at=None,
        description="<b>bold</b>",
    )
    normalize_items([item])
    assert item.published_at is None
    assert item.description == "bold"
