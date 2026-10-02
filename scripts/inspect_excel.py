"""Read-only full workbook profile, JSON to stdout; no source writes."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

from master_film_curator.catalog.excel_reader import MAIN, sheet_rows


def inspect(path):
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = {sheet.title: sheet_rows(sheet) for sheet in workbook}
        master = sheets[MAIN]
        by_id = {r["Master ID"]: r for r in master}
        result = {"source": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "sheets": {}}
        for name, rows in sheets.items():
            headers = list(rows[0]) if rows else []
            result["sheets"][name] = {
                "rows": len(rows),
                "columns": headers,
                "missing": {h: sum(r[h] is None for r in rows) for h in headers},
                "duplicate_ids": [k for k, v in Counter(r["Master ID"] for r in rows).items() if v > 1],
                "orphan_ids": sorted({r["Master ID"] for r in rows} - by_id.keys()),
            }
        result["duplicate_titles"] = {
            name: [
                {"id": r["Master ID"], "year": r["Year"], "director": r["Director / Creator"]}
                for r in master
                if r["Title"] == name
            ]
            for name, n in Counter(r["Title"] for r in master).items()
            if n > 1
        }
        result["year_values"] = sorted({str(r["Year"]) for r in master})
        result["tiers"] = dict(Counter(r["Rev07 Tier"] for r in master))
        result["priorities"] = dict(Counter(r["Rev07 Viewing Priority"] for r in master))
        result["ranking_disagreements"] = {
            name: sum(
                {k: v for k, v in r.items() if k != "Rank"}
                != {k: v for k, v in by_id[r["Master ID"]].items() if k != "Rank"}
                for r in sheets[name]
            )
            for name in ["Rev07_Taste_Fit_Ranking", "Rev07_Viewing_Priority_Ranking"]
        }
        result["series_hints"] = [
            {
                "Master ID": r["Master ID"],
                "Title": r["Title"],
                "Year": r["Year"],
                "Genre": r["Genre"],
            }
            for r in master
            if any(s in f"{r['Title']} {r['Genre']}".casefold() for s in ["miniseries", "tv series", "reality-tv", "tv-series"])
        ]
        return result
    finally:
        workbook.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("excel", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.excel), ensure_ascii=False, indent=2))
