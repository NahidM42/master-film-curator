# Verification — ffprobe Video Metadata and Resolution Classes

Source version: 0.1.0, Python 3.12.13.

```bash
uv sync --extra tui
uv run pytest tests/test_normalize_media.py tests/test_end_to_end.py
```

Coverage: 1920x800; missing bitrate; attached cover art; unknown dimensions; 4K is above-resolution review, not bad quality.

Failure contract: Missing ffprobe raises actionable installation error; bad video, no stream, invalid JSON, timeout and changed inventory files are captured as Unknown with probe_error.

Full project verification: 70 passing tests, including actual FFmpeg-generated videos, read-only import of 570 real catalog rows, ambiguity exclusions, 9 planned file operations, repeated empty plan, and byte-preserving rollback. Standalone demo result is retained locally in demo-output/acceptance-result.json. No actual user archive was scanned or mutated. External drive behavior is simulated, not falsely claimed as a real NTFS/exFAT unplug test.
