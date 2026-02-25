@echo off
echo Installing dependencies...
uv sync --all-extras
if errorlevel 1 (
    echo Installation failed!
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
echo Installation complete!
pause
