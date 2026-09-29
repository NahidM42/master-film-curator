import asyncio
import json

import yaml
from typer.testing import CliRunner

from media_curator.cli.commands import app
from media_curator.matching.matcher import match_all
from media_curator.scanner.filesystem import scan

runner = CliRunner()


def config_file(cfg):
    p = cfg.database_path.parent / "config.yaml"
    p.write_text(yaml.safe_dump(json.loads(cfg.model_dump_json())))
    return p


def test_cli_status_and_review(db, cfg):
    (cfg.sources[0] / "Shame.mkv").write_bytes(b"fake")
    scan(db, cfg)
    match_all(db, cfg)
    db.commit()
    p = config_file(cfg)
    result = runner.invoke(app, ["-c", str(p), "status"])
    assert result.exit_code == 0 and "manual_review" in result.stdout
    result = runner.invoke(
        app, ["-c", str(p), "review", "--file-id", "1", "--action", "accept", "--master-id", "2"]
    )
    assert result.exit_code == 0
    assert db.execute("SELECT status FROM media").fetchone()[0] == "manual_accepted"


def test_doctor_missing_probe(cfg):
    p = config_file(cfg)
    result = runner.invoke(app, ["-c", str(p), "doctor"])
    assert result.exit_code == 1 and "ffprobe" in result.stdout


def test_tui_accept(db, cfg):
    import pytest

    pytest.importorskip("textual")
    from media_curator.tui.review_app import ReviewApp

    (cfg.sources[0] / "Shame.mkv").write_bytes(b"fake")
    scan(db, cfg)
    match_all(db, cfg)

    async def exercise():
        ui = ReviewApp(db)
        async with ui.run_test(size=(160, 35)) as pilot:
            await pilot.pause()
            ui.selected = 1
            ui.query_one("#master").value = "2"
            await pilot.click("#accept")
            await pilot.pause()
            assert db.execute("SELECT status FROM media WHERE id=1").fetchone()[0] == "manual_accepted"

    asyncio.run(exercise())
