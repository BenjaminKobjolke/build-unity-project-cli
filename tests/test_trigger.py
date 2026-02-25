"""Tests for file-trigger build mode."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from build_unity_project.constants import RESULT_FILENAME, TRIGGER_FILENAME
from build_unity_project.trigger import focus_unity_editor, poll_result, write_trigger


def test_focus_unity_editor_no_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """focus_unity_editor does not crash when no Unity window exists."""
    monkeypatch.setattr("build_unity_project.trigger.sys.platform", "win32")

    mock_user32 = MagicMock()
    mock_user32.FindWindowW.return_value = 0  # no window found

    mock_windll = MagicMock()
    mock_windll.user32 = mock_user32

    with patch("build_unity_project.trigger.ctypes") as mock_ctypes:
        mock_ctypes.windll = mock_windll
        focus_unity_editor()

    mock_user32.FindWindowW.assert_called_once_with("UnityContainerWndClass", None)
    mock_user32.SetForegroundWindow.assert_not_called()


def test_focus_unity_editor_window_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """focus_unity_editor calls SetForegroundWindow when a Unity window exists."""
    monkeypatch.setattr("build_unity_project.trigger.sys.platform", "win32")

    mock_user32 = MagicMock()
    mock_user32.FindWindowW.return_value = 12345

    mock_windll = MagicMock()
    mock_windll.user32 = mock_user32

    with patch("build_unity_project.trigger.ctypes") as mock_ctypes:
        mock_ctypes.windll = mock_windll
        focus_unity_editor()

    mock_user32.FindWindowW.assert_called_once_with("UnityContainerWndClass", None)
    mock_user32.SetForegroundWindow.assert_called_once_with(12345)


def test_focus_unity_editor_noop_on_non_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """focus_unity_editor is a no-op on non-Windows platforms."""
    monkeypatch.setattr("build_unity_project.trigger.sys.platform", "linux")

    with patch("build_unity_project.trigger.ctypes") as mock_ctypes:
        focus_unity_editor()

    mock_ctypes.windll.user32.FindWindowW.assert_not_called()


def test_write_trigger(tmp_path: Path) -> None:
    output_apk = tmp_path / "output" / "test_v0.1.0.apk"
    scenes = ["Assets/Scenes/Main.unity", "Assets/Scenes/Menu.unity"]
    build_target = "Android"

    with patch("build_unity_project.trigger.focus_unity_editor"):
        write_trigger(tmp_path, output_apk, scenes, build_target)

    trigger_file = tmp_path / TRIGGER_FILENAME
    assert trigger_file.exists()

    data = json.loads(trigger_file.read_text(encoding="utf-8"))
    assert data["output_path"] == str(output_apk)
    assert data["scenes"] == scenes
    assert data["build_target"] == build_target


def test_poll_result_success(tmp_path: Path) -> None:
    result_data = {"success": True, "error": "", "duration_seconds": 42.5}
    result_file = tmp_path / RESULT_FILENAME
    result_file.write_text(json.dumps(result_data), encoding="utf-8")

    result = poll_result(tmp_path, timeout=5)

    assert result["success"] is True
    assert result["error"] == ""
    assert result["duration_seconds"] == 42.5
    assert not result_file.exists()


def test_poll_result_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("build_unity_project.trigger.TRIGGER_POLL_INTERVAL", 0.1)

    with pytest.raises(TimeoutError, match="Build result not received"):
        poll_result(tmp_path, timeout=1)


def test_poll_result_delayed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Result file appears after a short delay — poll should pick it up."""
    monkeypatch.setattr("build_unity_project.trigger.TRIGGER_POLL_INTERVAL", 0.1)

    result_data = {"success": False, "error": "Compilation error", "duration_seconds": 3.0}
    result_file = tmp_path / RESULT_FILENAME

    def _write_delayed() -> None:
        time.sleep(0.3)
        result_file.write_text(json.dumps(result_data), encoding="utf-8")

    thread = threading.Thread(target=_write_delayed)
    thread.start()

    result = poll_result(tmp_path, timeout=5)
    thread.join()

    assert result["success"] is False
    assert result["error"] == "Compilation error"
    assert not result_file.exists()
