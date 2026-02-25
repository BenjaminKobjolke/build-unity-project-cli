"""CLI entrypoint for the Unity build tool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from build_unity_project import build_script_deployer
from build_unity_project.config import BuildConfig, load_config
from build_unity_project.constants import (
    BUILD_TIMEOUT_SECONDS,
    EDITORS_CACHE_FILENAME,
    ERROR_APK_NOT_FOUND,
    ERROR_BUILD_FAILED,
    ERROR_EDITOR_NOT_RUNNING,
    ERROR_PROJECT_LOCKED,
    LOG_TAIL_LINES,
)
from build_unity_project.editor_discovery import (
    load_editors_cache,
    prompt_and_discover,
    save_editors_cache,
)
from build_unity_project.trigger import poll_result, write_trigger
from build_unity_project.unity import find_unity_executable, run_unity_build
from build_unity_project.version import (
    Version,
    build_apk_filename,
    detect_latest_version,
    increment_version,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Build a Unity project from the command line.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Path to config.json (default: config.json)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        dest="explicit_version",
        help="Explicit version to build (e.g. 1.0.0)",
    )
    parser.add_argument(
        "--increment",
        type=str,
        default=None,
        choices=["major", "minor", "patch"],
        help="Version increment type (overrides config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print build plan without executing",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=["auto", "batchmode", "trigger"],
        help="Build mode: auto (default), batchmode, or trigger",
    )
    return parser.parse_args(argv)


def resolve_version(
    explicit_version: str | None,
    increment_type: str,
    output_folder: Path,
    apk_prefix: str,
) -> Version:
    """Determine the build version from explicit value or auto-increment."""
    if explicit_version:
        parts = explicit_version.split(".")
        if len(parts) != 3:
            print(f"Error: Invalid version format '{explicit_version}'. Expected X.Y.Z")
            sys.exit(1)
        return Version(int(parts[0]), int(parts[1]), int(parts[2]))

    latest = detect_latest_version(output_folder, apk_prefix)
    if latest is None:
        print("No existing APKs found. Starting at version 0.1.0")
        return Version(0, 1, 0)

    print(f"Latest version found: {latest}")
    new_version = increment_version(latest, increment_type)
    print(f"Incrementing ({increment_type}): {latest} -> {new_version}")
    return new_version


def main(argv: list[str] | None = None) -> None:
    """Main CLI flow."""
    args = parse_args(argv)

    # Load config
    config = load_config(args.config)

    if config.unity_editors_path is None:
        from dataclasses import replace

        cache_path = args.config.resolve().parent / EDITORS_CACHE_FILENAME
        cached = load_editors_cache(cache_path)
        if cached is not None:
            print(f"Using cached Unity editors path: {cached}")
            editors_path = cached
        else:
            editors_path = prompt_and_discover()
            save_editors_cache(cache_path, editors_path)
        config = replace(config, unity_editors_path=editors_path)

    print(f"Project: {config.project_path}")
    print(f"Unity: {config.unity_version}")

    # Find Unity
    unity_exe = find_unity_executable(config)
    print(f"Unity executable: {unity_exe}")

    # Resolve version
    increment_type = args.increment or config.version_increment
    version = resolve_version(
        args.explicit_version, increment_type, config.output_folder, config.apk_prefix
    )
    apk_filename = build_apk_filename(config.apk_prefix, version)
    output_apk = config.output_folder / apk_filename
    print(f"Output: {output_apk}")

    # Resolve build mode: CLI flag > config > "auto"
    effective_mode = args.mode or config.build_mode
    lock_file = config.project_path / "Temp" / "UnityLockfile"
    editor_running = lock_file.exists()

    if effective_mode == "auto":
        effective_mode = "trigger" if editor_running else "batchmode"

    print(f"Build mode: {effective_mode}")

    # Dry run
    if args.dry_run:
        print("\n--- DRY RUN ---")
        print(f"Would build: {apk_filename}")
        print(f"Unity: {unity_exe}")
        print(f"Project: {config.project_path}")
        print(f"Scenes: {', '.join(config.scenes)}")
        print(f"Target: {config.build_target}")
        print(f"Output: {output_apk}")
        return

    if effective_mode == "batchmode":
        _build_batchmode(config, unity_exe, output_apk, version, editor_running, lock_file)
    else:
        _build_trigger(config, output_apk)

    # Verify
    if not output_apk.exists():
        print(ERROR_APK_NOT_FOUND.format(path=output_apk))
        sys.exit(1)

    size_mb = output_apk.stat().st_size / (1024 * 1024)
    print("\nBuild successful!")
    print(f"APK: {output_apk}")
    print(f"Size: {size_mb:.1f} MB")


def _build_batchmode(
    config: BuildConfig,
    unity_exe: Path,
    output_apk: Path,
    version: Version,
    editor_running: bool,
    lock_file: Path,
) -> None:
    """Run the build via Unity batchmode (editor must be closed)."""
    if editor_running:
        print(ERROR_PROJECT_LOCKED.format(path=lock_file))
        sys.exit(1)

    log_dir = Path(config.log_folder).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"build_{version}.log"

    print("\nDeploying build script...")
    dest = build_script_deployer.deploy(config)

    try:
        print("Starting Unity build (this may take a while)...")
        print(f"Log: {log_path}")
        exit_code = run_unity_build(unity_exe, config, output_apk, log_path)
    finally:
        print("Cleaning up build script...")
        build_script_deployer.cleanup(dest)

    if exit_code != 0:
        print(ERROR_BUILD_FAILED.format(code=exit_code, log=log_path))
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            tail = lines[-LOG_TAIL_LINES:] if len(lines) > LOG_TAIL_LINES else lines
            print(f"\n--- Last {len(tail)} lines of build log ---")
            for line in tail:
                print(line)
        sys.exit(exit_code)


def _build_trigger(config: BuildConfig, output_apk: Path) -> None:
    """Run the build via file-trigger (editor must be running)."""
    lock_file = config.project_path / "Temp" / "UnityLockfile"
    if not lock_file.exists():
        print(ERROR_EDITOR_NOT_RUNNING.format(path=lock_file))
        sys.exit(1)

    print("\nDeploying trigger watcher script...")
    watcher_dest = build_script_deployer.deploy_watcher(config)

    try:
        print("Writing build trigger...")
        write_trigger(config.project_path, output_apk, config.scenes, config.build_target)

        print(f"Waiting for build result (timeout: {BUILD_TIMEOUT_SECONDS}s)...")
        result = poll_result(config.project_path, BUILD_TIMEOUT_SECONDS)
    finally:
        print("Cleaning up watcher script...")
        build_script_deployer.cleanup_watcher(watcher_dest)

    if not result.get("success"):
        error_msg = result.get("error", "Unknown error")
        duration = result.get("duration_seconds", 0)
        print(f"Build failed after {duration:.1f}s: {error_msg}")
        sys.exit(1)

    duration = result.get("duration_seconds", 0)
    print(f"Editor build completed in {duration:.1f}s")


if __name__ == "__main__":
    main()
