# Verification — Local Curator Configuration and State

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_catalog_config.py
```

Coverage: Empty sources allowed for initial setup; config dry_run=false never authorizes mutation; relative executable paths are resolved; Linux/WSL only.

Failure contract: Unreadable YAML, validation failures, database errors and competing-process locks are surfaced; no media mutation.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 60 synthetic catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
