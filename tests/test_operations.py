from pathlib import Path

import pytest
from test_planning import prepare

from master_film_curator.matching.matcher import match_all
from master_film_curator.operations.mover import apply_plan
from master_film_curator.operations.rollback import rollback
from master_film_curator.operations.verifier import SafetyError
from master_film_curator.planning.planner import create_plan
from master_film_curator.scanner.filesystem import scan


@pytest.fixture(autouse=True)
def fake_probe_available(monkeypatch):
    monkeypatch.setattr("master_film_curator.operations.mover.require_ffprobe", lambda _: "/fake/ffprobe")


def test_dry_run(db, cfg):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)
    before = p.read_bytes()
    assert apply_plan(db, cfg, plan["id"])["status"] == "dry_run"
    assert p.read_bytes() == before and not cfg.destination_root.exists() and not cfg.logs_root.exists()
    with pytest.raises(SafetyError, match="approval"):
        apply_plan(db, cfg, plan["id"], dry_run=False)


def test_move_rollback_and_idempotency(db, cfg):
    p = prepare(db, cfg)
    side = p.with_name("Lanterns.at.Noon.1966.en.srt")
    side.write_bytes(b"subtitle")
    plan = create_plan(db, cfg)
    applied = apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    assert applied["status"] == "completed" and not p.exists() and not side.exists()
    assert all(Path(e["destination"]).exists() for e in applied["entries"])
    assert (cfg.logs_root / applied["operation_id"] / "rollback_manifest.json").exists()
    assert apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)["status"] == "already_applied"
    scan(db, cfg)
    match_all(db, cfg)
    assert create_plan(db, cfg)["entries"] == []
    assert rollback(db, cfg, applied["operation_id"])["status"] == "dry_run"
    assert not p.exists()
    result = rollback(db, cfg, applied["operation_id"], dry_run=False, confirmed=True)
    assert (
        result["status"] == "rolled_back" and p.read_bytes() == b"fake" and side.read_bytes() == b"subtitle"
    )


@pytest.mark.parametrize("delete", [False, True])
def test_cross_drive(db, cfg, monkeypatch, delete):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)
    monkeypatch.setattr("master_film_curator.operations.mover.same_filesystem", lambda *args: False)
    applied = apply_plan(
        db, cfg, plan["id"], dry_run=False, confirmed=True, delete_source_after_verify=delete
    )
    assert applied["status"] == "completed"
    assert p.exists() != delete
    scan(db, cfg)
    match_all(db, cfg)
    assert create_plan(db, cfg)["entries"] == []
    assert (
        rollback(db, cfg, applied["operation_id"], dry_run=False, confirmed=True)["status"] == "rolled_back"
    )
    assert p.read_bytes() == b"fake"


def test_collision_after_plan(db, cfg):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)
    dest = Path(plan["entries"][0]["destination"])
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"dont overwrite")
    with pytest.raises(SafetyError, match="collision"):
        apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    assert p.exists() and dest.read_bytes() == b"dont overwrite"


def test_source_changed(db, cfg):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)
    p.write_bytes(b"changed")
    with pytest.raises(SafetyError, match="changed"):
        apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)


def test_interrupted_copy(db, cfg, monkeypatch):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)

    def fail(src, dst):
        dst.write_bytes(b"partial")
        raise OSError("disk disconnected")

    monkeypatch.setattr("master_film_curator.operations.mover.copy_payload", fail)
    result = apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    assert result["status"] == "partial_failure" and p.read_bytes() == b"fake"
    assert not list(cfg.destination_root.rglob("*.partial"))
    assert not Path(plan["entries"][0]["destination"]).exists()


def test_corrupt_copy_preserves_source(db, cfg, monkeypatch):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)
    monkeypatch.setattr(
        "master_film_curator.operations.mover.copy_payload", lambda src, dst: dst.write_bytes(b"evil")
    )
    result = apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    assert result["status"] == "partial_failure" and p.read_bytes() == b"fake"


def test_rollback_refuses_modified_destination(db, cfg):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)
    applied = apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    dest = Path(applied["entries"][0]["destination"])
    dest.write_bytes(b"user changed")
    r = rollback(db, cfg, applied["operation_id"], dry_run=False, confirmed=True)
    assert r["status"] == "rollback_incomplete" and dest.read_bytes() == b"user changed" and not p.exists()


def test_symlink_destination(db, cfg, tmp_path):
    prepare(db, cfg)
    plan = create_plan(db, cfg)
    cfg.destination_root.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(SafetyError, match="Symlink"):
        apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)


def test_stale_plan(db, cfg):
    prepare(db, cfg)
    plan = create_plan(db, cfg)
    scan(db, cfg)
    with pytest.raises(SafetyError, match="stale"):
        apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)


def test_long_title_and_unknown_language_are_idempotent(db, cfg):
    from conftest import record

    from master_film_curator.db.sqlite import dumps

    title = "This Is An Exceptionally Long Movie Title With Many More Words Than The Path Can Hold"
    r = record(5, title, 2020)
    db.execute("INSERT INTO catalog VALUES(?,?)", (5, dumps(r)))
    p = prepare(db, cfg, title + ".2020.mkv")
    p.with_suffix(".srt").write_text("unknown language subtitle")
    plan = create_plan(db, cfg)
    assert plan["entries"] and not plan["blocked"], plan["blocked"]
    applied = apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    assert applied["status"] == "completed"
    scan(db, cfg)
    match_all(db, cfg)
    again = create_plan(db, cfg)
    assert again["entries"] == [] and not again["blocked"]


def test_corruption_after_publication_does_not_remove_source(db, cfg, monkeypatch):
    from master_film_curator.operations import mover

    original_publish = mover.publish_no_replace
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)

    def corrupt(source, destination):
        original_publish(source, destination)
        destination.write_bytes(b"corrupt after publication")

    monkeypatch.setattr(mover, "publish_no_replace", corrupt)
    result = apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    assert result["status"] == "partial_failure"
    assert p.read_bytes() == b"fake"


def test_disk_full_preflight(db, cfg, monkeypatch):
    from types import SimpleNamespace

    p = prepare(db, cfg)
    plan = create_plan(db, cfg)
    monkeypatch.setattr("master_film_curator.operations.mover.shutil.disk_usage", lambda _: SimpleNamespace(free=0))
    with pytest.raises(SafetyError, match="space"):
        apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    assert p.read_bytes() == b"fake" and not cfg.destination_root.exists()


def test_locked_source_copy_failure(db, cfg, monkeypatch):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)

    def locked(*args):
        raise PermissionError("file is locked")

    monkeypatch.setattr("master_film_curator.operations.mover.copy_payload", locked)
    assert apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)["status"] == "partial_failure"
    assert p.exists()


def test_atomic_publish_does_not_overwrite_racing_file(tmp_path):
    from master_film_curator.operations.mover import publish_no_replace

    src, dst = tmp_path / "temp", tmp_path / "existing"
    src.write_bytes(b"new")
    dst.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        publish_no_replace(src, dst)
    assert src.read_bytes() == b"new" and dst.read_bytes() == b"existing"


def test_rollback_occupied_source(db, cfg):
    p = prepare(db, cfg)
    plan = create_plan(db, cfg)
    applied = apply_plan(db, cfg, plan["id"], dry_run=False, confirmed=True)
    p.write_bytes(b"new user file")
    result = rollback(db, cfg, applied["operation_id"], dry_run=False, confirmed=True)
    assert result["status"] == "rollback_incomplete" and p.read_bytes() == b"new user file"
    assert Path(applied["entries"][0]["destination"]).exists()
