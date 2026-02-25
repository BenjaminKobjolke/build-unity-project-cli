"""Auto-discover Unity Editor installations and cache results."""

from __future__ import annotations

import contextlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from build_unity_project.constants import (
    ERROR_UNITY_EDITORS_NOT_DISCOVERED,
    UNITY_EXE_NAME,
    UNITY_HUB_EDITOR_SUBPATH,
    UNITY_VERSION_DIR_PATTERN,
)

_VERSION_RE = re.compile(UNITY_VERSION_DIR_PATTERN)


def _is_valid_editors_dir(path: Path) -> bool:
    """Check if *path* contains at least one Unity version with an editor executable."""
    if not path.is_dir():
        return False
    for child in path.iterdir():
        if child.is_dir() and _VERSION_RE.match(child.name):
            exe = child / "Editor" / UNITY_EXE_NAME
            if exe.exists():
                return True
    return False


def search_drive_for_editors(drive_letter: str) -> Path | None:
    """Search a single drive for Unity Editor installations.

    Returns the first valid editors directory found, or ``None``.
    """
    drive = f"{drive_letter.upper()}:/"

    candidates: list[Path] = [
        Path(drive, "Program Files", UNITY_HUB_EDITOR_SUBPATH),
        Path(drive, "Program Files (x86)", UNITY_HUB_EDITOR_SUBPATH),
        Path(drive, UNITY_HUB_EDITOR_SUBPATH),
    ]

    for candidate in candidates:
        print(f"  Checking {candidate} ...")
        if _is_valid_editors_dir(candidate):
            return candidate

    print(f"  Scanning top-level directories on {drive} ...")
    drive_path = Path(drive)
    if not drive_path.exists():
        return None

    for top_dir in _safe_iterdir(drive_path):
        if not top_dir.is_dir():
            continue
        deep = top_dir / UNITY_HUB_EDITOR_SUBPATH
        if _is_valid_editors_dir(deep):
            return deep
        for sub_dir in _safe_iterdir(top_dir):
            if not sub_dir.is_dir():
                continue
            deep2 = sub_dir / UNITY_HUB_EDITOR_SUBPATH
            if _is_valid_editors_dir(deep2):
                return deep2

    return None


def _safe_iterdir(path: Path) -> list[Path]:
    """Iterate a directory, returning an empty list on permission errors."""
    try:
        return list(path.iterdir())
    except OSError:
        return []


def prompt_and_discover() -> Path:
    """Interactive loop: ask the user which drive to search."""
    while True:
        letter = input("Enter drive letter to search for Unity editors (e.g. C): ").strip()
        if not letter:
            continue

        print(f"Searching {letter.upper()}: for Unity editors ...")
        result = search_drive_for_editors(letter)

        if result is not None:
            print(f"Found Unity editors at: {result}")
            return result

        again = (
            input(f"Unity not found on {letter.upper()}:. Search another drive? (y/n): ")
            .strip()
            .lower()
        )
        if again != "y":
            raise FileNotFoundError(ERROR_UNITY_EDITORS_NOT_DISCOVERED)


def load_editors_cache(cache_path: Path) -> Path | None:
    """Load the cached Unity editors path if the cache file exists and is still valid."""
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        raw = data.get("unity_editors_path")
        if not raw:
            return None
        editors_path = Path(str(raw))
        if not _is_valid_editors_dir(editors_path):
            return None
        return editors_path
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_editors_cache(cache_path: Path, editors_path: Path) -> None:
    """Persist the discovered editors path to a JSON cache file."""
    payload = {
        "unity_editors_path": str(editors_path),
        "found_at": datetime.now(tz=UTC).isoformat(),
    }
    with contextlib.suppress(OSError):
        cache_path.write_text(json.dumps(payload, indent=4), encoding="utf-8")
