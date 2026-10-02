# Complete Reusable Prompt

Implement or adapt the following independently testable Python 3.12 module. Follow every contract below. Do not copy unrelated application state, change source classifications, invent media identities, overwrite existing files, or bypass explicit approval. First inspect the target project and reusable modules; describe compatibility decisions. Implement the smallest modular solution, test the edge cases in isolated temporary directories, run a synthetic integration scenario, and document the verified limitations. Do not test mutation on a real archive. Deliver source, tests and these four module documents.

# ffprobe Video Metadata and Resolution Classes — Module Specification

## Module Name

ffprobe Video Metadata and Resolution Classes

## Purpose

Measure video stream dimensions and metadata, then separate below/above/unknown resolution classes.

## Problem Solved

Avoid trusting filename quality labels and misclassifying 1920x800 CinemaScope encodes as below 1080.

## Inputs & Types

Video Path, ffprobe executable str, timeout float, QualityConfig; SQLite inventory for batch probing.

## Outputs & Types

width/height/codec/duration/bitrate/raw metadata dictionary; quality class; failure counts and stored probe errors.

## Dependencies

Python 3.12+ subprocess/json/shutil; external ffprobe from FFmpeg.

## Database Dependencies

Updates media probe/quality/error fields; invalidates unused plans; writes quality audit event.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Require executable; subprocess argument list with no shell; timeout enforced; ignore attached cover-art streams; largest real video stream selected. Dimensions are authoritative; no filename fallback.

## Core Logic

Run ffprobe JSON output, filter video streams, parse optional numeric fields, classify Higher/2160/1440/1080/720/SD/Unknown, store results or explicit failures.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Missing ffprobe raises actionable installation error; bad video, no stream, invalid JSON, timeout and changed inventory files are captured as Unknown with probe_error.

## Edge Cases

1920x800; missing bitrate; attached cover art; unknown dimensions; 4K is above-resolution review, not bad quality.

## Data Flow

Video Path, ffprobe executable str, timeout float, QualityConfig; SQLite inventory for batch probing.

→ Run ffprobe JSON output, filter video streams, parse optional numeric fields, classify Higher/2160/1440/1080/720/SD/Unknown, store results or explicit failures.

→ width/height/codec/duration/bitrate/raw metadata dictionary; quality class; failure counts and stored probe errors.

## API / Function Contracts

require_ffprobe(executable="ffprobe") -> str absolute executable; probe(path, executable="ffprobe", timeout=45) -> dict; resolution_class(width, height, config=None) -> str; quality_folder(quality) -> str|None; run_quality(db, config) -> dict.

## Relevant Files

`src/master_film_curator/media/ffprobe.py`, `src/master_film_curator/media/quality.py`

## Tests

`uv run pytest tests/test_normalize_media.py tests/test_end_to_end.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

Resolution class does not measure subjective quality, upscaling, frame-by-frame corruption or source mastering resolution.

## Integration Points

Source project: Master Film Curator (formerly local media-library-curator) v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

doctor checks availability; quality measures indexed files; apply also requires ffprobe availability.

## Example Input / Output

1920x800 -> 1080-class -> normal hierarchy; 3840x2160 -> 2160 / 4K -> 90_Quality_Review/Above_1080_4K.
