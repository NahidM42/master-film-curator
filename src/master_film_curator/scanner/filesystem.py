import json
import os
from pathlib import Path

from master_film_curator.db.sqlite import dumps, event
from master_film_curator.matching.normalize import parse_path
from master_film_curator.scanner.media_detection import VIDEO_EXTENSIONS, is_extra


def scan(db, config) -> dict:
    counts = {"indexed": 0, "changed": 0, "errors": [], "skipped_symlinks": 0}
    roots = list(dict.fromkeys(config.sources))
    if config.destination_root.is_dir() and config.destination_root not in roots:
        roots.append(config.destination_root)
    seen = set()
    # Offline roots must never leave apparently available matches in inventory.
    db.execute("UPDATE media SET present=0")
    for root in roots:
        if root.is_symlink() or not root.is_dir():
            counts["errors"].append({"path": str(root), "error": "Root unavailable or symlink"})
            continue

        def walk_error(error):
            counts["errors"].append({"path": error.filename, "error": str(error)})

        for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
            dirs[:] = sorted(d for d in dirs if not Path(parent, d).is_symlink())
            for filename in sorted(files):
                path = Path(parent, filename).absolute()
                if path.suffix.lower() not in VIDEO_EXTENSIONS or str(path) in seen:
                    continue
                seen.add(str(path))
                if path.is_symlink():
                    counts["skipped_symlinks"] += 1
                    continue
                try:
                    stat = path.stat()
                    parsed = parse_path(path)
                    data = {
                        **parsed,
                        "filename": filename,
                        "extension": path.suffix.lower(),
                        "parents": [str(p) for p in path.parents],
                        "extra": is_extra(path, root),
                    }
                    old = db.execute("SELECT * FROM media WHERE path=?", (str(path),)).fetchone()
                    if old:
                        changed = (old["size"], old["mtime_ns"], old["device"], old["inode"]) != (
                            stat.st_size,
                            stat.st_mtime_ns,
                            stat.st_dev,
                            stat.st_ino,
                        )
                        previous_data = json.loads(old["data"])
                        if not changed and previous_data.get("managed_destination") == str(path):
                            for key in (
                                "title",
                                "year",
                                "season",
                                "episode",
                                "series_hint",
                                "series_uncertain",
                                "managed_destination",
                            ):
                                data[key] = previous_data[key]
                        db.execute(
                            "UPDATE media SET root=?,size=?,mtime_ns=?,device=?,inode=?,present=1,data=? WHERE id=?",
                            (
                                str(root),
                                stat.st_size,
                                stat.st_mtime_ns,
                                stat.st_dev,
                                stat.st_ino,
                                dumps(data),
                                old["id"],
                            ),
                        )
                        if changed:
                            db.execute(
                                "UPDATE media SET master_id=NULL,confidence=0,status='unmatched',candidates='[]',"
                                "probe=NULL,quality='Unknown',probe_error=NULL WHERE id=?",
                                (old["id"],),
                            )
                            db.execute(
                                "DELETE FROM decisions WHERE media_id=? AND action!='ignore'", (old["id"],)
                            )
                            counts["changed"] += 1
                    else:
                        status = "extra" if data["extra"] else "unmatched"
                        retained = db.execute(
                            "SELECT value FROM metadata WHERE key=?", ("retained:" + str(path),)
                        ).fetchone()
                        if retained:
                            saved = json.loads(retained[0])
                            if (saved["size"], saved["mtime_ns"]) == (stat.st_size, stat.st_mtime_ns):
                                status = "retained_source"
                        db.execute(
                            "INSERT INTO media(path,root,size,mtime_ns,device,inode,data,status) VALUES(?,?,?,?,?,?,?,?)",
                            (
                                str(path),
                                str(root),
                                stat.st_size,
                                stat.st_mtime_ns,
                                stat.st_dev,
                                stat.st_ino,
                                dumps(data),
                                status,
                            ),
                        )
                    counts["indexed"] += 1
                except (OSError, ValueError) as exc:
                    counts["errors"].append({"path": str(path), "error": str(exc)})
    db.execute("UPDATE plans SET status='stale' WHERE status='planned'")
    event(db, "scan", counts)
    return counts
