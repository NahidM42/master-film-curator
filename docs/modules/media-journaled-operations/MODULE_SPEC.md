# Verified No-overwrite Operations and Rollback — Module Specification

## Module Name

Verified No-overwrite Operations and Rollback

## Purpose

Execute explicitly approved plans with verified no-replace publication and conservative, auditable reversal.

## Problem Solved

Prevent loss of originals during cross-device copies, collisions, interrupted operations and unsafe rollback.

## Inputs & Types

Database/Config, stored plan ID, dry_run bool default True, confirmed bool, cross-device deletion flag; operation ID for rollback.

## Outputs & Types

Operation manifest/status, JSON journal and JSONL audit, verified destination files; rollback preview/results.

## Dependencies

Python 3.12+ os/shutil/ctypes/hashlib/sqlite3; Linux no-replace primitives; ffprobe availability gate.

## Database Dependencies

Reads plans/media/catalog metadata; journals operations; updates applied paths and retained-source markers; records events.

## Environment Variables

No application-specific environment variables. PATH may locate ffprobe; explicit configuration takes precedence. No API keys or credentials.

## Security Assumptions

Local trusted configuration, state and logs. Treat filenames and workbook values as data; never interpolate them into a shell. Keep media directories quiescent during approved filesystem operations. Tests use only generated or temporary files.

## Validation Rules

Never overwrite. Preflight current identity/hash, match approval, catalog checksum, root membership, mount availability, symlinks, collisions and free space. Require explicit confirmation; cross-device source removal requires separate flag.

## Core Logic

Persist intent; exclusively create staging file; copy/fsync; verify source and staging; record publishing intent; atomically publish without replacement; compare published bytes to staging digest; persist verified destination; optionally remove verified source; commit journal and index. Rollback validates recorded identities, restores without replacement, then removes only the verified destination.

## Step-by-step Operations

1. Validate documented input types and configuration before side effects.
2. Execute the core algorithm below, preserving uncertainty and source data.
3. Persist only the documented state; record errors rather than silently correcting identity.
4. Run the named tests and a generated-library integration scenario.
5. Deliver the contracts, limitations and explicit UI behavior alongside the implementation.

## Error Handling

Stop remaining Plan on first filesystem failure; keep source until verification succeeds; log partial_failure. Unsafe rollback entries are reported and untouched. Hard-crash unknown ownership is never guessed.

## Edge Cases

Same-drive and cross-drive, source change, post-publication corruption, permission denied, full disk, racing existing destination, stale plan, symlink ancestor, rollback target modified or original path occupied.

## Data Flow

Database/Config, stored plan ID, dry_run bool default True, confirmed bool, cross-device deletion flag; operation ID for rollback.

→ Persist intent; exclusively create staging file; copy/fsync; verify source and staging; record publishing intent; atomically publish without replacement; compare published bytes to staging digest; persist verified destination; optionally remove verified source; commit journal and index. Rollback validates recorded identities, restores without replacement, then removes only the verified destination.

→ Operation manifest/status, JSON journal and JSONL audit, verified destination files; rollback preview/results.

## API / Function Contracts

apply_plan(db, config, plan_id, *, dry_run=True, confirmed=False, delete_source_after_verify=False) -> dict; rollback(db, config, operation_id, *, dry_run=True, confirmed=False) -> dict; snapshot(path,mode) -> dict; check_snapshot(path,expected,identity=True) -> dict.

## Relevant Files

`src/master_film_curator/operations/verifier.py`, `src/master_film_curator/operations/mover.py`, `src/master_film_curator/operations/rollback.py`

## Tests

`uv run pytest tests/test_operations.py tests/test_end_to_end.py`

The source project full suite passed 70 tests, including real ffprobe metadata and full synthetic apply/idempotency/rollback. Consult TESTS.md for scope.

## Acceptance Criteria

Documented contracts are implemented; named tests pass; original Excel bytes are unchanged; only explicitly approved operation APIs can modify media; uncertainty stays reviewable; repeated runs do not create additional copies.

## Known Limitations

Not an atomic transaction across an entire archive or multiple drives. Hard kills can leave staging files or uncertain journal phases requiring manual inspection. Trusted state and quiescent filesystem required. Linux/WSL only; real NTFS/exFAT unplug behavior not yet pilot-tested.

## Integration Points

Source project: Master Film Curator (formerly local media-library-curator) v0.1.0. Composes through validated Config, SQLite helpers and the API contracts above. See source docs/architecture.md and docs/safety.md before transplanting file-operation code.

## Expected CLI/TUI Behavior

apply shows summary then confirms, or explicit --yes. rollback defaults to preview; --execute requires confirmation. Exposes operation ID and per-entry failure/verification state.

## Example Input / Output

Cross-device apply without deletion flag keeps source and verifies copy. Rollback later removes that copy only if both source and destination still match recorded content.

## Complete Reusable Prompt

See REUSABLE_PROMPT.md in this directory; it embeds this complete contract so it can be copied independently.
