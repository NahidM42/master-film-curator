# Verification — Verified No-overwrite Operations and Rollback

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_operations.py tests/test_end_to_end.py
```

Coverage: Same-drive and cross-drive, source change, post-publication corruption, permission denied, full disk, racing existing destination, stale plan, symlink ancestor, rollback target modified or original path occupied.

Failure contract: Stop remaining Plan on first filesystem failure; keep source until verification succeeds; log partial_failure. Unsafe rollback entries are reported and untouched. Hard-crash unknown ownership is never guessed.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 570 real catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
