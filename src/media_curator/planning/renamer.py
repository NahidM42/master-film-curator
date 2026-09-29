import hashlib
import re
from pathlib import Path

RESERVED = re.compile(r"(?i)^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)")


def windows_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def safe_component(value: str, limit: int = 110) -> str:
    clean = re.sub(r'[\\/:*?"<>|\x00-\x1f]', " - ", value)
    clean = re.sub(r"\s+", " ", clean).strip(" .") or "Untitled"
    if RESERVED.match(clean):
        clean = "_" + clean
    if windows_length(clean) > limit or len(clean.encode("utf-8")) > 240:
        suffix = "~" + hashlib.sha256(value.encode()).hexdigest()[:10]
        while clean and (
            windows_length(clean + suffix) > limit or len((clean + suffix).encode("utf-8")) > 240
        ):
            clean = clean[:-1]
        clean = clean.rstrip(" .") + suffix
    return clean


def canonical_base(record) -> str:
    return f"{record['title']} ({record['year']}) — {record['director']}"


def destination_for(record, parsed, quality_path, config, extension, variant="") -> tuple[Path, list[dict]]:
    original = canonical_base(record)
    is_series = record["is_series"] or parsed["series_hint"]
    if is_series and (parsed["series_uncertain"] or parsed["season"] is None or parsed["episode"] is None):
        raise ValueError("Uncertain episode identity; no rename permitted")
    season = f"Season {parsed['season']:02d}" if is_series else None
    raw_stem = (
        f"{record['title']} - S{parsed['season']:02d}E{parsed['episode']:02d}" if is_series else original
    )
    prefix = config.destination_root / quality_path
    # Reserve 24 characters for sidecar language and unknown-language suffixes.
    # Budget accounts for both repeated movie names, season and file extension.
    budget = config.max_path_length - windows_length(str(prefix)) - len(extension) - 27
    if season:
        budget -= len(season) + 1
    component_limit = min(config.max_component_length, budget // 2)
    if component_limit < 24:
        raise ValueError("Destination root too long for a safe Windows path")
    folder = safe_component(original, component_limit)
    stem = safe_component(raw_stem + variant, component_limit)
    dest = prefix / folder
    if season:
        dest /= season
    dest /= stem + extension.lower()
    if windows_length(str(dest)) > config.max_path_length:
        raise ValueError("Path exceeds configured Windows path limit")
    transformations = []
    for before, after in [(original, folder), (raw_stem + variant, stem)]:
        if before != after:
            transformations.append({"original": before, "safe": after})
    return dest, transformations


def sidecar_name(sidecar: Path, video: Path, new_stem: str) -> str:
    tail = (
        sidecar.stem[len(video.stem) :] if sidecar.stem.casefold().startswith(video.stem.casefold()) else ""
    )
    languages = re.findall(
        r"(?i)(?:^|[ ._-])(en|eng|fa|fas|per|fr|fre|ar|de|es|it|ja|ko|zh|ru|forced|sdh|hi)(?=$|[ ._-])",
        sidecar.stem,
    )
    if re.fullmatch(r"\.sidecar-[a-f0-9]{8}", tail):
        suffix = tail
    elif tail and re.fullmatch(r"(?:[ ._-][a-zA-Z]{2,8})+", tail):
        suffix = "." + ".".join(t for t in re.split("[ ._-]+", tail) if t)
    elif languages:
        suffix = "." + ".".join(languages)
    else:
        suffix = ".sidecar-" + hashlib.sha256(sidecar.name.encode()).hexdigest()[:8]
    return safe_component(new_stem, 150) + suffix.lower() + sidecar.suffix.lower()
