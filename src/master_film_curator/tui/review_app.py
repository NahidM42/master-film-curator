import json

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from master_film_curator.matching.matcher import save_decision


class ReviewApp(App):
    """Optional local review UI. Choosing any Master ID is supported through the input."""

    TITLE = "Media Curator — Manual Review"
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    DataTable { height: 1fr; }
    #details { height: 6; overflow-y: auto; }
    Input { width: 28; }
    Horizontal { height: 3; }
    #message { height: 2; }
    """

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="queue", cursor_type="row")
        yield Static("Select a row to inspect candidates.", id="details", markup=False)
        with Horizontal():
            yield Input(placeholder="Master ID (any catalog ID)", id="master")
            yield Button("Accept / choose", id="accept", variant="success")
            yield Button("Reject", id="reject")
            yield Button("Not in catalog", id="not_in_catalog")
            yield Button("Ignore permanently", id="ignore", variant="warning")
        yield Static("", id="message", markup=False)
        yield Footer()

    def on_mount(self):
        table = self.query_one("#queue", DataTable)
        table.add_columns("File ID", "Path", "Status")
        self.refresh_queue()

    def refresh_queue(self):
        table = self.query_one("#queue", DataTable)
        table.clear()
        self.rows = {
            r["id"]: dict(r)
            for r in self.db.execute(
                "SELECT * FROM media WHERE present=1 AND status IN "
                "('manual_review','multiple_candidates','unmatched','rejected') ORDER BY id"
            )
        }
        for mid, row in self.rows.items():
            table.add_row(str(mid), row["path"], row["status"], key=str(mid))
        self.selected = None

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if event.row_key.value is None:
            return
        self.selected = int(event.row_key.value)
        row = self.rows.get(self.selected)
        if row:
            candidates = json.loads(row["candidates"])
            self.query_one("#details", Static).update(json.dumps(candidates, ensure_ascii=False, indent=2))
            self.query_one("#master", Input).value = str(candidates[0]["master_id"]) if candidates else ""

    def on_button_pressed(self, event: Button.Pressed):
        action = event.button.id
        try:
            if self.selected is None:
                raise ValueError("Select a file first")
            mid = int(self.query_one("#master", Input).value) if action == "accept" else None
            save_decision(self.db, self.selected, action, mid)
            self.db.commit()
            self.query_one("#message", Static).update(
                f"Saved {action} for file {self.selected}. Rebuild the plan."
            )
            self.refresh_queue()
        except (ValueError, TypeError) as exc:
            self.query_one("#message", Static).update(str(exc))
