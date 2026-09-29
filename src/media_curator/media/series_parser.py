import re
from pathlib import Path

TOKEN = re.compile(r"(?i)(?<![a-z0-9])(?:s(\d{1,2})e(\d{1,3})|(\d{1,2})x(\d{1,3}))(?!\d)")


def parse_series(path: Path) -> dict:
    match = TOKEN.search(path.stem)
    season = episode = None
    hint = False
    uncertain = False
    if match:
        season = int(match[1] or match[3])
        episode = int(match[2] or match[4])
        hint = True
        # Multi-episode bundles need manual handling, never silently rename as one episode.
        uncertain = bool(re.match(r"(?i)[ ._-]*(?:e\d|s\d|\d{1,3}(?:\D|$))", path.stem[match.end() :]))
    for parent in list(path.parents)[:3]:
        folder = re.fullmatch(r"(?i)(?:season|s)[ ._-]*(\d{1,2})", parent.name)
        if folder:
            hint = True
            folder_season = int(folder[1])
            if season is not None and season != folder_season:
                uncertain = True
            season = folder_season if season is None else season
            if episode is None:
                em = re.match(r"(?i)(?:episode[ ._-]*|ep?[ ._-]*)(\d{1,3})(?!\d)", path.stem)
                if em:
                    episode = int(em[1])
            break
    if hint and (episode is None or episode == 0):
        uncertain = True
    return {"season": season, "episode": episode, "series_hint": hint, "series_uncertain": uncertain}
