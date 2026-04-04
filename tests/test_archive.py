"""Tests for dailydrop.archive — context building, rendering, writing."""

import datetime
from pathlib import Path

import pytest

from dailydrop.archive import build_archive_context, render_archive, write_archive
from dailydrop.models import RankResult


def test_build_archive_context_structure(sample_items):
    ctx = build_archive_context(sample_items, None, "2026-04-01")

    assert ctx["run_date"] == "2026-04-01"
    assert "all_items" in ctx
    assert "picks" in ctx
    assert "summary" in ctx
    assert "generated_at" in ctx


def test_build_archive_context_no_picks_when_no_rank_result(sample_items):
    ctx = build_archive_context(sample_items, None, "2026-04-01")
    assert ctx["picks"] == []


def test_build_archive_context_picks_from_rank_result(sample_items):
    rank = RankResult(
        picks=[sample_items[0].id],
        rationale={sample_items[0].id: "Top pick."},
        summary="One strong item today.",
    )
    ctx = build_archive_context(sample_items, rank, "2026-04-01")

    assert len(ctx["picks"]) == 1
    assert ctx["summary"] == "One strong item today."


def test_render_archive_returns_html_string(sample_items):
    ctx = build_archive_context(sample_items, None, "2026-04-01")
    html = render_archive(ctx)

    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "dailydrop" in html


def test_render_archive_contains_item_titles(sample_items):
    ctx = build_archive_context(sample_items, None, "2026-04-01")
    html = render_archive(ctx)

    assert "Article A" in html
    assert "Article B" in html
    assert "Article C" in html


def test_write_archive_creates_file(sample_items, tmp_path):
    html = "<html><body>test</body></html>"
    out = tmp_path / "archive.html"
    write_archive(html, path=out)

    assert out.exists()
    assert out.read_text() == html


def test_write_archive_creates_parent_dirs(tmp_path):
    html = "<html></html>"
    out = tmp_path / "sub" / "dir" / "archive.html"
    write_archive(html, path=out)
    assert out.exists()
