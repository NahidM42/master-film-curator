import pytest
from conftest import record

from master_film_curator.config import MatchingConfig
from master_film_curator.matching.confidence import decide
from master_film_curator.matching.matcher import candidates_for, match_all, save_decision
from master_film_curator.scanner.filesystem import scan


@pytest.mark.parametrize(
    "title,year,status,reason",
    [
        ("lanterns at noon", 1966, "matched", "exact_title_year"),
        ("lanterns at noon", 1967, "matched", "title_year_plus_minus_one"),
        ("lanterns at non", 1966, "manual_review", "fuzzy_title_year"),
        ("lanterns at noon", 2000, "manual_review", "title_only"),
        ("lanterns at noon", None, "manual_review", "title_only"),
        ("totally unrelated", 2020, "unmatched", None),
    ],
)
def test_matching(title, year, status, reason):
    c = candidates_for({"title": title, "year": year}, "", [record()])
    assert decide(c, MatchingConfig()) == status
    if reason:
        assert c[0]["reason"] == reason


def test_ambiguous():
    c = candidates_for(
        {"title": "silent harbor", "year": None},
        "",
        [record(1, "Silent Harbor", 1968), record(2, "Silent Harbor", 2011)],
    )
    assert decide(c, MatchingConfig()) == "manual_review"
    c = candidates_for(
        {"title": "silent harbor", "year": 2011},
        "",
        [record(1, "Silent Harbor", 1968), record(2, "Silent Harbor", 2011)],
    )
    assert decide(c, MatchingConfig()) == "matched" and c[0]["master_id"] == 2


def test_scan_roots_review_persistence(db, cfg, tmp_path):
    p = cfg.sources[0] / "Lanterns.at.Noon.1966.1080p.mkv"
    p.write_bytes(b"fake")
    second = tmp_path / "second"
    second.mkdir()
    (second / "unknown.mp4").write_bytes(b"other")
    cfg.sources += [second, cfg.sources[0]]
    before = p.stat()
    assert scan(db, cfg)["indexed"] == 2
    assert match_all(db, cfg) == {"matched": 1, "unmatched": 1}
    row = db.execute("SELECT * FROM media WHERE path=?", (str(p),)).fetchone()
    save_decision(db, row["id"], "accept", 1)
    scan(db, cfg)
    match_all(db, cfg)
    assert db.execute("SELECT status FROM media WHERE id=?", (row["id"],)).fetchone()[0] == "manual_accepted"
    assert p.stat().st_mtime_ns == before.st_mtime_ns and p.read_bytes() == b"fake"
    p.write_bytes(b"changed")
    scan(db, cfg)
    assert db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 0


def test_multiple_and_episodes(db, cfg):
    for name in [
        "Lanterns.at.Noon.1966.mkv",
        "Lanterns.at.Noon.1966.720p.mp4",
        "Meridian.House.1973.S01E01.mkv",
        "Meridian.House.1973.S01E02.mkv",
    ]:
        (cfg.sources[0] / name).write_bytes(b"fake")
    scan(db, cfg)
    assert match_all(db, cfg) == {"matched": 2, "multiple_candidates": 2}


def test_missing_root_and_extras(db, cfg):
    (cfg.sources[0] / "Lanterns.at.Noon.1966.sample.mkv").write_bytes(b"fake")
    scan(db, cfg)
    assert match_all(db, cfg) == {"extra": 1}
    cfg.sources[0].rename(cfg.sources[0].with_name("offline"))
    assert scan(db, cfg)["errors"]
    assert db.execute("SELECT COUNT(*) FROM media WHERE present=1").fetchone()[0] == 0


def test_symlink_not_followed(db, cfg, tmp_path):
    external = tmp_path / "outside.mkv"
    external.write_bytes(b"fake")
    (cfg.sources[0] / "Lanterns.at.Noon.1966.mkv").symlink_to(external)
    assert scan(db, cfg)["skipped_symlinks"] == 1
    assert db.execute("SELECT COUNT(*) FROM media").fetchone()[0] == 0
