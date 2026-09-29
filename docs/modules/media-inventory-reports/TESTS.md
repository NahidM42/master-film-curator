# Verification — Media Inventory and Operation Reports

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_reports.py tests/test_end_to_end.py
```

Coverage: No plans, no operations, empty inventory, offline roots, overlapping flags, approved duplicate encodes, different episodes of one series and malicious spreadsheet-like filenames.

Failure contract: Write failures propagate clearly; unique report directories prevent replacement of previous reports.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 570 real catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
