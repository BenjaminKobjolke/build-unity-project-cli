"""Build configuration loader."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from build_unity_project.constants import (
    ERROR_CONFIG_FIELD_MISSING,
    ERROR_CONFIG_MISSING,
    ERROR_OUTPUT_FOLDER_NOT_FOUND,
    ERROR_PROJECT_NOT_FOUND,
)

REQUIRED_FIELDS = [
    "unity_version",
    "unity_editors_path",
    "project_path",
    "scenes",
    "build_target",
    "output_folder",
    "apk_prefix",
    "version_increment",
    "build_script_method",
    "log_folder",
]


@dataclass(frozen=True)
class BuildConfig:
    """Typed build configuration."""

    unity_version: str
    unity_editors_path: Path
    project_path: Path
    scenes: list[str]
    build_target: str
    output_folder: Path
    apk_prefix: str
    version_increment: str
    build_script_method: str
    log_folder: str
    build_mode: str = "auto"


def load_config(path: Path) -> BuildConfig:
    """Load and validate build configuration from JSON file."""
    if not path.exists():
        raise FileNotFoundError(ERROR_CONFIG_MISSING.format(path=path))

    data = json.loads(path.read_text(encoding="utf-8"))

    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(ERROR_CONFIG_FIELD_MISSING.format(field=field))

    project_path = Path(data["project_path"])
    if not project_path.exists():
        raise FileNotFoundError(ERROR_PROJECT_NOT_FOUND.format(path=project_path))

    output_folder = Path(data["output_folder"])
    if not output_folder.exists():
        raise FileNotFoundError(ERROR_OUTPUT_FOLDER_NOT_FOUND.format(path=output_folder))

    return BuildConfig(
        unity_version=data["unity_version"],
        unity_editors_path=Path(data["unity_editors_path"]),
        project_path=project_path,
        scenes=data["scenes"],
        build_target=data["build_target"],
        output_folder=output_folder,
        apk_prefix=data["apk_prefix"],
        version_increment=data["version_increment"],
        build_script_method=data["build_script_method"],
        log_folder=data["log_folder"],
        build_mode=data.get("build_mode", "auto"),
    )
