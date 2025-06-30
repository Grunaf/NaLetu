from typing import List
from pydantic import ConfigDict, BaseModel


class DayVariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    name: str


class DayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    day_order: int
    variant: DayVariantRead | None = None


class DayVariantCreate(BaseModel):
    name: str
    est_budget: int
    is_default: bool
    segments: List["SegmentCreate"]


class DayCreate(BaseModel):
    day_order: int
    day_variants: List[DayVariantCreate]
