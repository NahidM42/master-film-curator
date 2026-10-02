"""End-to-end acceptance demo using newly generated media only."""

import argparse
import hashlib
import json
from pathlib import Path

import yaml
from fake_library import make_library

from master_film_curator.catalog.excel_reader import import_catalog
from master_film_curator.config import Config
from master_film_curator.db.sqlite import connect
from master_film_curator.matching.matcher import match_all
from master_film_curator.media.ffprobe import require_ffprobe, run_quality
from master_film_curator.operations.mover import apply_plan
from master_film_curator.operations.rollback import rollback
from master_film_curator.planning.planner import create_plan
from master_film_curator.reports.csv_reports import generate_reports
from master_film_curator.scanner.filesystem import scan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="Must be a NEW directory; refuses existing paths"
    )
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument(
        "--excel",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "sample-data" / "Rev07_Sample_Catalog_60.xlsx",
    )
    args = parser.parse_args()
    root = args.output.absolute()
    if root.exists():
        parser.error("Output already exists. Choose a new directory; nothing was modified.")
    probe = require_ffprobe(args.ffprobe)
    sources = make_library(root, args.ffmpeg)
    cfg = Config(
        sources=sources,
        destination_root=root / "curated",
        excel_path=args.excel.absolute(),
        database_path=root / "state.sqlite",
        reports_root=root / "reports",
        logs_root=root / "logs",
        expected_catalog_count=60,
        ffprobe=probe,
    )
    (root / "config.yaml").write_text(yaml.safe_dump(json.loads(cfg.model_dump_json())), encoding="utf-8")
    original = {
        p: hashlib.sha256(p.read_bytes()).hexdigest()
        for source in sources
        for p in source.rglob("*")
        if p.is_file()
    }
    result = {}
    with connect(cfg.database_path) as db:
        result["catalog_count"] = import_catalog(db, cfg.excel_path, cfg.expected_catalog_count)
        result["scan"] = scan(db, cfg)
        result["matches"] = match_all(db, cfg)
        result["quality"] = run_quality(db, cfg)
        plan = create_plan(db, cfg)
        result["plan"] = plan["summary"]
        result["plan_id"] = plan["id"]
        if plan["blocked"] or plan["summary"]["destination_collisions"]:
            raise RuntimeError(f"Synthetic plan blocked: {plan['blocked']}")
        result["dry_run"] = apply_plan(db, cfg, plan["id"])["status"]
        assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in original.items())
        result["reports_before"] = str(generate_reports(db, cfg))
        applied = apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
        result["operation_id"] = applied["operation_id"]
        result["apply_status"] = applied["status"]
        assert applied["status"] == "completed"
        scan(db, cfg)
        match_all(db, cfg)
        run_quality(db, cfg)
        repeat = create_plan(db, cfg)
        result["second_plan_entries"] = len(repeat["entries"])
        assert not repeat["entries"] and not repeat["blocked"]
        result["reports_after_apply"] = str(generate_reports(db, cfg))
        rolled = rollback(db, cfg, applied["operation_id"], dry_run=False, confirmed=True)
        result["rollback_status"] = rolled["status"]
        assert rolled["status"] == "rolled_back"
        assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in original.items())
        result["all_original_bytes_restored"] = True
        result["reports_after_rollback"] = str(generate_reports(db, cfg))
    (root / "acceptance-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
