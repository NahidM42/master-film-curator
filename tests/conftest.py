import pytest

from master_film_curator.config import Config
from master_film_curator.db.sqlite import connect, dumps


def record(mid=1, title="Persona", year=1966, **kw):
    return {
        "master_id": mid,
        "title": title,
        "year": year,
        "director": "Ingmar Bergman",
        "genre": "Drama",
        "channel_score": 95,
        "taste_fit": 90,
        "tier": "S",
        "viewing_priority": "1 — Essential",
        "analytical_note": "note",
        "calibration_reason": "reason",
        "is_series": False,
        "not_for_channel": False,
        "not_for_my_taste": False,
        "skip_for_now": False,
        "top_content_candidate": True,
        **kw,
    }


@pytest.fixture
def cfg(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    return Config(
        sources=[source],
        destination_root=tmp_path / "out",
        excel_path=tmp_path / "catalog.xlsx",
        database_path=tmp_path / "state.sqlite",
        reports_root=tmp_path / "reports",
        logs_root=tmp_path / "logs",
        expected_catalog_count=None,
    )


@pytest.fixture
def db(cfg):
    with connect(cfg.database_path, lock=False) as conn:
        for r in [
            record(),
            record(2, "Shame", 1968),
            record(3, "Shame", 2011, director="Steve McQueen"),
            record(4, "Show", 2019, is_series=True),
        ]:
            conn.execute("INSERT INTO catalog VALUES(?,?)", (r["master_id"], dumps(r)))
        conn.execute("INSERT INTO metadata VALUES('catalog_sha256','fixture')")
        yield conn
