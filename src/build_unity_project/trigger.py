"""File-trigger build mode: communicate with a running Unity editor via JSON files."""

from __future__ import annotations

import ctypes
import json
import sys
import time
from pathlib import Path

from build_unity_project.constants import (
    RESULT_FILENAME,
    TRIGGER_FILENAME,
    TRIGGER_POLL_INTERVAL,
)


def focus_unity_editor() -> None:
    """Bring the Unity editor window to the foreground on Windows.

    Uses the known Unity window class to find and focus the editor.
    No-op on non-Windows platforms.
    """
    if sys.platform != "win32":
        return

    user32 = ctypes.windll.user32
    hwnd: int = user32.FindWindowW("UnityContainerWndClass", None)
    if hwnd:
        user32.SetForegroundWindow(hwnd)


def write_trigger(
    project_path: Path,
    output_apk: Path,
    scenes: list[str],
    build_target: str,
) -> None:
    """Write a build_trigger.json file for the Unity editor to pick up."""
    trigger_path = project_path / TRIGGER_FILENAME
    payload = {
        "output_path": str(output_apk),
        "scenes": scenes,
        "build_target": build_target,
    }
    trigger_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    focus_unity_editor()


def poll_result(project_path: Path, timeout: int) -> dict[str, object]:
    """Poll for build_result.json until it appears or timeout is reached.

    Returns the parsed JSON dict on success.
    Raises TimeoutError if the result file does not appear in time.
    """
    result_path = project_path / RESULT_FILENAME
    elapsed = 0

    while elapsed < timeout:
        if result_path.exists():
            data: dict[str, object] = json.loads(result_path.read_text(encoding="utf-8"))
            result_path.unlink()
            return data
        time.sleep(TRIGGER_POLL_INTERVAL)
        elapsed += TRIGGER_POLL_INTERVAL

    raise TimeoutError(
        f"Build result not received within {timeout} seconds. Expected: {result_path}"
    )
