"""Shared fixtures for dailydrop tests."""

import datetime

import pytest

from dailydrop.models import Item


@pytest.fixture(autouse=True)
def no_file_logging(mocker):
    """Prevent pipeline tests from writing real log files to disk."""
    mocker.patch("dailydrop.pipeline._add_file_handler")


@pytest.fixture
def sample_items() -> list[Item]:
    """Three minimal Items for use across test modules."""
    return [
        Item(
            id="https://example.com/a",
            source_url="https://example.com/feed.xml",
            source_name="Test Blog",
            title="Article A",
            url="https://example.com/a",
            published_at=datetime.datetime(2026, 4, 1, 10, 0, tzinfo=datetime.UTC),
            description="First article about AI.",
        ),
        Item(
            id="https://example.com/b",
            source_url="https://example.com/feed.xml",
            source_name="Test Blog",
            title="Article B",
            url="https://example.com/b",
            published_at=datetime.datetime(2026, 4, 1, 11, 0, tzinfo=datetime.UTC),
            description="Second article about startups.",
        ),
        Item(
            id="https://example.com/c",
            source_url="https://example.com/feed.xml",
            source_name="Other Feed",
            title="Article C",
            url="https://example.com/c",
            published_at=datetime.datetime(2026, 4, 1, 12, 0, tzinfo=datetime.UTC),
            description="Third article about economics.",
        ),
    ]
