import hashlib
import json
import subprocess
from pathlib import Path
from uuid import uuid4

from master_film_curator.db.sqlite import catalog_records, dumps, event, now
from master_film_curator.matching.normalize import parse_filename
from master_film_curator.media.ffprobe import probe
from master_film_curator.operations.verifier import SafetyError, case_collision, digest, snapshot
from master_film_curator.planning.classifier import classification_path
from master_film_curator.planning.renamer import destination_for, safe_component, sidecar_name, windows_length
from master_film_curator.scanner.media_detection import SIDECAR_EXTENSIONS


def plan_digest(plan: dict) -> str:
    return hashlib.sha256(dumps(plan).encode()).hexdigest()


def related_sidecars(video: Path, siblings: list[dict]) -> tuple[list[Path], list[str]]:
    related = []
    ambiguous = []
    for p in sorted(video.parent.iterdir()):
        if p.suffix.lower() not in SIDECAR_EXTENSIONS or p.is_symlink() or not p.is_file():
            continue
        owners = []
        for sibling in siblings:
            v = Path(sibling["path"])
            if p.stem.casefold() == v.stem.casefold() or p.stem.casefold().startswith(
                v.stem.casefold() + "."
            ):
                owners.append(v)
        if not owners:
            parsed = parse_filename(p.name)
            owners = [
                Path(s["path"])
                for s in siblings
                if parse_filename(Path(s["path"]).name)["title"] == parsed["title"]
                and (parsed["year"] is None or parse_filename(Path(s["path"]).name)["year"] == parsed["year"])
            ]
        if (
            not owners
            and len(siblings) == 1
            and p.stem.casefold() in {"poster", "folder", "fanart", "cover", "movie", "metadata"}
        ):
            owners = [video]
        if not owners and p.suffix.lower() in {".srt", ".ass", ".ssa", ".sub", ".idx", ".vtt", ".nfo"}:
            ambiguous.append(str(p))
        if video in owners:
            if len(owners) == 1:
                related.append(p)
            else:
                ambiguous.append(str(p))
    return related, ambiguous


def collision_comparison(source_row, destination: Path, config) -> dict:
    comparison = {
        "source_size": source_row["size"],
        "source_quality": source_row["quality"],
        "source_probe": json.loads(source_row["probe"] or "{}"),
    }
    try:
        comparison["destination_size"] = destination.stat().st_size
        comparison["destination_digest"] = digest(destination, config.verification_mode)
        comparison["destination_probe"] = probe(destination, config.ffprobe, config.probe_timeout)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        comparison["inspection_error"] = str(exc)
    return comparison


