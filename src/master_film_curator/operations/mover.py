"""Journaled, no-replace file operations. Only explicit apply mutates media."""

import ctypes
import errno
import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from master_film_curator.db.sqlite import dumps, event, now
from master_film_curator.media.ffprobe import require_ffprobe
from master_film_curator.operations.verifier import (
    SafetyError,
    case_collision,
    check_snapshot,
    no_symlinks,
    snapshot,
)
from master_film_curator.planning.planner import load_plan


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".writing")
    with temp.open("w", encoding="utf-8") as stream:
        stream.write(dumps(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    fsync_directory(path.parent)


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    except OSError as exc:
        if exc.errno not in {errno.EINVAL, errno.ENOTSUP}:
            raise
    finally:
        os.close(fd)


def publish_no_replace(source: Path, destination: Path):
    """Publish a temporary file atomically; never fall back to overwriting rename."""
    try:
        os.link(source, destination, follow_symlinks=False)
        source.unlink()
    except OSError as exc:
        if exc.errno not in {errno.EPERM, errno.EOPNOTSUPP, errno.ENOSYS, errno.EXDEV}:
            raise
        libc = ctypes.CDLL(None, use_errno=True)
        if not hasattr(libc, "renameat2"):
            raise SafetyError("Filesystem does not support atomic no-replace publication") from exc
        code = libc.renameat2(-100, os.fsencode(source), -100, os.fsencode(destination), 1)
        if code:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(destination))
    fsync_directory(destination.parent)


def same_filesystem(source: Path, destination_directory: Path):
    return source.stat().st_dev == destination_directory.stat().st_dev


def copy_payload(source: Path, temporary: Path):
    # Exclusive create: another run or an unrelated partial file cannot be overwritten.
    with source.open("rb") as src, temporary.open("xb") as dst:
        shutil.copyfileobj(src, dst, 4 * 1024 * 1024)
        dst.flush()
        os.fsync(dst.fileno())
    shutil.copystat(source, temporary, follow_symlinks=False)


def mounted_windows_drive(path: Path):
    parts = path.absolute().parts
    if len(parts) >= 3 and parts[1] == "mnt" and len(parts[2]) == 1 and parts[2].isalpha():
        mount = Path("/mnt") / parts[2]
        if not mount.is_mount():
            raise SafetyError(f"Windows drive is not mounted: {mount}")


def existing_ancestor(path: Path) -> Path:
    while not path.exists():
        if path == path.parent:
            raise SafetyError("No available destination ancestor")
        path = path.parent
    return path


def preflight(db, config, plan):
    if Path(plan["destination_root"]) != config.destination_root:
        raise SafetyError("Destination changed since planning; create a new plan")
    checksum = db.execute("SELECT value FROM metadata WHERE key='catalog_sha256'").fetchone()
    if not checksum or checksum[0] != plan["catalog_sha256"]:
        raise SafetyError("Catalog changed since planning")
    if any(e["status"] == "collision" for e in plan["entries"]):
        raise SafetyError("Plan contains destination collisions; resolve and create a new plan")
    mounted_windows_drive(config.destination_root)
    no_symlinks(config.destination_root)
    totals = {}
    for entry in plan["entries"]:
        if entry["status"] != "ready":
            continue
        src, dst = Path(entry["source"]), Path(entry["destination"])
        if not dst.is_relative_to(config.destination_root) or ".." in dst.parts:
            raise SafetyError("Destination escapes configured root")
        mounted_windows_drive(src)
        if not any(src.is_relative_to(root) for root in [*config.sources, config.destination_root]):
            raise SafetyError("Source no longer belongs to a configured root")
        check_snapshot(src, entry["snapshot"])
        no_symlinks(dst)
        if case_collision(dst):
            raise SafetyError(f"Destination collision: {dst}")
        if entry["media_id"]:
            row = db.execute("SELECT * FROM media WHERE id=?", (entry["media_id"],)).fetchone()
            if (
                not row
                or row["status"] not in {"matched", "manual_accepted"}
                or not row["present"]
                or row["master_id"] != entry["master_id"]
            ):
                raise SafetyError("Match or inventory changed; re-plan")
            if row["status"] == "matched" and row["confidence"] < config.matching.auto_accept:
                raise SafetyError("Match below current confidence threshold")
        ancestor = existing_ancestor(dst.parent)
        if not ancestor.is_dir():
            raise SafetyError(f"Destination ancestor is not a directory: {ancestor}")
        dev = ancestor.stat().st_dev
        totals.setdefault(dev, {"path": ancestor, "size": 0})["size"] += entry["snapshot"]["size"]
    # Copy staging is deliberately used for both same-drive and cross-drive operations.
    for total in totals.values():
        if shutil.disk_usage(total["path"]).free < total["size"]:
            raise SafetyError(f"Insufficient destination space: {total['path']}")


def persist_manifest(db, config, manifest):
    folder = config.logs_root / manifest["operation_id"]
    # Durable JSON first: rollback can use this authoritative journal if DB update is interrupted.
    atomic_json(folder / "rollback_manifest.json", manifest)
    db.execute(
        "UPDATE operations SET status=?,manifest=? WHERE id=?",
        (manifest["status"], dumps(manifest), manifest["operation_id"]),
    )
    db.commit()


def log_entry(config, manifest, entry):
    with (config.logs_root / "operations.jsonl").open("a", encoding="utf-8") as log:
        log.write(
            dumps(
                {
                    "timestamp": now(),
                    "operation_id": manifest["operation_id"],
                    "master_id": entry["master_id"],
                    "source": entry["source"],
                    "destination": entry["destination"],
                    "match_confidence": entry["confidence"],
                    "operation": entry.get("operation"),
                    "result": entry["state"],
                    "error": entry.get("error"),
                }
            )
            + "\n"
        )
        log.flush()
        os.fsync(log.fileno())


def apply_plan(db, config, plan_id, *, dry_run=True, confirmed=False, delete_source_after_verify=False):
    plan, status = load_plan(db, plan_id)
    if status == "applied":
        return {"status": "already_applied", "plan_id": plan_id}
    if status != "planned":
        raise SafetyError(f"Plan is {status}; scan, match, quality and plan again")
    if dry_run:
        return {"status": "dry_run", "plan_id": plan_id, "summary": plan["summary"]}
    if not confirmed:
        raise SafetyError("Explicit approval required")
    require_ffprobe(config.ffprobe)
    preflight(db, config, plan)
    operation_id = uuid4().hex
    manifest = {
        "operation_id": operation_id,
        "plan_id": plan_id,
        "created": now(),
        "status": "applying",
        "delete_source_after_verify": delete_source_after_verify,
        "entries": [],
    }
    for e in plan["entries"]:
        if e["status"] == "ready":
            manifest["entries"].append(
                {
                    **e,
                    "state": "pending",
                    "operation": None,
                    "timestamp": None,
                    "old_filename": Path(e["source"]).name,
                    "new_filename": Path(e["destination"]).name,
                    "verification_status": "pending",
                    "source_removed": False,
                }
            )
    db.execute(
        "INSERT INTO operations VALUES(?,?,?,?,?)",
        (operation_id, plan_id, now(), "applying", dumps(manifest)),
    )
    db.execute("UPDATE plans SET status='applying' WHERE id=?", (plan_id,))
    persist_manifest(db, config, manifest)
    for index, entry in enumerate(manifest["entries"]):
        src, dst = Path(entry["source"]), Path(entry["destination"])
        temporary = dst.with_name(f".curator-{operation_id}-{index}.partial")
        try:
            check_snapshot(src, entry["snapshot"])
            no_symlinks(dst)
            if case_collision(dst):
                raise SafetyError(f"Destination collision: {dst}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            no_symlinks(dst)
            cross = not same_filesystem(src, dst.parent)
            entry.update(
                operation="copy" if cross and not delete_source_after_verify else "move",
                cross_filesystem=cross,
                temporary=str(temporary),
                timestamp=now(),
                state="copying",
            )
            persist_manifest(db, config, manifest)
            copy_payload(src, temporary)
            check_snapshot(src, entry["snapshot"])
            check_snapshot(temporary, entry["snapshot"], identity=False)
            # A full digest is always retained for safe future rollback, regardless of copy verification mode.
            entry["copied_snapshot"] = snapshot(temporary, "sha256")
            entry["state"] = "publishing"
            persist_manifest(db, config, manifest)
            no_symlinks(dst)
            if case_collision(dst):
                raise SafetyError(f"Destination collision: {dst}")
            publish_no_replace(temporary, dst)
            entry["destination_snapshot"] = check_snapshot(dst, entry["copied_snapshot"], identity=False)
            entry["state"] = "published"
            entry["verification_status"] = "verified"
            persist_manifest(db, config, manifest)
            check_snapshot(dst, entry["destination_snapshot"])
            if entry["operation"] == "move":
                check_snapshot(src, entry["snapshot"])
                entry["state"] = "removing_source"
                persist_manifest(db, config, manifest)
                src.unlink()
                fsync_directory(src.parent)
                entry["source_removed"] = True
            entry["state"] = "complete"
            if entry["media_id"]:
                media_data = json.loads(
                    db.execute("SELECT data FROM media WHERE id=?", (entry["media_id"],)).fetchone()[0]
                )
                media_data["managed_destination"] = str(dst)
                db.execute("UPDATE media SET data=? WHERE id=?", (dumps(media_data), entry["media_id"]))
                stat = dst.stat()
                db.execute(
                    "UPDATE media SET path=?,root=?,size=?,mtime_ns=?,device=?,inode=? WHERE id=?",
                    (
                        str(dst),
                        str(config.destination_root),
                        stat.st_size,
                        stat.st_mtime_ns,
                        stat.st_dev,
                        stat.st_ino,
                        entry["media_id"],
                    ),
                )
                if entry["operation"] == "copy":
                    db.execute(
                        "INSERT OR REPLACE INTO metadata VALUES(?,?)",
                        (
                            "retained:" + str(src),
                            dumps(
                                {"size": entry["snapshot"]["size"], "mtime_ns": entry["snapshot"]["mtime_ns"]}
                            ),
                        ),
                    )
            persist_manifest(db, config, manifest)
            log_entry(config, manifest, entry)
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
            # Keep publication state for conservative recovery. Never remove an uncertain destination.
            entry["failed_at"] = entry["state"]
            entry["state"] = "failed"
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()
            manifest["status"] = "partial_failure"
            db.execute("UPDATE plans SET status='failed' WHERE id=?", (plan_id,))
            persist_manifest(db, config, manifest)
            log_entry(config, manifest, entry)
            return manifest
    manifest["status"] = "completed"
    db.execute("UPDATE plans SET status='applied' WHERE id=?", (plan_id,))
    persist_manifest(db, config, manifest)
    event(db, "apply", {"operation_id": operation_id, "plan_id": plan_id, "status": manifest["status"]})
    return manifest
