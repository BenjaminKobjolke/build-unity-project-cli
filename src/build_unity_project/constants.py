"""Centralized string constants for the build tool."""

# Error messages
ERROR_CONFIG_MISSING = "Configuration file not found: {path}"
ERROR_CONFIG_FIELD_MISSING = "Required config field missing: {field}"
ERROR_UNITY_NOT_FOUND = "Unity executable not found: {path}"
ERROR_UNITY_EDITORS_NOT_FOUND = "Unity editors directory not found: {path}"
ERROR_PROJECT_NOT_FOUND = "Unity project not found: {path}"
ERROR_OUTPUT_FOLDER_NOT_FOUND = "Output folder not found: {path}"
ERROR_BUILD_FAILED = "Unity build failed with exit code {code}. Check log: {log}"
ERROR_APK_NOT_FOUND = "Build completed but APK not found: {path}"
ERROR_BUILD_TIMEOUT = "Unity build timed out after {minutes} minutes"
ERROR_PROJECT_LOCKED = (
    "Unity project is locked — close the Unity editor before building.\n"
    "Lock file: {path}"
)

# Log tail settings
LOG_TAIL_LINES = 20
ERROR_INVALID_INCREMENT = "Invalid increment type: {value}. Must be one of: major, minor, patch"

# File patterns
APK_VERSION_PATTERN = r"^{prefix}_v(\d+)\.(\d+)\.(\d+)\.apk$"

# Unity CLI flags
UNITY_BATCHMODE = "-batchmode"
UNITY_QUIT = "-quit"
UNITY_NOGRAPHICS = "-nographics"
UNITY_PROJECT_PATH = "-projectPath"
UNITY_EXECUTE_METHOD = "-executeMethod"
UNITY_LOG_FILE = "-logFile"
UNITY_BUILD_TARGET = "-buildTarget"

# Environment variable names
ENV_BUILD_OUTPUT_PATH = "BUILD_OUTPUT_PATH"
ENV_BUILD_SCENES = "BUILD_SCENES"

# Build settings
BUILD_TIMEOUT_SECONDS = 3600
UNITY_EXE_NAME = "Unity.exe"
BUILD_SCRIPT_FILENAME = "BuildScript.cs"
EDITOR_FOLDER_NAME = "Editor"

# File-trigger build mode
TRIGGER_FILENAME = "build_trigger.json"
RESULT_FILENAME = "build_result.json"
TRIGGER_POLL_INTERVAL = 2  # seconds
WATCHER_SCRIPT_FILENAME = "BuildTriggerWatcher.cs"
ERROR_EDITOR_NOT_RUNNING = (
    "Trigger mode requires the Unity editor to be running, "
    "but no lock file was found.\nExpected: {path}"
)
