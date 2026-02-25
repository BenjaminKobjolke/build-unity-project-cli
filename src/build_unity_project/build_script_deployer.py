"""Deploy and cleanup the Unity build script."""

from __future__ import annotations

import shutil
from pathlib import Path

from build_unity_project.config import BuildConfig
from build_unity_project.constants import (
    BUILD_SCRIPT_FILENAME,
    EDITOR_FOLDER_NAME,
    WATCHER_SCRIPT_FILENAME,
)

# Paths to C# scripts relative to the package
_SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent / "unity_build_script"
_SCRIPT_SOURCE = _SCRIPT_DIR / BUILD_SCRIPT_FILENAME
_WATCHER_SOURCE = _SCRIPT_DIR / WATCHER_SCRIPT_FILENAME


def deploy(config: BuildConfig) -> Path:
    """Copy BuildScript.cs into the Unity project's Assets/Editor/ folder."""
    editor_dir = config.project_path / "Assets" / EDITOR_FOLDER_NAME
    editor_dir.mkdir(parents=True, exist_ok=True)

    dest = editor_dir / BUILD_SCRIPT_FILENAME
    shutil.copy2(_SCRIPT_SOURCE, dest)
    return dest


def cleanup(dest: Path) -> None:
    """Remove the deployed build script and its .meta file."""
    if dest.exists():
        dest.unlink()

    meta = dest.with_suffix(dest.suffix + ".meta")
    if meta.exists():
        meta.unlink()


def deploy_watcher(config: BuildConfig) -> Path:
    """Copy BuildTriggerWatcher.cs into the Unity project's Assets/Editor/ folder."""
    editor_dir = config.project_path / "Assets" / EDITOR_FOLDER_NAME
    editor_dir.mkdir(parents=True, exist_ok=True)

    dest = editor_dir / WATCHER_SCRIPT_FILENAME
    shutil.copy2(_WATCHER_SOURCE, dest)
    return dest


def cleanup_watcher(dest: Path) -> None:
    """Remove the deployed watcher script and its .meta file."""
    cleanup(dest)
