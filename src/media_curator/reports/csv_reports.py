import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from media_curator.db.sqlite import catalog_records

CATALOG_FIELDS = [
    "master_id",
    "title",
    "year",
    "director",
    "genre",
    "channel_score",
    "taste_fit",
    "tier",
    "viewing_priority",
    "top_content_candidate",
    "not_for_channel",
    "not_for_my_taste",
    "skip_for_now",
    "analytical_note",
    "calibration_reason",
]
MEDIA_FIELDS = [
    "id",
    "path",
    "filename",
    "extension",
    "size",
    "mtime_ns",
    "present",
    "status",
    "master_id",
    "confidence",
    "parsed_title",
    "parsed_year",
    "season",
    "episode",
    "parents",
    "width",
    "height",
    "codec",
    "duration",
    "bitrate",
    "quality",
    "probe_error",
    "candidates",
]
PLAN_FIELDS = [
    "source",
    "destination",
    "kind",
    "master_id",
    "confidence",
    "quality",
    "status",
    "collision",
    "transformations",
    "collision_details",
]


def csv_value(value):
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    # Opening reports in Excel must not execute formulas from filenames or catalog cells.
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: csv_value(row.get(k)) for k in fields})


def generate_reports(db, config) -> Path:
    folder = config.reports_root / (datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid4().hex[:6])
    folder.mkdir(parents=True, exist_ok=False)
    catalog = catalog_records(db)
    records = {r["master_id"]: r for r in catalog}
    inventory = []
    for row in db.execute("SELECT * FROM media ORDER BY path"):
        item = dict(row)
        data = json.loads(item.pop("data"))
        probe = json.loads(item.pop("probe") or "{}")
        item.update({k: v for k, v in data.items() if k not in {"title", "year"}})
        item.update(parsed_title=data["title"], parsed_year=data["year"])
        item.update({k: probe.get(k) for k in ["width", "height", "codec", "duration", "bitrate"]})
        item["candidates"] = json.loads(item["candidates"])
        inventory.append(item)
    present = [r for r in inventory if r["present"]]
    confirmed = [r for r in present if r["status"] in {"matched", "manual_accepted"}]
    mids = {r["master_id"] for r in confirmed}
    missing = [
        {
            **r,
            "pending_candidate_files": sum(
                x["master_id"] == r["master_id"] and x["status"] in {"manual_review", "multiple_candidates"}
                for x in present
            ),
        }
        for r in catalog
        if r["master_id"] not in mids
    ]
    ambiguous = []
    for r in present:
        if r["status"] in {"manual_review", "multiple_candidates"}:
            best = r["candidates"][0] if r["candidates"] else {}
            ambiguous.append(
                {
                    **r,
                    "proposed_title": best.get("title"),
                    "candidate_master_ids": [x["master_id"] for x in r["candidates"]],
                    "similarity_score": best.get("similarity"),
                    "year_difference": best.get("year_difference"),
                    "proposed_action": "DO NOT MODIFY; review required",
                }
            )
    duplicate_groups = {}
    for r in present:
        if r["master_id"] is not None and r["status"] in {
            "matched",
            "manual_accepted",
            "multiple_candidates",
        }:
            key = (r["master_id"], r.get("season"), r.get("episode"))
            duplicate_groups.setdefault(key, []).append(r)
    duplicates = [r for group in duplicate_groups.values() if len(group) > 1 for r in group]
    last = db.execute("SELECT data,status FROM plans ORDER BY created DESC LIMIT 1").fetchone()
    plan = json.loads(last[0]) if last else {"entries": [], "summary": {}, "blocked": []}
    write_csv(folder / "library_inventory.csv", inventory, MEDIA_FIELDS)
    write_csv(
        folder / "matched.csv",
        [{**r, **{k: v for k, v in records[r["master_id"]].items() if k != "master_id"}} for r in confirmed],
        MEDIA_FIELDS + CATALOG_FIELDS[1:],
    )
    write_csv(folder / "missing_from_library.csv", missing, CATALOG_FIELDS + ["pending_candidate_files"])
    write_csv(
        folder / "unmatched_on_disk.csv",
        [r for r in present if r["status"] in {"unmatched", "rejected", "not_in_catalog"}],
        MEDIA_FIELDS,
    )
    write_csv(
        folder / "ambiguous_matches.csv",
        ambiguous,
        MEDIA_FIELDS
        + [
            "proposed_title",
            "candidate_master_ids",
            "similarity_score",
            "year_difference",
            "proposed_action",
        ],
    )
    write_csv(folder / "duplicate_candidates.csv", duplicates, MEDIA_FIELDS)
    for name, classes in [
        ("below_1080", {"SD", "720-class"}),
        ("above_1080_4k", {"1440-class", "2160 / 4K", "Higher"}),
        ("unknown_resolution", {"Unknown"}),
    ]:
        write_csv(folder / (name + ".csv"), [r for r in present if r["quality"] in classes], MEDIA_FIELDS)
    write_csv(
        folder / "rename_plan.csv",
        [e for e in plan["entries"] if Path(e["source"]).name != Path(e["destination"]).name],
        PLAN_FIELDS,
    )
    write_csv(folder / "move_plan.csv", plan["entries"], PLAN_FIELDS)
    summary = {
        "catalog_count": len(catalog),
        "present_media": len(present),
        "offline_or_missing_files": len(inventory) - len(present),
        "confirmed_files": len(confirmed),
        "missing_unconfirmed_titles": len(missing),
        "ambiguous_files": len(ambiguous),
        "latest_plan_id": plan.get("id"),
        "latest_plan_status": last[1] if last else None,
        "plan_summary": plan["summary"],
        "blocked": plan["blocked"],
    }
    (folder / "operation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    operations = [json.loads(r[0]) for r in db.execute("SELECT manifest FROM operations ORDER BY created")]
    (folder / "rollback_manifest.json").write_text(
        json.dumps({"operations": operations}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    from media_curator.reports.summary import write_summary

    write_summary(folder / "summary.md", summary)
    return folder
