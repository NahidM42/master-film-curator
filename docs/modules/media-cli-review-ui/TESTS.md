# Verification — Typer CLI and Optional Textual Review

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_cli_tui.py tests/test_end_to_end.py
```

Coverage: Empty queue, noninteractive scripts, rejected confirmation, alternate candidate, absent ffprobe, missing optional Textual and unknown file IDs.

Failure contract: Invalid config and expected filesystem/validation/database errors produce exit 1; apply partial_failure and incomplete rollback also exit 1. Missing optional TUI gives install command.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 570 real catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
