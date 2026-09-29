# Verification — Read-only Rev07 Excel Catalog Import

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_catalog_config.py tests/test_end_to_end.py
```

Coverage: Duplicate titles across years are valid; formulas require cached values; historical audit sheet never overrides main sheet; independent flags overlap.

Failure contract: Missing sheets/columns, invalid records, count mismatch and ID errors stop import. Removed previously imported IDs require a new database to preserve old audit history.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 570 real catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
