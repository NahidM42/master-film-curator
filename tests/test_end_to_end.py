import importlib.util
import json
import shutil
from pathlib import Path

import pytest

from master_film_curator.catalog.excel_reader import import_catalog
from master_film_curator.config import Config
from master_film_curator.db.sqlite import connect
from master_film_curator.matching.matcher import match_all
from master_film_curator.media.ffprobe import run_quality
from master_film_curator.operations.mover import apply_plan
from master_film_curator.operations.rollback import rollback
from master_film_curator.planning.planner import create_plan
from master_film_curator.reports.csv_reports import generate_reports
from master_film_curator.scanner.filesystem import scan

ROOT = Path(__file__).parents[1]


def binary(name):
    found = shutil.which(name)
    if found:
        return found
    local = ROOT / ".state/linux" / name
    if local.exists():
        return str(local)
    pytest.skip("Real FFmpeg integration requires ffmpeg and ffprobe; see README")


def test_real_ffprobe_end_to_end(tmp_path):
    ffmpeg, ffprobe = binary("ffmpeg"), binary("ffprobe")
    spec = importlib.util.spec_from_file_location("fake_library", ROOT / "scripts/fake_library.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sources = module.make_library(tmp_path / "fake", ffmpeg)
    config = Config(
        sources=sources,
        destination_root=tmp_path / "curated",
        excel_path=ROOT / "private-catalog.xlsx",
        database_path=tmp_path / "db.sqlite",
        reports_root=tmp_path / "reports",
        logs_root=tmp_path / "logs",
        ffprobe=ffprobe,
        max_path_length=300,
    )
    originals = {p: p.read_bytes() for source in sources for p in source.rglob("*") if p.is_file()}
    with connect(config.database_path) as db:
        assert import_catalog(db, config.excel_path) == 570
        assert scan(db, config)["indexed"] == 11
        counts = match_all(db, config)
        assert counts == {
            "matched": 6,
            "multiple_candidates": 2,
            "manual_review": 1,
            "extra": 1,
            "unmatched": 1,
        }
        assert run_quality(db, config) == {"probed": 10, "failed": 1}
        plan = create_plan(db, config)
        assert not plan["blocked"]
        assert plan["summary"]["files_to_move"] == 9
        assert plan["summary"]["below_1080_files"] == 1
        assert plan["summary"]["above_1080_files"] == 1
        assert plan["summary"]["unknown_resolution_files"] == 1
        assert apply_plan(db, config, plan["id"])["status"] == "dry_run"
        assert all(p.read_bytes() == b for p, b in originals.items())
        report = generate_reports(db, config)
        assert (
            json.loads((report / "operation_summary.json").read_text())["missing_unconfirmed_titles"] == 565
        )
        applied = apply_plan(db, config, plan["id"], dry_run=False, confirmed=True)
        assert applied["status"] == "completed"
        assert any("/Season 01/" in e["destination"] for e in applied["entries"])
        assert all(
            (sources[1] / name).exists()
            for name in ["Shame.mkv", "Unknown.Zyxw.2020.mkv", "Papillon.1973.720p.mkv"]
        )
        scan(db, config)
        match_all(db, config)
        run_quality(db, config)
        repeat = create_plan(db, config)
        assert not repeat["entries"] and not repeat["blocked"]
        result = rollback(db, config, applied["operation_id"], dry_run=False, confirmed=True)
        assert result["status"] == "rolled_back"
        assert all(p.read_bytes() == b for p, b in originals.items())
