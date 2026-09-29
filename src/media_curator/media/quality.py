from media_curator.config import QualityConfig


def resolution_class(width: int | None, height: int | None, config: QualityConfig | None = None) -> str:
    c = config or QualityConfig()
    if not width or not height or width <= 0 or height <= 0:
        return "Unknown"
    if width > 4096 or height > 2160:
        return "Higher"
    if width >= 3600 or height >= 2000:
        return "2160 / 4K"
    if width >= 2400 or height > 1200:
        return "1440-class"
    if width >= c.nominal_1080_width or (width >= c.min_1080_width and height >= c.min_1080_height):
        return "1080-class"
    if width >= 1200 or height >= 700:
        return "720-class"
    return "SD"


def quality_folder(quality: str) -> str | None:
    if quality == "1080-class":
        return None
    if quality in {"SD", "720-class"}:
        return "Below_1080"
    if quality in {"1440-class", "2160 / 4K", "Higher"}:
        return "Above_1080_4K"
    return "Unknown_Resolution"
