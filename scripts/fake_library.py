"""Build only synthetic files in a new directory; never accepts existing library roots."""

import json
import shutil
import subprocess
from pathlib import Path


def make_library(root: Path, ffmpeg: str):
    root.mkdir(parents=True, exist_ok=False)
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/library.json"
    spec = json.loads(fixture.read_text())
    templates = root / "templates"
    templates.mkdir()
    for entry in spec["videos"]:
        path = root / entry["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if entry.get("invalid"):
            path.write_bytes(b"Synthetic invalid video for failure testing")
            continue
        dimensions = entry["size"]
        template = templates / (dimensions + ".mkv")
        if not template.exists():
            subprocess.run(
                [
                    ffmpeg,
                    "-nostdin",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    f"color=c=black:s={dimensions}:r=5",
                    "-t",
                    "0.4",
                    "-c:v",
                    "libx264",
                    "-threads",
                    "1",
                    "-preset",
                    "ultrafast",
                    str(template),
                ],
                check=True,
                timeout=60,
            )
        shutil.copy2(template, path)
    for relative, content in spec["sidecars"].items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return [root / "drive-a", root / "drive-b"]
