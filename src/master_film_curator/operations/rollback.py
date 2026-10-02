import json
from pathlib import Path

from master_film_curator.db.sqlite import event, now
from master_film_curator.operations.mover import (
    copy_payload,
    fsync_directory,
    log_entry,
    persist_manifest,
    publish_no_replace,
)
from master_film_curator.operations.verifier import (
    SafetyError,
    case_collision,
    check_snapshot,
    no_symlinks,
    snapshot,
)


def load_manifest(db, config, operation_id):
    row = db.execute("SELECT manifest FROM operations WHERE id=?", (operation_id,)).fetchone()
    if not row:
        raise ValueError("Unknown operation ID")
    # operation_id comes from the DB, not an arbitrary user-controlled filesystem path.
    manifest = json.loads(row[0])
    path = config.logs_root / manifest["operation_id"] / "rollback_manifest.json"
    if path.exists():
        disk = json.loads(path.read_text(encoding="utf-8"))
        if disk["operation_id"] != manifest["operation_id"] or disk["plan_id"] != manifest["plan_id"]:
            raise SafetyError("Manifest identity mismatch")
        manifest = disk
    return manifest


def rollback(db, config, operation_id, *, dry_run=True, confirmed=False):
    manifest = load_manifest(db, config, operation_id)
    if manifest["status"] == "rolled_back":
        return {"operation_id": operation_id, "status": "already_rolled_back", "entries": []}
    if not dry_run and not confirmed:
        raise SafetyError("Explicit rollback approval required")
    results = []
    for entry in reversed(manifest["entries"]):
        if entry.get("rollback_status") == "restored" or entry["state"] == "pending":
            continue
        src, dst = Path(entry["source"]), Path(entry["destination"])
        result = {"source": str(src), "destination": str(dst), "status": "safe"}
        try:
            from master_film_curator.operations.mover import mounted_windows_drive

            mounted_windows_drive(src)
            mounted_windows_drive(dst)
            if not entry.get("destination_snapshot"):
                raise SafetyError(
                    "No verified ownership of destination; inspect interrupted operation manually"
                )
            no_symlinks(src)
            no_symlinks(dst)
            check_snapshot(dst, entry["destination_snapshot"])
            if entry["operation"] == "copy":
                if not src.exists():
                    raise SafetyError("Retained source is missing; keep destination")
                check_snapshot(src, entry["destination_snapshot"], identity=False)
            elif src.exists() or case_collision(src):
                # If recovery previously restored a source, only the persisted identity authorizes cleanup.
                if not entry.get("restored_snapshot"):
                    raise SafetyError("Original path is occupied; no overwrite or deletion permitted")
                check_snapshot(src, entry["restored_snapshot"])
            if not dry_run:
                if entry["operation"] == "move" and not src.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    no_symlinks(src)
                    temporary = src.with_name(f".curator-rollback-{operation_id}.partial")
                    try:
                        copy_payload(dst, temporary)
                        check_snapshot(temporary, entry["destination_snapshot"], identity=False)
                        check_snapshot(dst, entry["destination_snapshot"])
                        publish_no_replace(temporary, src)
                    finally:
                        if temporary.exists() and not temporary.is_symlink():
                            temporary.unlink()
                    entry["restored_snapshot"] = snapshot(src, "sha256")
                    entry["rollback_status"] = "source_restored"
                    persist_manifest(db, config, manifest)
                check_snapshot(src, entry["destination_snapshot"], identity=False)
                check_snapshot(dst, entry["destination_snapshot"])
                dst.unlink()
                fsync_directory(dst.parent)
                if entry["media_id"]:
                    stat = src.stat()
                    # A rescan may have re-indexed the retained source. Merge that non-authoritative index row.
                    other = db.execute(
                        "SELECT id FROM media WHERE path=? AND id!=?", (str(src), entry["media_id"])
                    ).fetchone()
                    if other:
                        db.execute("DELETE FROM decisions WHERE media_id=?", (other[0],))
                        db.execute("DELETE FROM media WHERE id=?", (other[0],))
                    db.execute(
                        "UPDATE media SET path=?,size=?,mtime_ns=?,device=?,inode=?,present=1 WHERE id=?",
                        (
                            str(src),
                            stat.st_size,
                            stat.st_mtime_ns,
                            stat.st_dev,
                            stat.st_ino,
                            entry["media_id"],
                        ),
                    )
                    db.execute("DELETE FROM metadata WHERE key=?", ("retained:" + str(src),))
                entry["rollback_status"] = "restored"
                entry["rollback_timestamp"] = now()
                persist_manifest(db, config, manifest)
                log_entry(config, manifest, {**entry, "state": "rolled_back"})
                result["status"] = "restored"
        except (OSError, SafetyError) as exc:
            result.update(status="unsafe", error=str(exc))
        results.append(result)
    if not dry_run:
        manifest["rollback_results"] = results
        manifest["status"] = (
            "rollback_incomplete" if any(r["status"] == "unsafe" for r in results) else "rolled_back"
        )
        db.execute("UPDATE plans SET status='rolled_back' WHERE id=?", (manifest["plan_id"],))
        persist_manifest(db, config, manifest)
        event(db, "rollback", {"operation_id": operation_id, "results": results})
    return {
        "operation_id": operation_id,
        "status": "dry_run" if dry_run else manifest["status"],
        "entries": results,
    }
