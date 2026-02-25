"""Unity executable discovery and build execution."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from build_unity_project.config import BuildConfig
from build_unity_project.constants import (
    BUILD_TIMEOUT_SECONDS,
    ENV_BUILD_OUTPUT_PATH,
    ENV_BUILD_SCENES,
    ERROR_BUILD_TIMEOUT,
    ERROR_UNITY_EDITORS_NOT_FOUND,
    ERROR_UNITY_NOT_FOUND,
    UNITY_BATCHMODE,
    UNITY_BUILD_TARGET,
    UNITY_EXE_NAME,
    UNITY_EXECUTE_METHOD,
    UNITY_LOG_FILE,
    UNITY_NOGRAPHICS,
    UNITY_PROJECT_PATH,
    UNITY_QUIT,
)


def find_unity_executable(config: BuildConfig) -> Path:
    """Construct path to Unity executable and validate it exists."""
    if config.unity_editors_path is None:
        raise ValueError("unity_editors_path must be resolved before finding executable")
    if not config.unity_editors_path.exists():
        raise FileNotFoundError(
            ERROR_UNITY_EDITORS_NOT_FOUND.format(path=config.unity_editors_path)
        )

    unity_exe = config.unity_editors_path / config.unity_version / "Editor" / UNITY_EXE_NAME
    if not unity_exe.exists():
        available = [d.name for d in config.unity_editors_path.iterdir() if d.is_dir()]
        msg = ERROR_UNITY_NOT_FOUND.format(path=unity_exe)
        if available:
            msg += f"\nAvailable versions: {', '.join(sorted(available))}"
        raise FileNotFoundError(msg)

    return unity_exe


def build_unity_command(
    unity_exe: Path,
    config: BuildConfig,
    output_apk: Path,
    log_path: Path,
) -> list[str]:
    """Build the command-line arguments for the Unity process."""
    return [
        str(unity_exe),
        UNITY_BATCHMODE,
        UNITY_QUIT,
        UNITY_NOGRAPHICS,
        UNITY_PROJECT_PATH,
        str(config.project_path),
        UNITY_BUILD_TARGET,
        config.build_target,
        UNITY_EXECUTE_METHOD,
        config.build_script_method,
        UNITY_LOG_FILE,
        str(log_path),
    ]


def run_unity_build(
    unity_exe: Path,
    config: BuildConfig,
    output_apk: Path,
    log_path: Path,
) -> int:
    """Run Unity in batchmode to build the project. Returns the exit code."""
    cmd = build_unity_command(unity_exe, config, output_apk, log_path)

    env = os.environ.copy()
    env[ENV_BUILD_OUTPUT_PATH] = str(output_apk)
    env[ENV_BUILD_SCENES] = ";".join(config.scenes)

    try:
        result = subprocess.run(
            cmd,
            env=env,
            timeout=BUILD_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        minutes = BUILD_TIMEOUT_SECONDS // 60
        raise TimeoutError(ERROR_BUILD_TIMEOUT.format(minutes=minutes)) from None

    return result.returncode
