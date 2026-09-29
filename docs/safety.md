# Safety model and recovery

The supported runtime is Python 3.12+ on Linux/WSL2, with a trusted local SQLite database and logs directory. Native Windows Python is not supported in v1: the process lock uses `fcntl`, and no-replace publication uses Linux primitives. NTFS/exFAT through WSL requires practical validation on that filesystem before a large real-archive run.

## Invariants

- Import, scan, match, review, quality, plan and report never rename/delete media. They may write application state, reports or logs.
- The public operation API defaults to `dry_run=True`. CLI `apply` is the explicit mutation command and displays a summary before confirmation. Configuration cannot bypass confirmation.
- Pending/low-confidence/ambiguous/unmatched/multiple candidates are not planned automatically. Manual acceptance is recorded with file size and nanosecond mtime.
- Source identity includes device, inode, size and mtime; the configured digest is captured at planning and checked before apply.
- Every source and destination path is checked for symlinks. Destination paths must stay inside the configured root. `/mnt/<letter>` must be mounted before media mutations.
- Existing destinations and case-insensitive Windows aliases are collisions. No code path replaces them. Destination publication uses hard-link plus unlink of the staging name or Linux `renameat2(RENAME_NOREPLACE)`; unsupported filesystems fail closed.
- Copy to a unique, exclusively-created `.partial`, fsync, verify, publish without replacement, verify the published bytes, persist the journal, then remove the source only when the approved operation permits it.
- Cross-device source removal additionally requires `--delete-source-after-verify`. Retained originals are indexed as `retained_source` on rescan and excluded from further automatic copies.
- SQLite commits and JSON journal updates occur between operation phases. A process lock prevents concurrent curator commands sharing the same database. Two different databases must not manage the same archive concurrently.
- Rollback hashes the destination again, refuses occupied original paths, and restores a move through verified no-replace copy. It removes a copied destination only after confirming an intact source.

## Operational limits

Stop downloaders, media editors, sync tools and other programs modifying these paths during apply/rollback. Path/stat checks are protection against accidental changes, not a security boundary against a malicious process concurrently replacing filesystem components. SQLite and logs are trusted local control files: do not edit plan/manifest JSON to bypass review. Keep them on the WSL Linux filesystem, not a disconnected external drive.

`size` and sampled `quick_hash` have weaker integrity guarantees than SHA-256. The default is SHA-256. A full SHA-256 of staged/destination data is retained for rollback even when the configured copy verification is weaker.

A Plan is not a distributed transaction across drives. If file 3 fails, files 1–2 may already be moved. Apply stops the remaining work and logs `partial_failure`. Review the operation manifest, use rollback preview, then execute safe reversals or reconcile manually. Do not rerun the old failed Plan; rescan and make a new Plan after recovery.

Caught copy failures remove the operation's incomplete staging file where possible and retain the source. A hard power loss / SIGKILL / drive removal can leave an owned `.partial`, a published destination plus source, or a phase awaiting its final journal update. No program can promise atomic whole-library rollback across power failures and independent filesystems. The persisted phase and paths are the evidence for recovery; uncertain ownership is reported rather than inferred.

## Recovery procedure

1. Reconnect the exact drives and stop other writers. Copy the SQLite database and `logs/` somewhere safe.
2. Run `status`; read `logs/<id>/rollback_manifest.json` and `operations.jsonl`.
3. Run `rollback <id>` without `--execute`. Only entries with a recorded verified destination identity can be automatically reversed.
4. Use `rollback <id> --execute` for safe reversals. Inspect any `unsafe` entries manually; neither their source nor destination is modified by rollback.
5. A `.partial` from a hard crash is never promoted automatically. Confirm source integrity and manifest ownership before manually removing it. Never delete the source merely because a partial destination exists.
6. Rescan, rematch, rerun quality and create a new Plan after reconciliation.

The rollback snapshot included in reports is informational. The per-operation journal in `logs/` is authoritative when a process died between JSON persistence and a SQLite commit. Empty directories are intentionally retained.

## Known domain limits

Filename parsing is conservative, not a movie-identification oracle. Alternate-language titles, unknown release groups, multi-episode files, absolute anime numbering and unusual box sets can require manual review. Catalog type detection uses explicit TV/series hints in title/genre; no external metadata service is consulted. Individual series episodes are organized safely, but season completeness cannot be inferred from this catalog.

Dimensions are an encode resolution class, not perceptual quality, bitrate sufficiency, upscaling detection, corruption scanning of every frame or proof of the original source resolution. Probe errors are recorded and routed to Unknown.

The filesystem tests use temporary ext4-like storage and simulated cross-device classification. Real external-drive locking, NTFS/exFAT mount options and unplug events require a small user-approved pilot before a full archive run. No such real-archive run was performed during development.
