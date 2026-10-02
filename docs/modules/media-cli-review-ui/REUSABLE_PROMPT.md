# Complete Reusable Prompt

Implement or adapt the following independently testable Python 3.12 module. Follow every contract below. Do not copy unrelated application state, change source classifications, invent media identities, overwrite existing files, or bypass explicit approval. First inspect the target project and reusable modules; describe compatibility decisions. Implement the smallest modular solution, test the edge cases in isolated temporary directories, run a synthetic integration scenario, and document the verified limitations. Do not test mutation on a real archive. Deliver source, tests and these four module documents.

# Typer CLI and Optional Textual Review — Module Specification

## Module Name

Typer CLI and Optional Textual Review

## Purpose

Expose the complete local curation workflow with explicit mutation approval and interchangeable review interfaces.

## Problem Solved

Make inventory, matching, review and recovery usable without requiring a GUI or letting an interface bypass core safety rules.

## Inputs & Types

CLI options and YAML configuration; interactive review selections; database connection.

## Outputs & Types

Rich summaries/JSON, process exit codes, persistent review decisions, optional terminal UI.

## Dependencies

Python 3.12+, Typer, Rich; optional Textual; core modules.

## Database Dependencies

Uses process-locked state context; TUI delegates decisions to the same save_decision contract as CLI.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Global --config before command; review accept requires valid Master ID; reject/not_in_catalog/ignore use no catalog ID; apply prints saved Plan summary and requires confirmation or --yes; rollback defaults to preview.

## Core Logic

Load config, open protected session, call one core operation, format results, translate expected errors to concise stop messages. TUI displays queue/candidates, accepts user action and commits decision.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Invalid config and expected filesystem/validation/database errors produce exit 1; apply partial_failure and incomplete rollback also exit 1. Missing optional TUI gives install command.

## Edge Cases

Empty queue, noninteractive scripts, rejected confirmation, alternate candidate, absent ffprobe, missing optional Textual and unknown file IDs.

## Data Flow

CLI options and YAML configuration; interactive review selections; database connection.

→ Load config, open protected session, call one core operation, format results, translate expected errors to concise stop messages. TUI displays queue/candidates, accepts user action and commits decision.

→ Rich summaries/JSON, process exit codes, persistent review decisions, optional terminal UI.

## API / Function Contracts

app: typer.Typer; main() -> None; ReviewApp(db): Textual App; session(ctx) -> context manager.

## Relevant Files

`src/master_film_curator/cli/commands.py`, `src/master_film_curator/tui/review_app.py`, `src/master_film_curator/main.py`

## Tests

`uv run pytest tests/test_cli_tui.py tests/test_end_to_end.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

No browser UI, remote service or background daemon. TUI requires a suitable terminal; CLI remains complete without it.

## Integration Points

Source project: Master Film Curator (formerly local media-library-curator) v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

doctor, import-catalog, scan, match, quality, review, plan, report, apply, rollback, status. review --interactive and --tui are optional; --file-id/--action/--master-id covers every decision.

## Example Input / Output

film-curator review --file-id 12 --action accept --master-id 545 stores an explicit match; no media is moved until a later approved Plan.
