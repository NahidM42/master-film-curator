# Classification and Safe File Operation Planner — Module Specification

## Module Name

Classification and Safe File Operation Planner

## Purpose

Build immutable, reviewable media/sidecar destination plans from confirmed identities and source metadata.

## Problem Solved

Keep multiple classification dimensions, films, episodes, long Windows paths and related files consistent without moving anything during planning.

## Inputs & Types

Config, catalog records, indexed approved media and live source filesystem; verification mode.

## Outputs & Types

Stored UUID plan containing entries, snapshots, noops, blocked reasons and summary; deterministic safe paths and transformation audit.

## Dependencies

Python 3.12+, classification/renaming helpers, snapshot verifier, optional ffprobe for collision comparisons.

## Database Dependencies

Reads catalog/media/metadata; inserts plans and plan event. Does not mutate media.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Only matched above threshold or manual_accepted rows; uncertain episodes blocked even after identity acceptance; Windows invalid/reserved names sanitized; UTF-16 path and UTF-8 component limits; no overwrite; case-insensitive collisions block bundles.

## Core Logic

Choose priority/tier hierarchy and quality prefix; derive movie or season/episode name; reserve subtitle suffix budget; identify sidecars and unique-owner extras; snapshot all sources; detect in-plan and disk collisions; persist summary and blocked items.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Changed/unreadable sources, shared/unowned subtitles, excessively long roots and uncertain series become blocked entries. Plan collisions prevent apply.

## Edge Cases

Multi-director titles, 4K, unknown metadata, multiple approved versions, orphan sidecars, case aliases, shared subtitles, extras, long Unicode titles and repeat plans.

## Data Flow

Config, catalog records, indexed approved media and live source filesystem; verification mode.

→ Choose priority/tier hierarchy and quality prefix; derive movie or season/episode name; reserve subtitle suffix budget; identify sidecars and unique-owner extras; snapshot all sources; detect in-plan and disk collisions; persist summary and blocked items.

→ Stored UUID plan containing entries, snapshots, noops, blocked reasons and summary; deterministic safe paths and transformation audit.

## API / Function Contracts

classification_path(record, quality, config) -> Path; safe_component(value, limit=110) -> str; destination_for(...) -> (Path,list[dict]); sidecar_name(sidecar,video,new_stem) -> str; create_plan(db,config) -> dict; load_plan(db,plan_id) -> (dict,str).

## Relevant Files

`src/media_curator/planning/classifier.py`, `src/media_curator/planning/renamer.py`, `src/media_curator/planning/planner.py`

## Tests

`uv run pytest tests/test_planning.py tests/test_operations.py tests/test_end_to_end.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

Extras are attached only in unambiguous dedicated movie folders. Unknown episode structures require manual filesystem organization and rescan. Shortening uses stable hash suffixes.

## Integration Points

Source project: local media-library-curator v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

plan prints UUID, move/rename/quality/series/ambiguity/missing/collision/size summary. report exposes every source/destination. Plan generation is always non-destructive.

## Example Input / Output

Persona 1966, Essential/S, 1080-class -> 01_Essential/S/Persona (1966) — Ingmar Bergman/Persona (1966) — Ingmar Bergman.mkv.

## Complete Reusable Prompt

See REUSABLE_PROMPT.md in this directory; it embeds this complete contract so it can be copied independently.
