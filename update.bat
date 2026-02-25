@echo off
echo Updating dependencies...
uv lock --upgrade
if errorlevel 1 (
    echo Update failed!
    pause
    exit /b 1
)

uv sync --all-extras
if errorlevel 1 (
    echo Sync failed!
    pause
    exit /b 1
)

echo.
echo Running linter...
uv run ruff check src/ tests/
if errorlevel 1 (
    echo Lint failed!
    pause
    exit /b 1
)

echo.
echo Running tests...
uv run pytest tests/ -v
if errorlevel 1 (
    echo Tests failed!
    pause
    exit /b 1
)

echo.
echo Update complete!
pause
