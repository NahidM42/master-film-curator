# Verification — Media Filename and Episode Parser

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_normalize_media.py tests/test_scan_match.py
```

Coverage: 1917 (2019), 2001 A Space Odyssey, accented Unicode, fullwidth text, S01E01E02, Season 03 with S02E01, generic S01E01 filenames.

Failure contract: Missing evidence returns None/uncertainty rather than fabricated year or episode. Caller must block uncertain series operations.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 570 real catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
