"""Tests for dailydrop.models — Item construction."""

import datetime

from dailydrop.models import Item


def test_item_construction():
    item = Item(
        id="https://example.com/1",
        source_url="https://example.com/feed.xml",
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
        source_url="https://example.com/feed.xml",
        source_name="Feed",
        title="Title",
        url="https://example.com",
        published_at=None,
    )
    assert item.published_at is None
