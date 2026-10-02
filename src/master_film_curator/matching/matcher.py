import json
from pathlib import Path

from rapidfuzz.fuzz import ratio

from master_film_curator.db.sqlite import catalog_records, dumps, event, now
from master_film_curator.matching.confidence import decide
from master_film_curator.matching.normalize import normalize_title


def candidates_for(parsed: dict, context: str, catalog: list[dict]) -> list[dict]:
    candidates = []
    title = parsed["title"]
    if not title:
        return candidates
    for record in catalog:
        expected = normalize_title(record["title"])
        similarity = ratio(title, expected)
        year = parsed.get("year")
        difference = abs(year - record["year"]) if year else None
        director = any(
            normalize_title(d) in normalize_title(context)
            for d in record["director"].split(";")
            if len(normalize_title(d)) > 3
        )
        if similarity == 100 and difference == 0:
            confidence, reason = 100, "exact_title_year"
        elif similarity == 100 and difference == 1:
            confidence, reason = 97, "title_year_plus_minus_one"
        elif similarity == 100 and difference is None and director:
            confidence, reason = 96, "title_director"
        elif similarity == 100:
            confidence, reason = (82 if difference is None else 72), "title_only"
        elif difference in (0, 1) and similarity >= 70:
            confidence, reason = min(94, similarity - (2 if difference else 0)), "fuzzy_title_year"
        elif similarity >= 80 and director and difference is None:
            confidence, reason = min(90, similarity), "fuzzy_title_director"
        else:
            confidence, reason = min(69, similarity * 0.7), "weak_title"
        if confidence >= 50:
            candidates.append(
                {
                    "master_id": record["master_id"],
                    "title": record["title"],
                    "year": record["year"],
                    "similarity": round(similarity, 2),
                    "confidence": round(confidence, 2),
                    "year_difference": difference,
                    "reason": reason,
                }
            )
    return sorted(candidates, key=lambda c: (-c["confidence"], c["master_id"]))[:5]


def match_all(db, config) -> dict:
    catalog = catalog_records(db)
    if not catalog:
        raise ValueError("Import the catalog before matching")
    for row in db.execute("SELECT * FROM media WHERE present=1").fetchall():
        data = json.loads(row["data"])
        if row["status"] == "retained_source":
            continue
        decision = db.execute("SELECT * FROM decisions WHERE media_id=?", (row["id"],)).fetchone()
        if decision and (
            decision["action"] == "ignore"
            or (decision["size"], decision["mtime_ns"]) == (row["size"], row["mtime_ns"])
        ):
            status = {
                "accept": "manual_accepted",
                "reject": "rejected",
                "not_in_catalog": "not_in_catalog",
                "ignore": "ignored",
            }[decision["action"]]
            db.execute(
                "UPDATE media SET master_id=?,confidence=?,status=? WHERE id=?",
                (decision["master_id"], 100 if decision["action"] == "accept" else 0, status, row["id"]),
            )
            continue
        if data["extra"]:
            db.execute("UPDATE media SET status='extra',master_id=NULL WHERE id=?", (row["id"],))
            continue
        candidates = candidates_for(data, str(Path(row["path"])), catalog)
        status = decide(candidates, config.matching)
        best = candidates[0] if candidates else None
        if best and (
            data["series_uncertain"]
            or (
                next(c for c in catalog if c["master_id"] == best["master_id"])["is_series"]
                and data["episode"] is None
            )
        ):
            status = "manual_review"
        db.execute(
            "UPDATE media SET master_id=?,confidence=?,status=?,candidates=? WHERE id=?",
            (
                best["master_id"] if best and status != "unmatched" else None,
                best["confidence"] if best else 0,
                status,
                dumps(candidates),
                row["id"],
            ),
        )
    # Distinct series episodes are separate works within one title; duplicate episode encodes are reviewed.
    groups = {}
    for row in db.execute("SELECT * FROM media WHERE present=1 AND status IN ('matched','manual_accepted')"):
        data = json.loads(row["data"])
        key = (row["master_id"], data.get("season"), data.get("episode"))
        groups.setdefault(key, []).append(row)
    for rows in groups.values():
        if len(rows) > 1:
            for row in rows:
                if row["status"] != "manual_accepted":
                    db.execute("UPDATE media SET status='multiple_candidates' WHERE id=?", (row["id"],))
    db.execute("UPDATE plans SET status='stale' WHERE status='planned'")
    counts = {
        r[0]: r[1] for r in db.execute("SELECT status,COUNT(*) FROM media WHERE present=1 GROUP BY status")
    }
    event(db, "match", counts)
    return counts


def save_decision(db, media_id: int, action: str, master_id: int | None = None):
    if action not in {"accept", "reject", "not_in_catalog", "ignore"}:
        raise ValueError("Invalid review action")
    row = db.execute("SELECT * FROM media WHERE id=?", (media_id,)).fetchone()
    if row is None:
        raise ValueError("Unknown media ID")
    if action == "accept":
        if not db.execute("SELECT 1 FROM catalog WHERE master_id=?", (master_id,)).fetchone():
            raise ValueError("Accept requires an existing Master ID")
    else:
        master_id = None
    db.execute(
        "INSERT OR REPLACE INTO decisions VALUES(?,?,?,?,?,?)",
        (media_id, action, master_id, row["size"], row["mtime_ns"], now()),
    )
    status = {
        "accept": "manual_accepted",
        "reject": "rejected",
        "not_in_catalog": "not_in_catalog",
        "ignore": "ignored",
    }[action]
    db.execute(
        "UPDATE media SET status=?,master_id=?,confidence=? WHERE id=?",
        (status, master_id, 100 if action == "accept" else 0, media_id),
    )
    db.execute("UPDATE plans SET status='stale' WHERE status='planned'")
    event(db, "manual_decision", {"media_id": media_id, "action": action, "master_id": master_id})
