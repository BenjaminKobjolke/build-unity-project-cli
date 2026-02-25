"""Tests for Unity executable discovery and build command composition."""

from __future__ import annotations

from pathlib import Path

import pytest

from build_unity_project.config import BuildConfig
from build_unity_project.constants import (
    UNITY_BATCHMODE,
    UNITY_BUILD_TARGET,
    UNITY_EXECUTE_METHOD,
    UNITY_LOG_FILE,
    UNITY_NOGRAPHICS,
    UNITY_PROJECT_PATH,
    UNITY_QUIT,
)
from build_unity_project.unity import build_unity_command, find_unity_executable


def _make_config(tmp_path: Path, unity_version: str = "6000.3.7f1") -> BuildConfig:
    """Create a BuildConfig with paths under tmp_path."""
    editors = tmp_path / "editors"
    editors.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    output = tmp_path / "output"
    output.mkdir()

    return BuildConfig(
        unity_version=unity_version,
        unity_editors_path=editors,
        project_path=project,
        scenes=["Assets/Scenes/Main.unity"],
        build_target="Android",
        output_folder=output,
        apk_prefix="test",
        version_increment="patch",
        build_script_method="BuildAutomation.BuildScript.BuildAndroid",
        log_folder="logs",
    )


def test_find_unity_executable(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    editor_dir = config.unity_editors_path / config.unity_version / "Editor"
    editor_dir.mkdir(parents=True)
    unity_exe = editor_dir / "Unity.exe"
    unity_exe.touch()

    result = find_unity_executable(config)
    assert result == unity_exe


def test_find_unity_executable_missing_editors(tmp_path: Path) -> None:
    config = BuildConfig(
        unity_version="6000.3.7f1",
        unity_editors_path=tmp_path / "nonexistent",
        project_path=tmp_path,
        scenes=[],
        build_target="Android",
        output_folder=tmp_path,
        apk_prefix="test",
        version_increment="patch",
        build_script_method="Build.Method",
        log_folder="logs",
    )
    with pytest.raises(FileNotFoundError, match="Unity editors directory not found"):
        find_unity_executable(config)


def test_find_unity_executable_missing_version(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    # Don't create the version directory — should fail
    with pytest.raises(FileNotFoundError, match="Unity executable not found"):
        find_unity_executable(config)


def test_find_unity_executable_lists_available(tmp_path: Path) -> None:
    config = _make_config(tmp_path, unity_version="9999.0.0f1")
    (config.unity_editors_path / "2022.3.1f1").mkdir()
    (config.unity_editors_path / "6000.3.7f1").mkdir()

    with pytest.raises(FileNotFoundError, match="Available versions"):
        find_unity_executable(config)


def test_build_unity_command(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    unity_exe = tmp_path / "Unity.exe"
    output_apk = tmp_path / "test_v0.1.0.apk"
    log_path = tmp_path / "build.log"

    cmd = build_unity_command(unity_exe, config, output_apk, log_path)

    assert cmd[0] == str(unity_exe)
    assert UNITY_BATCHMODE in cmd
    assert UNITY_QUIT in cmd
    assert UNITY_NOGRAPHICS in cmd

    # Check flag-value pairs
    idx = cmd.index(UNITY_PROJECT_PATH)
    assert cmd[idx + 1] == str(config.project_path)

    idx = cmd.index(UNITY_BUILD_TARGET)
    assert cmd[idx + 1] == "Android"

    idx = cmd.index(UNITY_EXECUTE_METHOD)
    assert cmd[idx + 1] == "BuildAutomation.BuildScript.BuildAndroid"

    idx = cmd.index(UNITY_LOG_FILE)
    assert cmd[idx + 1] == str(log_path)
