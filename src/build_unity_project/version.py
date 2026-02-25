"""Version detection and increment logic."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from build_unity_project.constants import APK_VERSION_PATTERN, ERROR_INVALID_INCREMENT


@dataclass(frozen=True)
class Version:
    """Semantic version."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def detect_latest_version(output_folder: Path, apk_prefix: str) -> Version | None:
    """Scan folder for APKs matching prefix and return the highest version found."""
    pattern = re.compile(APK_VERSION_PATTERN.format(prefix=re.escape(apk_prefix)))
    versions: list[Version] = []

    if not output_folder.exists():
        return None

    for file in output_folder.iterdir():
        match = pattern.match(file.name)
        if match:
            versions.append(
                Version(
                    major=int(match.group(1)),
                    minor=int(match.group(2)),
                    patch=int(match.group(3)),
                )
            )

    if not versions:
        return None

    return max(versions, key=lambda v: (v.major, v.minor, v.patch))


def increment_version(version: Version, increment_type: str) -> Version:
    """Return a new Version with the specified field incremented."""
    if increment_type == "patch":
        return Version(version.major, version.minor, version.patch + 1)
    if increment_type == "minor":
        return Version(version.major, version.minor + 1, 0)
    if increment_type == "major":
        return Version(version.major + 1, 0, 0)
    raise ValueError(ERROR_INVALID_INCREMENT.format(value=increment_type))


def build_apk_filename(prefix: str, version: Version) -> str:
    """Build APK filename from prefix and version."""
    return f"{prefix}_v{version}.apk"
