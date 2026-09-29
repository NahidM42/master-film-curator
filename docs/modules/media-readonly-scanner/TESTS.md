# Verification — Read-only Multi-root Media Scanner

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_scan_match.py tests/test_operations.py tests/test_end_to_end.py
```

Coverage: Overlapping roots, disconnected roots, symlink videos, unusual Unicode, extras folders, canonical shortened names and preserved cross-device source copies.

Failure contract: Drive disappearance, permission errors and stat failures become path errors; scanning continues for accessible files. No media moves or deletes.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 570 real catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
