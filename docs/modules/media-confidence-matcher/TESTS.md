# Verification — Confidence Matching and Persistent Review

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_scan_match.py tests/test_cli_tui.py tests/test_end_to_end.py
```

Coverage: Same title in different years, exact ties, wrong year, director in filename/folder, multiple encodes, distinct episodes, rejected/not-in-catalog files.

Failure contract: Unknown IDs or invalid actions fail. Changed file fingerprints invalidate ordinary approvals; ignore is persistent for that indexed path.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 570 real catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
