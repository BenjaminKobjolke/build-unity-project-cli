# build-unity-project-cli

CLI tool to automate Unity project builds from the command line. Supports two build modes — **batchmode** (editor closed) and **trigger** (editor running) — with automatic version detection and incrementing.

## Features

- Two build modes with auto-detection based on editor state
- Semantic version auto-detection from existing APK filenames
- Version incrementing (patch / minor / major)
- Dry-run mode to preview build plans
- Zero runtime dependencies (stdlib only)
- Automatic C# build script deployment and cleanup

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Unity Hub with the target Unity version installed

## Setup

```bash
install.bat
```

This installs dependencies and runs the test suite to verify the installation.

## Usage

```bash
start.bat                                   # Build with auto-increment (patch)
uv run build-unity --version 1.0.0          # Explicit version
uv run build-unity --increment minor        # Increment minor version
uv run build-unity --increment major        # Increment major version
uv run build-unity --dry-run                # Preview without building
uv run build-unity --mode batchmode         # Force batchmode
uv run build-unity --mode trigger           # Force trigger mode
uv run build-unity --config custom.json     # Custom config path
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--config PATH` | Path to config file (default: `config.json`) |
| `--version X.Y.Z` | Build with an explicit version |
| `--increment TYPE` | Override increment type: `major`, `minor`, `patch` |
| `--mode MODE` | Force build mode: `auto`, `batchmode`, `trigger` |
| `--dry-run` | Print the build plan without executing |

## Configuration

Create a `config.json` in the project root:

```json
{
    "unity_version": "6000.3.7f1",
    "unity_editors_path": "C:/Program Files/Unity/Hub/Editor",
    "project_path": "E:/GIT/my-unity-project",
    "scenes": ["Assets/Scenes/Main.unity"],
    "build_target": "Android",
    "output_folder": "E:/builds/output",
    "apk_prefix": "myapp",
    "version_increment": "patch",
    "build_script_method": "BuildAutomation.BuildScript.BuildAndroid",
    "log_folder": "logs",
    "build_mode": "auto"
}
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `unity_version` | Yes | Unity editor version (e.g. `6000.3.7f1`) |
| `unity_editors_path` | Yes | Path to Unity Hub editors directory |
| `project_path` | Yes | Path to the Unity project root (must exist) |
| `scenes` | Yes | List of scene paths to include in the build |
| `build_target` | Yes | Target platform (e.g. `Android`, `StandaloneWindows64`) |
| `output_folder` | Yes | Directory for built APKs (must exist) |
| `apk_prefix` | Yes | Filename prefix (e.g. `myapp` produces `myapp_v1.0.0.apk`) |
| `version_increment` | Yes | Default increment type: `patch`, `minor`, or `major` |
| `build_script_method` | Yes | Fully qualified C# build method |
| `log_folder` | Yes | Directory for build logs (created if missing) |
| `build_mode` | No | `auto` (default), `batchmode`, or `trigger` |

## Build Modes

### Auto (default)

Detects whether the Unity editor is running by checking for `Temp/UnityLockfile` in the project directory. Uses **trigger** mode if the editor is open, **batchmode** if it is closed.

### Batchmode

Requires the Unity editor to be **closed**. Deploys `BuildScript.cs` into the project's `Assets/Editor/` folder, launches Unity in headless mode (`-batchmode -quit -nographics`), and reads the result from the process exit code. The build script and its `.meta` file are cleaned up afterward.

### Trigger

Requires the Unity editor to be **running**. Deploys `BuildTriggerWatcher.cs` into `Assets/Editor/`, writes a `build_trigger.json` file that the watcher picks up, then polls for a `build_result.json` response. On Windows, the tool automatically brings the Unity editor to the foreground so `EditorApplication.update` fires reliably.

## Version Management

Versions are auto-detected by scanning the output folder for APK files matching the pattern `{prefix}_v{major}.{minor}.{patch}.apk`. The highest version found is incremented according to the configured type:

```
patch:  0.1.5 -> 0.1.6
minor:  0.1.5 -> 0.2.0
major:  0.1.5 -> 1.0.0
```

If no existing APKs are found, the version starts at `0.1.0`.

## Project Structure

```
src/build_unity_project/
  __main__.py              # CLI entrypoint and build orchestration
  config.py                # Configuration loading and validation
  constants.py             # Error messages, filenames, Unity flags
  version.py               # Version detection and incrementing
  unity.py                 # Unity executable discovery and command building
  trigger.py               # Trigger mode: JSON file communication, window focus
  build_script_deployer.py # C# script deployment and cleanup

unity_build_script/
  BuildScript.cs           # Batchmode build executor (C#)
  BuildTriggerWatcher.cs   # Trigger mode file watcher (C#)

tests/                     # pytest test suite
```

## Development

```bash
tools\tests.bat            # Run tests
update.bat                 # Update deps + lint + tests
```

### Tooling

- **Formatter/Linter:** ruff
- **Type checker:** mypy (strict mode)
- **Tests:** pytest
