import re
from pathlib import Path

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv", ".ts", ".m2ts", ".webm"}
SIDECAR_EXTENSIONS = {
    ".srt",
    ".ass",
    ".ssa",
    ".sub",
    ".idx",
    ".vtt",
    ".nfo",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}
EXTRA = re.compile(
    r"(?i)(?:^|[ ._\-/])(trailer|sample|interview|featurettes?|behind[ ._-]the[ ._-]scenes|extras)(?:$|[ ._\-/])"
)


def is_extra(path: Path, root: Path) -> bool:
    return bool(EXTRA.search(str(path.relative_to(root).with_suffix(""))))
