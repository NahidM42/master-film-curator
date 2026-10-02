import json
import shutil
import subprocess
from pathlib import Path

from master_film_curator.db.sqlite import dumps, event
from master_film_curator.media.quality import resolution_class


def require_ffprobe(executable: str = "ffprobe") -> str:
    found = shutil.which(executable)
    if not found:
        raise RuntimeError(
            "ffprobe is missing. On Ubuntu/WSL: sudo apt update && sudo apt install ffmpeg. "
            "Or set ffprobe in config.yaml to its installed executable path. No apply allowed."
        )
    return str(Path(found).absolute())


def probe(path: Path, executable="ffprobe", timeout=45) -> dict:
    binary = require_ffprobe(executable)
    result = subprocess.run(
        [binary, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    data = json.loads(result.stdout)
    videos = [
        s
        for s in data.get("streams", [])
        if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")
    ]
    if not videos:
        raise ValueError("No video stream")
    stream = max(videos, key=lambda s: (s.get("width") or 0) * (s.get("height") or 0))
    fmt = data.get("format", {})

    def number(v, cast):
        try:
            return cast(v)
        except (TypeError, ValueError):
            return None

    return {
        "width": number(stream.get("width"), int),
        "height": number(stream.get("height"), int),
        "codec": stream.get("codec_name"),
        "duration": number(stream.get("duration", fmt.get("duration")), float),
        "bitrate": number(stream.get("bit_rate", fmt.get("bit_rate")), int),
        "raw": data,
    }


def run_quality(db, config) -> dict:
    require_ffprobe(config.ffprobe)
    counts = {"probed": 0, "failed": 0}
    for row in db.execute("SELECT * FROM media WHERE present=1").fetchall():
        try:
            path = Path(row["path"])
            stat = path.stat()
            if (stat.st_size, stat.st_mtime_ns) != (row["size"], row["mtime_ns"]):
                raise ValueError("File changed since scan; rescan before probing")
            data = probe(path, config.ffprobe, config.probe_timeout)
            quality = resolution_class(data["width"], data["height"], config.quality)
            db.execute(
                "UPDATE media SET probe=?,quality=?,probe_error=NULL WHERE id=?",
                (dumps(data), quality, row["id"]),
            )
            counts["probed"] += 1
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            db.execute(
                "UPDATE media SET probe=NULL,quality='Unknown',probe_error=? WHERE id=?",
                (str(exc), row["id"]),
            )
            counts["failed"] += 1
    db.execute("UPDATE plans SET status='stale' WHERE status='planned'")
    event(db, "quality", counts)
    return counts
