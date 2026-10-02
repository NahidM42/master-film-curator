import hashlib
from pathlib import Path

import pytest

from master_film_curator.catalog.excel_reader import import_catalog, read_catalog
from master_film_curator.config import Config, load_config
from master_film_curator.db.sqlite import catalog_records, connect

WORKBOOK = Path(__file__).parents[1] / "sample-data" / "Rev07_Sample_Catalog_60.xlsx"


def test_sample_workbook_readonly(tmp_path):
    original = hashlib.sha256(WORKBOOK.read_bytes()).hexdigest()
    with connect(tmp_path / "db.sqlite") as db:
        assert import_catalog(db, WORKBOOK, 60) == 60
        assert import_catalog(db, WORKBOOK, 60) == 60
        rows = catalog_records(db)
        assert len({r["master_id"] for r in rows}) == 60
        assert sum(r["not_for_channel"] for r in rows) == 8
        assert sum(r["not_for_my_taste"] for r in rows) == 7
        assert sum(r["skip_for_now"] for r in rows) == 10
        assert sum(r["top_content_candidate"] for r in rows) == 12
        a = next(r for r in rows if r["master_id"] == 1001)
        assert (a["title"], a["tier"], a["channel_score"]) == ("Lanterns at Noon", "S", 100)
        assert a["raw"]["Rev07 Channel"] == a["channel_score"]
    assert hashlib.sha256(WORKBOOK.read_bytes()).hexdigest() == original


def test_count_guard():
    with pytest.raises(ValueError, match="Expected"):
        read_catalog(WORKBOOK, 59)


def test_relative_config(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("sources: [input]\ndestination_root: output\nexcel_path: a.xlsx\n")
    c = load_config(p)
    assert c.sources == [tmp_path / "input"]
    assert c.operation_mode.dry_run
    with pytest.raises(ValueError):
        Config(destination_root="out", excel_path="x", matching={"auto_accept": 50})


def test_database_command_lock(tmp_path):
    with connect(tmp_path / "locked.sqlite"):
        with pytest.raises(RuntimeError, match="Another curator"):
            with connect(tmp_path / "locked.sqlite"):
                pass
