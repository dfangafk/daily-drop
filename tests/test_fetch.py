"""Tests for dailydrop.fetch — source loading, feed fetching, entry parsing."""

import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dailydrop.fetch import _parse_entry, fetch_all_sources, fetch_feed, load_sources
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
    sources = load_sources(path=f)
    assert isinstance(sources, list)
    assert len(sources) == 1
    assert sources[0]["name"] == "Test Feed"
    assert sources[0]["url"] == "https://example.com/feed.xml"


def test_load_sources_missing_file_raises(tmp_path):
    with pytest.raises(Exception):
        load_sources(path=tmp_path / "nonexistent.yaml")


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

    mocker.patch("dailydrop.fetch.feedparser.parse", return_value=mock_feed)

    items = fetch_feed("https://example.com/feed.xml")

    assert isinstance(items, list)
    assert all(isinstance(i, Item) for i in items)


def test_fetch_feed_returns_empty_on_error(mocker):
    mocker.patch("dailydrop.fetch.feedparser.parse", side_effect=Exception("network error"))
    items = fetch_feed("https://bad.example.com/")
    assert items == []


def test_parse_entry_uses_entry_id_as_stable_id():
    entry = MagicMock()
    entry.get.side_effect = lambda k, default="": {
        "id": "tag:example.com,2026:1",
        "link": "https://example.com/1",
        "title": "Title",
        "summary": "",
    }.get(k, default)

    item = _parse_entry(entry)

    assert item.id == "tag:example.com,2026:1"


def test_parse_entry_falls_back_to_link_when_no_id():
    entry = MagicMock()
    entry.get.side_effect = lambda k, default="": {
        "link": "https://example.com/no-id",
        "title": "No ID Entry",
        "summary": "",
    }.get(k, default)

    item = _parse_entry(entry)

    assert item.id == "https://example.com/no-id"


def test_parse_entry_published_at_is_none_when_no_date():
    entry = MagicMock()
    entry.get.side_effect = lambda k, default="": {
        "id": "https://example.com/no-date",
        "link": "https://example.com/no-date",
        "title": "No Date",
        "summary": "",
    }.get(k, default)

    item = _parse_entry(entry)

    assert item.published_at is None


def test_fetch_all_sources_combines_feeds(mocker, sample_items):
    mocker.patch(
        "dailydrop.fetch.fetch_feed",
        side_effect=[sample_items[:2], sample_items[2:]],
    )

    items = fetch_all_sources(["https://a.example.com/", "https://b.example.com/"])

    assert len(items) == 3


def test_fetch_all_sources_sorted_newest_first(mocker, sample_items):
    # sample_items are already sorted oldest→newest; fetch_all_sources should reverse
    mocker.patch("dailydrop.fetch.fetch_feed", return_value=sample_items)

    items = fetch_all_sources(["https://feed.example.com/"])

    dates = [i.published_at for i in items if i.published_at]
    assert dates == sorted(dates, reverse=True)
