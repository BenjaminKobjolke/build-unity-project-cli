# CLAUDE.md — Coding Rules

## Common Rules
- Write clean, readable code
- No unused imports or variables
- Keep functions short and focused
- Use meaningful variable and function names
- Handle errors explicitly, never silently swallow exceptions
- Write tests for all new functionality

## Python Rules
- Use type hints on all function signatures
- Use `pathlib.Path` instead of `os.path`
- Use dataclasses for structured data
- Use `subprocess.run` (not `Popen`) for external commands
- Format with `ruff format`, lint with `ruff check`
- Strict mypy compliance
- No runtime dependencies — stdlib only
- Tests use `pytest` with `tmp_path` fixtures and `unittest.mock`
