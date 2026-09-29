from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MatchingConfig(StrictModel):
    auto_accept: float = Field(95, ge=85, le=100)
    review_threshold: float = Field(70, ge=0, le=100)
    ambiguity_margin: float = Field(5, ge=0, le=100)

    @model_validator(mode="after")
    def order(self):
        if self.review_threshold >= self.auto_accept:
            raise ValueError("review_threshold must be below auto_accept")
        return self


class QualityConfig(StrictModel):
    min_1080_width: int = Field(1800, gt=0)
    min_1080_height: int = Field(780, gt=0)
    nominal_1080_width: int = Field(1900, gt=0)


class Classification(StrictModel):
    primary: Literal["viewing_priority", "channel_tier"] = "viewing_priority"
    secondary: Literal["viewing_priority", "channel_tier"] = "channel_tier"
    strategy: Literal["priority_then_tier", "tier_then_priority"] | None = None

    @model_validator(mode="after")
    def distinct(self):
        if self.primary == self.secondary and self.strategy is None:
            raise ValueError("classification dimensions must differ")
        return self


class OperationMode(StrictModel):
    dry_run: bool = True


class Config(StrictModel):
    sources: list[Path] = Field(default_factory=list)
    destination_root: Path
    excel_path: Path
    database_path: Path = Path(".state/curator.sqlite3")
    reports_root: Path = Path("reports")
    logs_root: Path = Path("logs")
    expected_catalog_count: int | None = 570
    classification: Classification = Field(default_factory=Classification)
    operation_mode: OperationMode = Field(default_factory=OperationMode)
    verification_mode: Literal["size", "quick_hash", "sha256"] = "sha256"
    matching: MatchingConfig = Field(default_factory=MatchingConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    ffprobe: str = "ffprobe"
    probe_timeout: float = Field(45, gt=0)
    max_path_length: int = Field(240, ge=100, le=32000)
    max_component_length: int = Field(110, ge=32, le=240)


def load_config(path: Path) -> Config:
    path = path.expanduser().resolve()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg = Config.model_validate(raw)
    for key in ["destination_root", "excel_path", "database_path", "reports_root", "logs_root"]:
        value = getattr(cfg, key).expanduser()
        setattr(cfg, key, (path.parent / value).absolute())
    if "/" in cfg.ffprobe or cfg.ffprobe.startswith("~"):
        cfg.ffprobe = str((path.parent / Path(cfg.ffprobe).expanduser()).absolute())
    cfg.sources = [(path.parent / p.expanduser()).absolute() for p in cfg.sources]
    return cfg
