# Complete Reusable Prompt

Implement or adapt the following independently testable Python 3.12 module. Follow every contract below. Do not copy unrelated application state, change source classifications, invent media identities, overwrite existing files, or bypass explicit approval. First inspect the target project and reusable modules; describe compatibility decisions. Implement the smallest modular solution, test the edge cases in isolated temporary directories, run a synthetic integration scenario, and document the verified limitations. Do not test mutation on a real archive. Deliver source, tests and these four module documents.

# Media Inventory and Operation Reports — Module Specification

## Module Name

Media Inventory and Operation Reports

## Purpose

Produce inspectable CSV/JSON/Markdown inventory and audit artifacts from consistent SQLite state.

## Problem Solved

Distinguish confirmed library presence from unconfirmed or unavailable files and expose proposed actions without mutating media.

## Inputs & Types

SQLite connection and Config reports_root; catalog/media/plan/operation rows.

## Outputs & Types

New timestamp/UUID report directory Path containing 11 CSVs, operation_summary.json, rollback_manifest.json and summary.md.

## Dependencies

Python 3.12+ csv/json/datetime/pathlib; SQLite query helpers.

## Database Dependencies

Read-only queries of all domain tables; reports do not alter matching or file state.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Use UTF-8 BOM CSV; escape formula-triggering strings; preserve numeric values; consistent field headers for empty reports; missing means no confirmed present match; include pending-candidate counts.

## Core Logic

Flatten catalog/inventory/probe records; select confirmed, missing, unmatched, ambiguous and duplicate groups; split quality classes; export latest Plan paths; snapshot operation manifests; render human summary.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Write failures propagate clearly; unique report directories prevent replacement of previous reports.

## Edge Cases

No plans, no operations, empty inventory, offline roots, overlapping flags, approved duplicate encodes, different episodes of one series and malicious spreadsheet-like filenames.

## Data Flow

SQLite connection and Config reports_root; catalog/media/plan/operation rows.

→ Flatten catalog/inventory/probe records; select confirmed, missing, unmatched, ambiguous and duplicate groups; split quality classes; export latest Plan paths; snapshot operation manifests; render human summary.

→ New timestamp/UUID report directory Path containing 11 CSVs, operation_summary.json, rollback_manifest.json and summary.md.

## API / Function Contracts

generate_reports(db, config) -> Path; write_csv(path,rows,fields) -> None; csv_value(value) -> scalar; write_summary(path,summary) -> None.

## Relevant Files

`src/media_curator/reports/csv_reports.py`, `src/media_curator/reports/summary.py`

## Tests

`uv run pytest tests/test_reports.py tests/test_end_to_end.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

Missing is not proof a title was never acquired. Series completeness is unknown. Report manifest is a DB snapshot; per-operation logs journal is authoritative after a crash.

## Integration Points

Source project: local media-library-curator v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

report prints the generated folder. Reports never authorize or execute operations.

## Example Input / Output

One confirmed Persona plus three unconfirmed fixture records -> missing CSV contains IDs 2, 3 and 4. A filename beginning = is prefixed with an apostrophe for Excel safety.

