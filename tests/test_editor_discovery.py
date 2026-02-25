"""Tests for editor discovery and caching."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from build_unity_project.editor_discovery import (
    _is_valid_editors_dir,
    load_editors_cache,
    prompt_and_discover,
    save_editors_cache,
    search_drive_for_editors,
)


def _make_version_dir(base: Path, version: str = "6000.3.7f1") -> Path:
    """Create a fake Unity version directory with Editor/Unity.exe."""
    editor_dir = base / version / "Editor"
    editor_dir.mkdir(parents=True)
    exe = editor_dir / "Unity.exe"
    exe.write_bytes(b"fake")
    return base


# --- _is_valid_editors_dir ---


def test_is_valid_editors_dir_true(tmp_path: Path) -> None:
    _make_version_dir(tmp_path)
    assert _is_valid_editors_dir(tmp_path) is True


def test_is_valid_editors_dir_empty(tmp_path: Path) -> None:
    assert _is_valid_editors_dir(tmp_path) is False


def test_is_valid_editors_dir_no_exe(tmp_path: Path) -> None:
    (tmp_path / "6000.3.7f1" / "Editor").mkdir(parents=True)
    assert _is_valid_editors_dir(tmp_path) is False


# --- load_editors_cache ---


def test_load_cache_valid(tmp_path: Path) -> None:
    editors = _make_version_dir(tmp_path / "Editors")
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(
        json.dumps({"unity_editors_path": str(editors), "found_at": "2026-01-01T00:00:00"}),
        encoding="utf-8",
    )
    assert load_editors_cache(cache_file) == editors


def test_load_cache_missing_file(tmp_path: Path) -> None:
    assert load_editors_cache(tmp_path / "nonexistent.json") is None


def test_load_cache_stale_path(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(
        json.dumps(
            {"unity_editors_path": str(tmp_path / "gone"), "found_at": "2026-01-01T00:00:00"}
        ),
        encoding="utf-8",
    )
    assert load_editors_cache(cache_file) is None


def test_load_cache_invalid_json(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    cache_file.write_text("{bad json", encoding="utf-8")
    assert load_editors_cache(cache_file) is None


def test_load_cache_no_versions(tmp_path: Path) -> None:
    editors = tmp_path / "Editors"
    editors.mkdir()
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(
        json.dumps({"unity_editors_path": str(editors), "found_at": "2026-01-01T00:00:00"}),
        encoding="utf-8",
    )
    assert load_editors_cache(cache_file) is None


# --- save_editors_cache ---


def test_save_cache(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    editors = tmp_path / "Editors"
    save_editors_cache(cache_file, editors)

    data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert data["unity_editors_path"] == str(editors)
    assert "found_at" in data


# --- search_drive_for_editors ---


def test_search_drive_finds_standard_location(tmp_path: Path) -> None:
    editors_path = Path("C:/Program Files/Unity/Hub/Editor")

    with (
        patch(
            "build_unity_project.editor_discovery._is_valid_editors_dir",
            side_effect=lambda p: p == editors_path,
        ),
        patch("builtins.print"),
    ):
        result = search_drive_for_editors("C")
    assert result == editors_path


def test_search_drive_nothing_found(tmp_path: Path) -> None:
    with (
        patch("build_unity_project.editor_discovery._is_valid_editors_dir", return_value=False),
        patch("build_unity_project.editor_discovery._safe_iterdir", return_value=[]),
        patch("builtins.print"),
    ):
        result = search_drive_for_editors("Z")
    assert result is None


# --- prompt_and_discover ---


def test_prompt_and_discover_first_try(tmp_path: Path) -> None:
    editors = tmp_path / "Editors"
    editors.mkdir()

    with (
        patch("builtins.input", return_value="C"),
        patch(
            "build_unity_project.editor_discovery.search_drive_for_editors",
            return_value=editors,
        ),
        patch("builtins.print"),
    ):
        result = prompt_and_discover()
    assert result == editors


def test_prompt_and_discover_retry(tmp_path: Path) -> None:
    editors = tmp_path / "Editors"
    editors.mkdir()

    inputs = iter(["C", "y", "D"])
    returns = iter([None, editors])

    with (
        patch("builtins.input", side_effect=lambda _: next(inputs)),
        patch(
            "build_unity_project.editor_discovery.search_drive_for_editors",
            side_effect=lambda _: next(returns),
        ),
        patch("builtins.print"),
    ):
        result = prompt_and_discover()
    assert result == editors


def test_prompt_and_discover_user_gives_up() -> None:
    inputs = iter(["C", "n"])

    with (
        patch("builtins.input", side_effect=lambda _: next(inputs)),
        patch(
            "build_unity_project.editor_discovery.search_drive_for_editors",
            return_value=None,
        ),
        patch("builtins.print"),
        pytest.raises(FileNotFoundError, match="Could not find any Unity Editor"),
    ):
        prompt_and_discover()
