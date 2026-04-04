"""Tests for feedcurator.dedup — load/save/filter seen-item journal."""

import json
from pathlib import Path

import pytest

from feedcurator.dedup import filter_new, load_seen, save_seen


def test_load_seen_returns_empty_set_when_no_file(tmp_path):
    result = load_seen(path=tmp_path / "seen.json")
    assert result == set()


def test_load_seen_returns_ids_from_file(tmp_path):
    f = tmp_path / "seen.json"
    f.write_text(json.dumps({"ids": ["a", "b", "c"]}))
    result = load_seen(path=f)
    assert result == {"a", "b", "c"}


def test_save_seen_writes_json(tmp_path):
    f = tmp_path / "seen.json"
    save_seen({"x", "y"}, path=f)
    data = json.loads(f.read_text())
    assert set(data["ids"]) == {"x", "y"}


def test_save_seen_creates_parent_dirs(tmp_path):
    f = tmp_path / "sub" / "dir" / "seen.json"
    save_seen({"z"}, path=f)
    assert f.exists()


def test_filter_new_excludes_seen_items(sample_items):
    seen = {sample_items[0].id}
    result = filter_new(sample_items, seen)
    assert len(result) == 2
    assert all(item.id != sample_items[0].id for item in result)


def test_filter_new_returns_all_when_seen_empty(sample_items):
    result = filter_new(sample_items, set())
    assert result == sample_items


def test_filter_new_returns_empty_when_all_seen(sample_items):
    seen = {item.id for item in sample_items}
    result = filter_new(sample_items, seen)
    assert result == []


def test_filter_new_empty_items():
    result = filter_new([], {"some-id"})
    assert result == []
