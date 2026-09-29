import re
import unicodedata
from pathlib import Path

RELEASE = re.compile(
    r"(?<!\w)(?:\d{3,4}p|4k|uhd|bluray|blu[ ._-]?ray|b[dr]rip|web[ ._-]?(?:dl|rip)|"
    r"[xh][ ._-]?26[45]|hevc|avc|aac(?:\d)?|dts|atmos|hdr\d*|dv|remux|"
    r"yify|yts|psa|rarbg|10bit|8bit|ddp?\d?|multi|dual[ ._-]?audio)(?!\w)",
    re.IGNORECASE,
)
YEAR = re.compile(r"(?<!\d)(18\d{2}|19\d{2}|20\d{2}|21\d{2})(?!\d)")
EPISODE = re.compile(r"(?i)(?<!\w)(?:s\d{1,2}e\d{1,3}|\d{1,2}x\d{1,3})(?!\d)")


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"\(tv series\)", "", value)
    value = value.replace("&", " and ")
    return " ".join("".join(c if c.isalnum() else " " for c in value).split())


def parse_filename(value: str) -> dict:
    # Only recognized extensions: Path.stem would eat the last token in dotted folder names.
    value = re.sub(
        r"\.(mkv|mp4|avi|mov|m4v|wmv|ts|m2ts|webm|srt|ass|ssa|sub|idx|vtt|nfo)$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = unicodedata.normalize("NFKC", value)
    release = RELEASE.search(value)
    episode = EPISODE.search(value)
    years = [m for m in YEAR.finditer(value) if normalize_title(value[: m.start()])]
    # A year-like title (1917 / 2001) alone is not a release year.
    year = years[0] if years else None
    stops = [m.start() for m in [release, episode, year] if m]
    title = value[: min(stops)] if stops else value
    # Canonical names without year may still carry an em-dash director.
    title = title.split(" — ")[0]
    title = re.sub(r"^\[[^]]+\]\s*", "", title)
    title = re.sub(
        r"(?i)(?:[ ._-]+(?:en|eng|fa|fas|per|fr|de|es|subbed|dubbed|multisub|farsi|persian))+$",
        "",
        title.strip(" ._-"),
    )
    return {"title": normalize_title(title), "year": int(year.group()) if year else None}


def parse_path(path: Path) -> dict:
    from media_curator.media.series_parser import parse_series

    parsed = parse_filename(path.name)
    series = parse_series(path)
    if series["series_hint"] and re.fullmatch(r"(?i)(?:episode|ep?|)\s*\d{1,3}", parsed["title"]):
        parsed["title"] = ""
    if not parsed["title"] or series["series_hint"]:
        for folder in list(path.parents)[:3]:
            if re.fullmatch(r"(?i)(?:season|s)[ ._-]*\d{1,2}", folder.name):
                continue
            parent = parse_filename(folder.name)
            if parent["title"] and (not parsed["title"] or parent["year"] or series["series_hint"]):
                # A recognizable title in the episode filename takes precedence.
                if not parsed["title"] or parsed["title"].isdigit():
                    parsed["title"] = parent["title"]
                if parsed["year"] is None:
                    parsed["year"] = parent["year"]
                break
    return {**parsed, **series}
