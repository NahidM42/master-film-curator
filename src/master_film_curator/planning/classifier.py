from pathlib import Path

from master_film_curator.media.quality import quality_folder

PRIORITIES = {"1": "01_Essential", "2": "02_High", "3": "03_Medium", "4": "04_Low", "5": "05_Skip_For_Now"}


def classification_path(record, quality, config) -> Path:
    priority = PRIORITIES.get(record["viewing_priority"].split()[0])
    if not priority or record["tier"] not in {"S", "A", "B", "C", "D"}:
        raise ValueError("Unsupported catalog classification")
    c = config.classification
    tier_first = c.strategy == "tier_then_priority" or (c.strategy is None and c.primary == "channel_tier")
    parts = [record["tier"], priority] if tier_first else [priority, record["tier"]]
    quality_dir = quality_folder(quality)
    if quality_dir:
        parts = ["90_Quality_Review", quality_dir, *parts]
    return Path(*parts)
