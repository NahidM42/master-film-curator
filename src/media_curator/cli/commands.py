import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from media_curator.catalog.excel_reader import import_catalog as do_import
from media_curator.catalog.excel_reader import read_catalog
from media_curator.config import load_config
from media_curator.db.sqlite import connect
from media_curator.matching.matcher import match_all, save_decision
from media_curator.media.ffprobe import require_ffprobe, run_quality
from media_curator.operations.mover import apply_plan, existing_ancestor
from media_curator.operations.rollback import rollback as do_rollback
from media_curator.planning.planner import create_plan, load_plan
from media_curator.reports.csv_reports import generate_reports
from media_curator.scanner.filesystem import scan as do_scan

app = typer.Typer(
    no_args_is_help=True,
    help="Local, safety-first Excel media curator. Media changes require explicit apply approval.",
)
console = Console()


@app.callback()
def options(
    ctx: typer.Context,
    config: Annotated[Path, typer.Option("--config", "-c", help="YAML configuration path")] = Path(
        "config.yaml"
    ),
):
    try:
        ctx.obj = load_config(config)
    except (OSError, ValueError) as exc:
        console.print(f"[red]Configuration error:[/red] {exc}", markup=False)
        raise typer.Exit(1) from exc


@contextmanager
def session(ctx):
    try:
        with connect(ctx.obj.database_path) as db:
            yield db, ctx.obj
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        console.print(f"Stopped safely: {exc}", style="red", markup=False)
        raise typer.Exit(1) from exc


def show_json(value):
    console.print_json(json.dumps(value, ensure_ascii=False, default=str))


def review_rows(db):
    return [
        dict(r)
        for r in db.execute(
            "SELECT id,path,status,candidates,master_id,confidence FROM media WHERE present=1 "
            "AND status IN ('manual_review','multiple_candidates','unmatched','rejected') ORDER BY id"
        )
    ]


@app.command()
def doctor(ctx: typer.Context):
    """Read-only checks: configuration, catalog, roots, destination, ffprobe and permissions."""
    cfg = ctx.obj
    checks = []
    checks.append(
        (
            "sources configured",
            bool(cfg.sources),
            "Add source roots to config.yaml" if not cfg.sources else str(len(cfg.sources)),
        )
    )
    for root in cfg.sources:
        checks.append(
            (str(root), root.is_dir() and os.access(root, os.R_OK | os.X_OK), "read/traverse permission")
        )
    try:
        rows = read_catalog(cfg.excel_path, cfg.expected_catalog_count)
        checks.append(("Excel", True, f"{len(rows)} records; opened read-only"))
    except (OSError, ValueError, KeyError) as exc:
        checks.append(("Excel", False, str(exc)))
    try:
        checks.append(("ffprobe", True, require_ffprobe(cfg.ffprobe)))
    except RuntimeError as exc:
        checks.append(("ffprobe", False, str(exc)))
    for label, path in [
        ("destination", cfg.destination_root),
        ("database", cfg.database_path.parent),
        ("reports", cfg.reports_root),
        ("logs", cfg.logs_root),
    ]:
        try:
            parent = existing_ancestor(path)
            from media_curator.operations.mover import mounted_windows_drive
            from media_curator.operations.verifier import no_symlinks

            mounted_windows_drive(path)
            no_symlinks(path)
            checks.append((label, os.access(parent, os.W_OK | os.X_OK), str(path)))
        except (OSError, RuntimeError) as exc:
            checks.append((label, False, str(exc)))
    table = Table("Check", "Result", "Details")
    for label, ok, detail in checks:
        table.add_row(label, "PASS" if ok else "FAIL", detail)
    console.print(table)
    if not all(ok for _, ok, _ in checks):
        raise typer.Exit(1)


@app.command("import-catalog")
def import_command(ctx: typer.Context):
    """Import the read-only Rev07 catalog. Never recompute scores or tiers."""
    with session(ctx) as (db, cfg):
        show_json({"imported": do_import(db, cfg.excel_path, cfg.expected_catalog_count)})


@app.command()
def scan(ctx: typer.Context):
    """Index video files across configured roots without modifying media."""
    with session(ctx) as (db, cfg):
        result = do_scan(db, cfg)
        show_json(result)
        if result["errors"]:
            console.print(
                "Some paths were unavailable; inventory reflects only accessible files.", style="yellow"
            )


@app.command("match")
def match_command(ctx: typer.Context):
    """Compute confidence-based matches, preserving manual decisions."""
    with session(ctx) as (db, cfg):
        show_json(match_all(db, cfg))


@app.command()
def quality(ctx: typer.Context):
    """Probe actual video dimensions using ffprobe."""
    with session(ctx) as (db, cfg):
        show_json(run_quality(db, cfg))


