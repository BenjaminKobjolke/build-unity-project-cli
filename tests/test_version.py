"""Tests for version detection and increment logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from build_unity_project.version import (
    Version,
    build_apk_filename,
    detect_latest_version,
    increment_version,
)


def test_version_str() -> None:
    assert str(Version(1, 2, 3)) == "1.2.3"
    assert str(Version(0, 0, 0)) == "0.0.0"


def test_detect_latest_version(tmp_path: Path) -> None:
    (tmp_path / "myapp_v0.1.0.apk").touch()
    (tmp_path / "myapp_v0.1.1.apk").touch()
    (tmp_path / "myapp_v0.1.5.apk").touch()
    (tmp_path / "myapp_v0.1.3.apk").touch()
    (tmp_path / "unrelated.txt").touch()

    result = detect_latest_version(tmp_path, "myapp")
    assert result == Version(0, 1, 5)


def test_detect_latest_version_no_apks(tmp_path: Path) -> None:
    (tmp_path / "unrelated.txt").touch()
    assert detect_latest_version(tmp_path, "myapp") is None


def test_detect_latest_version_empty_folder(tmp_path: Path) -> None:
    assert detect_latest_version(tmp_path, "myapp") is None


def test_detect_latest_version_nonexistent_folder(tmp_path: Path) -> None:
    assert detect_latest_version(tmp_path / "nope", "myapp") is None


def test_detect_latest_version_different_prefix(tmp_path: Path) -> None:
    (tmp_path / "other_v1.0.0.apk").touch()
    assert detect_latest_version(tmp_path, "myapp") is None


def test_increment_patch() -> None:
    assert increment_version(Version(0, 1, 5), "patch") == Version(0, 1, 6)


def test_increment_minor() -> None:
    assert increment_version(Version(0, 1, 5), "minor") == Version(0, 2, 0)


def test_increment_major() -> None:
    assert increment_version(Version(0, 1, 5), "major") == Version(1, 0, 0)


def test_increment_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid increment type"):
        increment_version(Version(0, 1, 0), "invalid")


def test_build_apk_filename() -> None:
    assert build_apk_filename("siemens-vr", Version(0, 1, 6)) == "siemens-vr_v0.1.6.apk"


def test_build_apk_filename_major() -> None:
    assert build_apk_filename("app", Version(2, 0, 0)) == "app_v2.0.0.apk"
