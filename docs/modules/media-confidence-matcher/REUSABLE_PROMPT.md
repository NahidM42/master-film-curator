# Complete Reusable Prompt

Implement or adapt the following independently testable Python 3.12 module. Follow every contract below. Do not copy unrelated application state, change source classifications, invent media identities, overwrite existing files, or bypass explicit approval. First inspect the target project and reusable modules; describe compatibility decisions. Implement the smallest modular solution, test the edge cases in isolated temporary directories, run a synthetic integration scenario, and document the verified limitations. Do not test mutation on a real archive. Deliver source, tests and these four module documents.

# Confidence Matching and Persistent Review — Module Specification

## Module Name

Confidence Matching and Persistent Review

## Purpose

Match indexed media to catalog identities with explainable scores and persistent human decisions.

## Problem Solved

Prevent false-positive organization for duplicate titles, uncertain years, fuzzy names and multiple encodes.

## Inputs & Types

Parsed title/year/context, catalog list[dict], MatchingConfig, SQLite inventory; explicit review media ID/action/Master ID.

## Outputs & Types

Top five candidate dictionaries with similarity/confidence/year_difference/reason; media status and persisted review decision.

## Dependencies

Python 3.12+, RapidFuzz>=3, normalization and SQLite modules.

## Database Dependencies

Reads catalog/media; writes match state, candidates, decisions and events; invalidates existing unused plans.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Exact title/year 100; ±1 year 97; exact title plus director without year 96; fuzzy compatible-year evidence capped 94; title-only never auto-accepted. Ambiguity gap <= configured margin requires review. Multiple encodes require individual approval.

## Core Logic

Rank candidates deterministically; decide unmatched/manual_review/matched; honor valid persisted decisions; protect uncertain series; group duplicate movie or episode candidates; record result counts.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Unknown IDs or invalid actions fail. Changed file fingerprints invalidate ordinary approvals; ignore is persistent for that indexed path.

## Edge Cases

Same title in different years, exact ties, wrong year, director in filename/folder, multiple encodes, distinct episodes, rejected/not-in-catalog files.

## Data Flow

Parsed title/year/context, catalog list[dict], MatchingConfig, SQLite inventory; explicit review media ID/action/Master ID.

→ Rank candidates deterministically; decide unmatched/manual_review/matched; honor valid persisted decisions; protect uncertain series; group duplicate movie or episode candidates; record result counts.

→ Top five candidate dictionaries with similarity/confidence/year_difference/reason; media status and persisted review decision.

## API / Function Contracts

candidates_for(parsed: dict, context: str, catalog: list[dict]) -> list[dict]; decide(candidates, config) -> str; match_all(db, config) -> dict; save_decision(db, media_id: int, action: str, master_id: int|None=None).

## Relevant Files

`src/master_film_curator/matching/confidence.py`, `src/master_film_curator/matching/matcher.py`

## Tests

`uv run pytest tests/test_scan_match.py tests/test_cli_tui.py tests/test_end_to_end.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

Heuristic confidence is not a calibrated statistical probability. Catalog aliases and alternate-language titles require review.

## Integration Points

Source project: Master Film Curator (formerly local media-library-curator) v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

match never mutates media. review supports accept, reject, choosing any existing Master ID, not_in_catalog and ignore in CLI and optional TUI.

## Example Input / Output

Shame without year -> manual_review with 1968 and 2011 candidates. Shame.2011 -> exact match to 2011.
