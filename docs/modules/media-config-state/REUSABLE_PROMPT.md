# Complete Reusable Prompt

Implement or adapt the following independently testable Python 3.12 module. Follow every contract below. Do not copy unrelated application state, change source classifications, invent media identities, overwrite existing files, or bypass explicit approval. First inspect the target project and reusable modules; describe compatibility decisions. Implement the smallest modular solution, test the edge cases in isolated temporary directories, run a synthetic integration scenario, and document the verified limitations. Do not test mutation on a real archive. Deliver source, tests and these four module documents.

# Local Curator Configuration and State — Module Specification

## Module Name

Local Curator Configuration and State

## Purpose

Validate portable YAML configuration and persist auditable application state under a single-command lock.

## Problem Solved

Prevent hard-coded paths, invalid thresholds, competing commands and lost review history.

## Inputs & Types

Path to YAML; sqlite3 database Path; JSON-serializable event dictionaries.

## Outputs & Types

Config Pydantic model; context-managed sqlite3.Connection with Row factory; persisted tables and events.

## Dependencies

Python 3.12+, pydantic>=2, PyYAML>=6, standard sqlite3/fcntl/pathlib.

## Database Dependencies

Owns metadata, catalog, media, decisions, plans, operations and events schema. Foreign keys enabled; synchronous FULL.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Reject unknown YAML fields; auto_accept in [85,100]; review_threshold below auto_accept; distinct classification dimensions; configured path limits. Resolve all relative paths against the YAML directory.

## Core Logic

Read YAML safely, validate typed nested models, resolve paths, acquire nonblocking flock, initialize schema, yield a connection, commit on success or rollback on failure, release resources.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Unreadable YAML, validation failures, database errors and competing-process locks are surfaced; no media mutation.

## Edge Cases

Empty sources allowed for initial setup; config dry_run=false never authorizes mutation; relative executable paths are resolved; Linux/WSL only.

## Data Flow

Path to YAML; sqlite3 database Path; JSON-serializable event dictionaries.

→ Read YAML safely, validate typed nested models, resolve paths, acquire nonblocking flock, initialize schema, yield a connection, commit on success or rollback on failure, release resources.

→ Config Pydantic model; context-managed sqlite3.Connection with Row factory; persisted tables and events.

## API / Function Contracts

load_config(path: Path) -> Config; connect(path: Path, *, lock: bool=True) -> context manager; event(db, kind: str, data) -> None; catalog_records(db) -> list[dict].

## Relevant Files

`src/media_curator/config.py`, `src/media_curator/db/sqlite.py`

## Tests

`uv run pytest tests/test_catalog_config.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

Schema v1 has no cross-version migration framework. SQLite/log locations must be trusted and available. Independent databases must not manage the same archive concurrently.

## Integration Points

Source project: local media-library-curator v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

All commands accept --config before the subcommand. doctor validates paths without creating media files.

## Example Input / Output

A YAML at /workspace/settings/config.yaml with sources: [input] resolves to /workspace/settings/input.
