from pathlib import Path

from conftest import record

from master_film_curator.matching.matcher import match_all, save_decision
from master_film_curator.operations.verifier import case_collision
from master_film_curator.planning.classifier import classification_path
from master_film_curator.planning.planner import create_plan
from master_film_curator.planning.renamer import destination_for, safe_component, sidecar_name, windows_length
from master_film_curator.scanner.filesystem import scan


def prepare(db, cfg, name="Persona.1966.1080p.mkv"):
    p = cfg.sources[0] / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"fake")
    scan(db, cfg)
    match_all(db, cfg)
    db.execute("UPDATE media SET quality='1080-class'")
    return p


def test_names():
    assert safe_component("CON") == "_CON"
    assert not any(c in safe_component('A/B:C*D?E"F<G>H|I') for c in '\\/:*?"<>|')
    assert safe_component("x" * 500) == safe_component("x" * 500)
    assert len(safe_component("فیلم" * 100).encode()) <= 240
    assert (
        sidecar_name(Path("Persona.1966.en.srt"), Path("Persona.1966.1080p.mkv"), "Persona (1966)")
        == "Persona (1966).en.srt"
    )
    assert ".sidecar-" in sidecar_name(Path("odd.srt"), Path("Persona.mkv"), "Persona")


def test_classification(cfg):
    assert str(classification_path(record(), "1080-class", cfg)) == "01_Essential/S"
    assert str(classification_path(record(), "2160 / 4K", cfg)).startswith("90_Quality_Review/Above_1080_4K")
    cfg.classification.strategy = "tier_then_priority"
    assert str(classification_path(record(), "1080-class", cfg)) == "S/01_Essential"


def test_plan_sidecars_and_no_mutation(db, cfg):
    p = prepare(db, cfg)
    s = p.with_name("Persona.1966.en.srt")
    s.write_text("subtitle")
    plan = create_plan(db, cfg)
    assert len(plan["entries"]) == 2 and plan["summary"]["files_to_move"] == 2
    assert p.exists() and s.exists() and not cfg.destination_root.exists()
    assert Path(plan["entries"][0]["destination"]).name == "Persona (1966) — Ingmar Bergman.mkv"


def test_plan_collisions_and_manual_only(db, cfg):
    prepare(db, cfg)
    plan = create_plan(db, cfg)
    target = Path(plan["entries"][0]["destination"])
    target.parent.mkdir(parents=True)
    target.write_text("existing")
    plan = create_plan(db, cfg)
    assert plan["summary"]["destination_collisions"] == 1
    db.execute("UPDATE media SET status='manual_review'")
    assert create_plan(db, cfg)["entries"] == []


def test_windows_case_collision(tmp_path):
    (tmp_path / "Movie.mkv").write_text("existing")
    assert case_collision(tmp_path / "movie.mkv") == tmp_path / "Movie.mkv"


def test_long_path_and_directors(cfg):
    r = record(title="long title " * 40, director="Director A; Director B; Director C")
    dest, changes = destination_for(r, {"series_hint": False}, Path("01_Essential/S"), cfg, ".mkv")
    assert windows_length(str(dest)) <= cfg.max_path_length
    assert changes


def test_uncertain_series_stays(db, cfg):
    prepare(db, cfg, "Show.2019.mkv")
    row = db.execute("SELECT id FROM media").fetchone()
    save_decision(db, row[0], "accept", 4)
    plan = create_plan(db, cfg)
    assert not plan["entries"] and plan["blocked"]


def test_extras_and_shared_sidecar(db, cfg):
    p = prepare(db, cfg, "Persona/Persona.1966.mkv")
    p.with_name("sample.mkv").write_bytes(b"extra")
    (p.parent / "poster.jpg").write_bytes(b"poster")
    scan(db, cfg)
    match_all(db, cfg)
    plan = create_plan(db, cfg)
    assert {e["kind"] for e in plan["entries"]} == {"video", "sidecar", "extra"}
    assert "/Extras/" in next(e["destination"] for e in plan["entries"] if e["kind"] == "extra")
