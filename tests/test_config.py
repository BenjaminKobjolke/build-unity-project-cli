"""Tests for config loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from build_unity_project.config import BuildConfig, load_config


def _write_config(tmp_path: Path, data: dict, project: bool = True, output: bool = True) -> Path:
    """Helper to write a config.json and create required directories."""
    if project:
        project_path = tmp_path / "project"
        project_path.mkdir()
        data.setdefault("project_path", str(project_path))

    if output:
        output_path = tmp_path / "output"
        output_path.mkdir()
        data.setdefault("output_folder", str(output_path))

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(data), encoding="utf-8")
    return config_file


def _valid_data(tmp_path: Path) -> dict:
    """Return a valid config dict (without paths — those are set by _write_config)."""
    return {
        "unity_version": "6000.3.7f1",
        "unity_editors_path": str(tmp_path),
        "scenes": ["Assets/Scenes/Main.unity"],
        "build_target": "Android",
        "apk_prefix": "test-app",
        "version_increment": "patch",
        "build_script_method": "BuildAutomation.BuildScript.BuildAndroid",
        "log_folder": "logs",
    }


def test_load_valid_config(tmp_path: Path) -> None:
    data = _valid_data(tmp_path)
    config_file = _write_config(tmp_path, data)
    config = load_config(config_file)

    assert isinstance(config, BuildConfig)
    assert config.unity_version == "6000.3.7f1"
    assert config.build_target == "Android"
    assert config.scenes == ["Assets/Scenes/Main.unity"]
    assert config.apk_prefix == "test-app"


def test_load_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config(tmp_path / "nonexistent.json")


def test_load_config_missing_field(tmp_path: Path) -> None:
    data = _valid_data(tmp_path)
    del data["unity_version"]
    config_file = _write_config(tmp_path, data)

    with pytest.raises(ValueError, match="Required config field missing: unity_version"):
        load_config(config_file)


def test_load_config_missing_project_path(tmp_path: Path) -> None:
    data = _valid_data(tmp_path)
    data["project_path"] = str(tmp_path / "nonexistent_project")
    config_file = _write_config(tmp_path, data, project=False)

    with pytest.raises(FileNotFoundError, match="Unity project not found"):
        load_config(config_file)


def test_load_config_missing_output_folder(tmp_path: Path) -> None:
    data = _valid_data(tmp_path)
    data["output_folder"] = str(tmp_path / "nonexistent_output")
    config_file = _write_config(tmp_path, data, output=False)

    with pytest.raises(FileNotFoundError, match="Output folder not found"):
        load_config(config_file)
