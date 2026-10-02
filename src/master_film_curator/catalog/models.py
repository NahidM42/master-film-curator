from typing import Literal

from pydantic import BaseModel, Field


class CatalogRecord(BaseModel):
    master_id: int = Field(gt=0)
    title: str = Field(min_length=1)
    year: int = Field(ge=1800, le=2200)
    director: str = Field(min_length=1)
    genre: str
    channel_score: float
    taste_fit: float
    tier: Literal["S", "A", "B", "C", "D"]
    viewing_priority: str
    analytical_note: str
    calibration_reason: str
    not_for_channel: bool = False
    not_for_my_taste: bool = False
    skip_for_now: bool = False
    top_content_candidate: bool = False
    is_series: bool = False
    raw: dict = Field(default_factory=dict)