@app.command()
def review(
    ctx: typer.Context,
    media_id: Annotated[int | None, typer.Option("--file-id")] = None,
    action: Annotated[str | None, typer.Option(help="accept, reject, not_in_catalog, ignore")] = None,
    master_id: Annotated[int | None, typer.Option("--master-id")] = None,
    interactive: Annotated[bool, typer.Option("--interactive")] = False,
    tui: Annotated[bool, typer.Option("--tui")] = False,
):
    """List review queue or save a persistent decision. All TUI actions also have CLI options."""
    with session(ctx) as (db, cfg):
        if tui:
            try:
                from media_curator.tui.review_app import ReviewApp
            except ImportError as exc:
                raise RuntimeError("Install optional TUI: uv sync --extra tui") from exc
            ReviewApp(db).run()
            return
        if media_id is not None:
            if action is None:
                raise ValueError("--file-id requires --action")
            save_decision(db, media_id, action, master_id)
            show_json({"file_id": media_id, "action": action, "master_id": master_id})
            return
        if action is not None or master_id is not None:
            raise ValueError("--action and --master-id require --file-id")
        rows = review_rows(db)
        if not interactive:
            show_json(rows)
            return
        for row in rows:
            show_json(row)
            choice = typer.prompt("accept / reject / not_in_catalog / ignore / skip / quit", default="skip")
            if choice == "quit":
                break
            if choice == "skip":
                continue
            mid = typer.prompt("Master ID (any catalog record)", type=int) if choice == "accept" else None
            save_decision(db, row["id"], choice, mid)
            db.commit()


@app.command()
def plan(ctx: typer.Context):
    """Create a stored dry-run plan. No media file changes."""
    with session(ctx) as (db, cfg):
        result = create_plan(db, cfg)
        show_json({"plan_id": result["id"], "summary": result["summary"], "blocked": result["blocked"]})
        console.print("Inspect all proposed paths: media-curator --config <config.yaml> report", markup=False)


@app.command()
def report(ctx: typer.Context):
    """Write inventory, review, quality, missing-title and operation reports."""
    with session(ctx) as (db, cfg):
        console.print(str(generate_reports(db, cfg)), markup=False)


@app.command()
def apply(
    ctx: typer.Context,
    plan_id: Annotated[str, typer.Option("--plan", help="Saved plan ID")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Preview only; no confirmation or file changes")
    ] = False,
    yes: Annotated[
        bool, typer.Option("--yes", help="Explicit noninteractive approval of the displayed plan")
    ] = False,
    delete_source: Annotated[
        bool,
        typer.Option(
            "--delete-source-after-verify", help="Also remove cross-drive sources after verified copies"
        ),
    ] = False,
):
    """Explicit mutation command. Displays summary and requires confirmation (or --yes)."""
    with session(ctx) as (db, cfg):
        saved, status = load_plan(db, plan_id)
        show_json({"plan_id": plan_id, "status": status, **saved["summary"]})
        if not dry_run and not yes:
            if not typer.confirm("Apply this exact saved plan?", default=False):
                console.print("Cancelled. No media changes.")
                return
        result = apply_plan(
            db,
            cfg,
            plan_id,
            dry_run=dry_run,
            confirmed=yes or not dry_run,
            delete_source_after_verify=delete_source,
        )
        show_json(result)
        if result["status"] == "partial_failure":
            raise typer.Exit(1)


@app.command()
def rollback(
    ctx: typer.Context,
    operation_id: str,
    execute: Annotated[
        bool, typer.Option("--execute", help="Perform the safe reversals; default only previews")
    ] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Explicit approval of safe rollback actions")] = False,
):
    """Preview rollback safety; use --execute and confirmation to reverse operations."""
    with session(ctx) as (db, cfg):
        preview = do_rollback(db, cfg, operation_id)
        show_json(preview)
        if not execute:
            return
        if not yes and not typer.confirm("Reverse the safe operations shown above?", default=False):
            return
        result = do_rollback(db, cfg, operation_id, dry_run=False, confirmed=True)
        show_json(result)
        if result["status"] == "rollback_incomplete":
            raise typer.Exit(1)


@app.command()
def status(ctx: typer.Context):
    """Show catalog, inventory, plan and operation state."""
    with session(ctx) as (db, cfg):
        show_json(
            {
                "catalog": db.execute("SELECT COUNT(*) FROM catalog").fetchone()[0],
                "media": {
                    r[0]: r[1]
                    for r in db.execute("SELECT status,COUNT(*) FROM media WHERE present=1 GROUP BY status")
                },
                "plans": [
                    dict(r)
                    for r in db.execute("SELECT id,created,status FROM plans ORDER BY created DESC LIMIT 10")
                ],
                "operations": [
                    dict(r)
                    for r in db.execute(
                        "SELECT id,plan_id,created,status FROM operations ORDER BY created DESC LIMIT 10"
                    )
                ],
            }
        )
