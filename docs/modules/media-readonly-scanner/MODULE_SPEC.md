# Read-only Multi-root Media Scanner — Module Specification

## Module Name

Read-only Multi-root Media Scanner

## Purpose

Index a local video library without changing any media, while recognizing offline roots and preserved copies.

## Problem Solved

Build a reproducible inventory spanning laptop and external drives without stale presence claims or accidental symlink traversal.

## Inputs & Types

Validated Config with sources/destination and database connection.

## Outputs & Types

Counts and structured path errors; one media row per absolute path with stat identity, parsed data and presence.

## Dependencies

Python 3.12+ standard os/pathlib/json; filename and episode parser.

## Database Dependencies

Upserts media; removes stale content-scoped decisions; invalidates planned plans; records scan events.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Nine required video extensions; recursively walk non-symlink directories; deduplicate overlapping root paths; mark absent/offline inventory nonpresent before scan; never read paths as executable code.

## Core Logic

Combine configured roots and existing destination, walk directories, stat video files, parse names and extras, upsert unchanged/changed rows, invalidate changed quality/matches, preserve permanent ignore and retained_source markers.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Drive disappearance, permission errors and stat failures become path errors; scanning continues for accessible files. No media moves or deletes.

## Edge Cases

Overlapping roots, disconnected roots, symlink videos, unusual Unicode, extras folders, canonical shortened names and preserved cross-device source copies.

## Data Flow

Validated Config with sources/destination and database connection.

→ Combine configured roots and existing destination, walk directories, stat video files, parse names and extras, upsert unchanged/changed rows, invalidate changed quality/matches, preserve permanent ignore and retained_source markers.

→ Counts and structured path errors; one media row per absolute path with stat identity, parsed data and presence.

## API / Function Contracts

scan(db, config: Config) -> dict[indexed,changed,errors,skipped_symlinks]; is_extra(path: Path, root: Path) -> bool.

## Relevant Files

`src/master_film_curator/scanner/filesystem.py`, `src/master_film_curator/scanner/media_detection.py`

## Tests

`uv run pytest tests/test_scan_match.py tests/test_operations.py tests/test_end_to_end.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

Video-only index; associated sidecars are enumerated during planning. No full-media hash on every scan; identity changes use size/mtime/device/inode.

## Integration Points

Source project: Master Film Curator (formerly local media-library-curator) v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

scan prints inventory counts and unavailable-path warnings. Filesystem state changes only in the application database.

## Example Input / Output

Two roots with one Persona video and one unknown video produce indexed=2, with both original byte strings and mtimes unchanged.

## Complete Reusable Prompt

See REUSABLE_PROMPT.md in this directory; it embeds this complete contract so it can be copied independently.