def create_plan(db, config) -> dict:
    catalog = {r["master_id"]: r for r in catalog_records(db)}
    if not catalog:
        raise ValueError("Import catalog first")
    rows = [dict(r) for r in db.execute("SELECT * FROM media WHERE present=1 ORDER BY path")]
    plan = {
        "id": uuid4().hex,
        "created": now(),
        "catalog_sha256": db.execute("SELECT value FROM metadata WHERE key='catalog_sha256'").fetchone()[0],
        "destination_root": str(config.destination_root),
        "verification_mode": config.verification_mode,
        "entries": [],
        "blocked": [],
        "noops": [],
        "summary": {},
    }
    approved = [r for r in rows if r["status"] in {"matched", "manual_accepted"}]
    counts = {}
    for r in approved:
        d = json.loads(r["data"])
        key = (r["master_id"], d.get("season"), d.get("episode"))
        counts[key] = counts.get(key, 0) + 1
    owned = set()
    for row in approved:
        video = Path(row["path"])
        record = catalog[row["master_id"]]
        parsed = json.loads(row["data"])
        if row["status"] == "matched" and row["confidence"] < config.matching.auto_accept:
            plan["blocked"].append({"source": str(video), "reason": "confidence below threshold"})
            continue
        siblings = [
            r for r in rows if Path(r["path"]).parent == video.parent and not json.loads(r["data"])["extra"]
        ]
        try:
            key = (row["master_id"], parsed.get("season"), parsed.get("episode"))
            variant = f" [version-{row['id']}]" if counts[key] > 1 else ""
            dest, transforms = destination_for(
                record,
                parsed,
                classification_path(record, row["quality"], config),
                config,
                video.suffix,
                variant,
            )
            related, ambiguous = related_sidecars(video, siblings)
            if ambiguous:
                raise SafetyError("Shared sidecars need manual separation: " + ", ".join(ambiguous))
            bundle = [(video, dest, "video", transforms)]
            for sidecar in related:
                bundle.append(
                    (sidecar, dest.with_name(sidecar_name(sidecar, video, dest.stem)), "sidecar", [])
                )
            # Extras in a dedicated movie folder only; mixed folders stay untouched.
            if len(siblings) == 1 and not record["is_series"] and not parsed["series_hint"]:
                extras = [
                    r
                    for r in rows
                    if json.loads(r["data"])["extra"]
                    and (
                        Path(r["path"]).parent == video.parent
                        or Path(r["path"]).is_relative_to(video.parent / "Extras")
                        or Path(r["path"]).is_relative_to(video.parent / "extras")
                    )
                ]
                for extra in extras:
                    p = Path(extra["path"])
                    relative = p.relative_to(video.parent)
                    parts = relative.parts[1:] if relative.parts[0].casefold() == "extras" else relative.parts
                    target = dest.parent / "Extras" / Path(*(safe_component(part) for part in parts))
                    bundle.append((p, target, "extra", []))
                    for side in p.parent.iterdir():
                        if (
                            side.is_file()
                            and side.suffix.lower() in SIDECAR_EXTENSIONS
                            and side.stem.startswith(p.stem)
                        ):
                            bundle.append((side, target.with_name(side.name), "extra_sidecar", []))
            staged = []
            for source, target, kind, changes in bundle:
                if str(source) in owned:
                    continue
                if source == target:
                    plan["noops"].append(str(source))
                    continue
                if windows_length(str(target)) > config.max_path_length:
                    raise SafetyError(f"Path too long: {target}")
                snap = snapshot(source, config.verification_mode)
                if kind == "video" and (snap["size"], snap["mtime_ns"]) != (row["size"], row["mtime_ns"]):
                    raise SafetyError("Source changed since scan")
                collision = case_collision(target)
                staged.append(
                    {
                        "source": str(source),
                        "destination": str(target),
                        "kind": kind,
                        "media_id": row["id"] if kind == "video" else None,
                        "master_id": row["master_id"],
                        "confidence": row["confidence"],
                        "match_status": row["status"],
                        "snapshot": snap,
                        "quality": row["quality"],
                        "is_series": bool(parsed["series_hint"] or record["is_series"]),
                        "original_title": record["title"],
                        "transformations": changes,
                        "status": "collision" if collision else "ready",
                        "collision": str(collision) if collision else None,
                        "collision_details": collision_comparison(row, collision, config)
                        if collision
                        else None,
                        "bundle_id": row["id"],
                    }
                )
            plan["entries"].extend(staged)
            owned.update(e["source"] for e in staged)
        except (OSError, ValueError, SafetyError) as exc:
            plan["blocked"].append({"source": str(video), "reason": str(exc)})
    destinations = {}
    for e in plan["entries"]:
        key = e["destination"].casefold()
        if key in destinations:
            e["status"] = "collision"
            destinations[key]["status"] = "collision"
        destinations[key] = e
    colliding = {e["bundle_id"] for e in plan["entries"] if e["status"] == "collision"}
    for e in plan["entries"]:
        if e["bundle_id"] in colliding:
            e["status"] = "collision"
    ready = [e for e in plan["entries"] if e["status"] == "ready"]
    mids = {r["master_id"] for r in approved}
    plan["summary"] = {
        "files_to_move": len(ready),
        "files_to_rename": sum(Path(e["source"]).name != Path(e["destination"]).name for e in ready),
        "series_folders": len({str(Path(e["destination"]).parent.parent) for e in ready if e["is_series"]}),
        "below_1080_files": sum(e["kind"] == "video" and e["quality"] in {"SD", "720-class"} for e in ready),
        "above_1080_files": sum(
            e["kind"] == "video" and e["quality"] in {"1440-class", "2160 / 4K", "Higher"} for e in ready
        ),
        "unknown_resolution_files": sum(e["kind"] == "video" and e["quality"] == "Unknown" for e in ready),
        "ambiguous_files": sum(r["status"] in {"manual_review", "multiple_candidates"} for r in rows),
        "missing_catalog_titles": len(set(catalog) - mids),
        "destination_collisions": len(plan["entries"]) - len(ready),
        "estimated_bytes": sum(e["snapshot"]["size"] for e in ready),
        "blocked_files": len(plan["blocked"]),
        "already_organized": len(plan["noops"]),
    }
    db.execute("INSERT INTO plans VALUES(?,?,?,?)", (plan["id"], plan["created"], "planned", dumps(plan)))
    event(db, "plan", {"plan_id": plan["id"], **plan["summary"]})
    return plan


def load_plan(db, plan_id):
    row = db.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
    if not row:
        raise ValueError("Unknown plan ID")
    return json.loads(row["data"]), row["status"]
