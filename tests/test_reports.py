import csv
import json

from test_planning import prepare

from media_curator.planning.planner import create_plan
from media_curator.reports.csv_reports import csv_value, generate_reports


def test_reports(db, cfg):
    prepare(db, cfg)
    create_plan(db, cfg)
    folder = generate_reports(db, cfg)
    expected = {
        "library_inventory.csv",
        "matched.csv",
        "missing_from_library.csv",
        "unmatched_on_disk.csv",
        "ambiguous_matches.csv",
        "duplicate_candidates.csv",
        "below_1080.csv",
        "above_1080_4k.csv",
        "unknown_resolution.csv",
        "rename_plan.csv",
        "move_plan.csv",
        "operation_summary.json",
        "rollback_manifest.json",
        "summary.md",
    }
    assert {p.name for p in folder.iterdir()} == expected
    with (folder / "missing_from_library.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert {int(r["master_id"]) for r in rows} == {2, 3, 4}
    summary = json.loads((folder / "operation_summary.json").read_text())
    assert summary["confirmed_files"] == 1
    assert not cfg.destination_root.exists()


def test_formula_escape():
    assert csv_value('=HYPERLINK("evil")').startswith("'")
    assert csv_value(42) == 42
