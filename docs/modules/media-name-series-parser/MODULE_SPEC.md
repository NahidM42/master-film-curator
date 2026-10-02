# Media Filename and Episode Parser — Module Specification

## Module Name

Media Filename and Episode Parser

## Purpose

Normalize matching text and conservatively extract release year, season and episode identifiers.

## Problem Solved

Separate encoding metadata from work identity without renaming source files or collapsing ambiguous episode bundles.

## Inputs & Types

Unicode filename strings and pathlib.Path values; optional title context from nearby folders.

## Outputs & Types

Normalized title str; dictionary containing title/year and season/episode/series_hint/series_uncertain.

## Dependencies

Python 3.12+ standard re, unicodedata and pathlib.

## Database Dependencies

None; scanner persists returned values.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

NFKC, case-folding and punctuation collapse for matching only. Year-like first tokens are titles until later year evidence exists. Multi-episode tokens and inconsistent season folders are uncertain.

## Core Logic

Strip only recognized extensions; find release, year and episode boundaries; remove trailing language tags; parse S01E01/S1E1/1x01; use Season folders and explicit E/EP/Episode numbers; use nearby series title/year context.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Missing evidence returns None/uncertainty rather than fabricated year or episode. Caller must block uncertain series operations.

## Edge Cases

1917 (2019), 2001 A Space Odyssey, accented Unicode, fullwidth text, S01E01E02, Season 03 with S02E01, generic S01E01 filenames.

## Data Flow

Unicode filename strings and pathlib.Path values; optional title context from nearby folders.

→ Strip only recognized extensions; find release, year and episode boundaries; remove trailing language tags; parse S01E01/S1E1/1x01; use Season folders and explicit E/EP/Episode numbers; use nearby series title/year context.

→ Normalized title str; dictionary containing title/year and season/episode/series_hint/series_uncertain.

## API / Function Contracts

normalize_title(value: str) -> str; parse_filename(value: str) -> dict; parse_path(path: Path) -> dict; parse_series(path: Path) -> dict.

## Relevant Files

`src/master_film_curator/matching/normalize.py`, `src/master_film_curator/media/series_parser.py`

## Tests

`uv run pytest tests/test_normalize_media.py tests/test_scan_match.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

No transliteration, alternate-title service, absolute anime numbering or multi-episode renaming. Episode-title metadata is not fetched or invented.

## Integration Points

Source project: Master Film Curator (formerly local media-library-curator) v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

Used by scan and match. Original filenames and original catalog titles remain available in inventory and logs.

## Example Input / Output

A.Separation.2011.1080p.BluRay.x265.AAC-PSA.mkv -> title=a separation, year=2011; Show/Season 02/E03.mkv -> season=2, episode=3.

## Complete Reusable Prompt

See REUSABLE_PROMPT.md in this directory; it embeds this complete contract so it can be copied independently.
