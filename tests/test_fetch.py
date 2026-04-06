"""Tests for dailydrop.fetch — source loading, feed fetching, entry parsing."""

import logging
from unittest.mock import MagicMock

import pytest

from dailydrop.fetch import _fetch_feed, _load_sources, fetch_all_sources
from dailydrop.models import Item

_MINIMAL_SOURCES_YAML = """\
sources:
  - name: "Test Feed"
    type: rss
    url: "https://example.com/feed.xml"
    category: "tech"
"""


def test_load_sources_returns_list(tmp_path):
    f = tmp_path / "sources.yaml"
    f.write_text(_MINIMAL_SOURCES_YAML)
    sources = _load_sources(path=f)
    assert isinstance(sources, list)
    assert len(sources) == 1
    assert sources[0]["name"] == "Test Feed"
    assert sources[0]["url"] == "https://example.com/feed.xml"


def test_load_sources_missing_file_raises(tmp_path):
    with pytest.raises(Exception):
        _load_sources(path=tmp_path / "nonexistent.yaml")


def test_fetch_feed_returns_items(mocker):
    mock_entry = MagicMock()
    mock_entry.get.side_effect = lambda k, default="": {
        "id": "https://example.com/entry1",
        "link": "https://example.com/entry1",
        "title": "Entry One",
        "summary": "A brief summary.",
    }.get(k, default)
    mock_entry.published_parsed = None

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]
    mock_feed.bozo = False
    mock_feed.feed.get.return_value = ""

    mocker.patch("dailydrop.fetch.feedparser.parse", return_value=mock_feed)

    items = _fetch_feed("https://example.com/feed.xml")

    assert isinstance(items, list)
    assert all(isinstance(i, Item) for i in items)


def test_fetch_feed_returns_empty_on_error(mocker):
    mocker.patch(
        "dailydrop.fetch.feedparser.parse",
        side_effect=Exception("network error"),
    )
    items = _fetch_feed("https://bad.example.com/")
    assert items == []


def test_fetch_feed_logs_redacted_source_on_error(mocker, caplog):
    sensitive_url = (
        "https://user:secret@example.com/private/feed.xml?token=abc123"
    )
    mocker.patch(
        "dailydrop.fetch.feedparser.parse",
        side_effect=Exception("network error"),
    )

    with caplog.at_level(logging.WARNING):
        items = _fetch_feed(sensitive_url)

    assert items == []
    assert "example.com#" in caplog.text
    assert sensitive_url not in caplog.text
    assert "secret" not in caplog.text
    assert "token=abc123" not in caplog.text
    assert "network error" not in caplog.text


def _make_mock_feed(entry_data: dict) -> MagicMock:
    entry = MagicMock()
    entry.get.side_effect = lambda k, default="": entry_data.get(k, default)
    feed = MagicMock()
    feed.entries = [entry]
    feed.bozo = False
    feed.feed.get.return_value = ""
    return feed


def test_fetch_feed_uses_entry_id_as_stable_id(mocker):
    mock_feed = _make_mock_feed(
        {
            "id": "tag:example.com,2026:1",
            "link": "https://example.com/1",
            "title": "Title",
            "summary": "",
        }
    )
    mocker.patch("dailydrop.fetch.feedparser.parse", return_value=mock_feed)

    items = _fetch_feed("https://example.com/feed.xml")

    assert items[0].id == "tag:example.com,2026:1"


def test_fetch_feed_falls_back_to_link_when_no_id(mocker):
    mock_feed = _make_mock_feed(
        {
            "link": "https://example.com/no-id",
            "title": "No ID Entry",
            "summary": "",
        }
    )
    mocker.patch("dailydrop.fetch.feedparser.parse", return_value=mock_feed)

    items = _fetch_feed("https://example.com/feed.xml")

    assert items[0].id == "https://example.com/no-id"


def test_fetch_feed_published_at_is_none_when_no_date(mocker):
    mock_feed = _make_mock_feed(
        {
            "id": "https://example.com/no-date",
            "link": "https://example.com/no-date",
            "title": "No Date",
            "summary": "",
        }
    )
    mocker.patch("dailydrop.fetch.feedparser.parse", return_value=mock_feed)

    items = _fetch_feed("https://example.com/feed.xml")

    assert items[0].published_at is None


def test_fetch_all_sources_combines_feeds(mocker, sample_items):
    mocker.patch(
        "dailydrop.fetch._fetch_feed",
        side_effect=[sample_items[:2], sample_items[2:]],
    )

    items = fetch_all_sources(
        ["https://a.example.com/", "https://b.example.com/"]
    )

    assert len(items) == 3


def test_fetch_feed_falls_back_to_updated_parsed_when_no_published(mocker):
    """Atom entries with only <updated> must not be silently dropped."""
    import time

    ts = time.strptime("2026-01-15 12:00:00", "%Y-%m-%d %H:%M:%S")
    mock_feed = _make_mock_feed(
        {
            "id": "https://example.com/atom-updated-only",
            "link": "https://example.com/atom-updated-only",
            "title": "Atom Updated Only",
            "summary": "",
            "updated_parsed": ts,
        }
    )
    mocker.patch("dailydrop.fetch.feedparser.parse", return_value=mock_feed)

    items = _fetch_feed("https://example.com/feed.xml")

    assert items[0].published_at is not None
    assert items[0].published_at.year == 2026
    assert items[0].published_at.month == 1
    assert items[0].published_at.day == 15


def test_fetch_all_sources_sorted_newest_first(mocker, sample_items):
    # sample_items are already sorted oldest→newest;
    # fetch_all_sources should reverse
    mocker.patch("dailydrop.fetch._fetch_feed", return_value=sample_items)

    items = fetch_all_sources(["https://feed.example.com/"])

    dates = [i.published_at for i in items if i.published_at]
    assert dates == sorted(dates, reverse=True)
