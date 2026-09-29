# Read-only Rev07 Excel Catalog Import — Module Specification

## Module Name

Read-only Rev07 Excel Catalog Import

## Purpose

Import authoritative catalog classifications and independent cross-sheet flags without recalculating them.

## Problem Solved

Preserve a user-maintained ranking workbook as source of truth while making it queryable by stable Master ID.

## Inputs & Types

XLSX Path; expected_count: int|None, default 570; database connection for persistence.

## Outputs & Types

list[CatalogRecord] or imported integer count; source checksum and raw rows retained in SQLite.

## Dependencies

Python 3.12+, openpyxl>=3.1, pydantic>=2, standard hashlib.

## Database Dependencies

Writes catalog and metadata; invalidates unused plans and automated matches; emits catalog_import event.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Require primary and flag sheets, all mapped headers, positive unique Master IDs, allowed tiers S/A/B/C/D, numeric years and valid priority prefixes. Reject orphan or duplicate flag IDs. Never change scores or tiers.

## Core Logic

Open load_workbook(read_only=True,data_only=True), validate all master rows, infer explicit series hints, join four flag sets by ID, validate before persistence, upsert records and store SHA-256.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Missing sheets/columns, invalid records, count mismatch and ID errors stop import. Removed previously imported IDs require a new database to preserve old audit history.

## Edge Cases

Duplicate titles across years are valid; formulas require cached values; historical audit sheet never overrides main sheet; independent flags overlap.

## Data Flow

XLSX Path; expected_count: int|None, default 570; database connection for persistence.

→ Open load_workbook(read_only=True,data_only=True), validate all master rows, infer explicit series hints, join four flag sets by ID, validate before persistence, upsert records and store SHA-256.

→ list[CatalogRecord] or imported integer count; source checksum and raw rows retained in SQLite.

## API / Function Contracts

read_catalog(path: Path, expected_count: int|None=570) -> list[CatalogRecord]; import_catalog(db, path: Path, expected_count=570) -> int.

## Relevant Files

`src/media_curator/catalog/models.py`, `src/media_curator/catalog/excel_reader.py`

## Tests

`uv run pytest tests/test_catalog_config.py tests/test_end_to_end.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

Header mapping is specific to Rev07. No external enrichment or arbitrary workbook schema discovery.

## Integration Points

Source project: local media-library-curator v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

import-catalog writes only application state; doctor opens the workbook read-only and reports count.

## Example Input / Output

Master ID 545 maps to A Separation (2011), S, Channel 100, Taste 100; top_content_candidate remains true.

## Complete Reusable Prompt

See REUSABLE_PROMPT.md in this directory; it embeds this complete contract so it can be copied independently.
