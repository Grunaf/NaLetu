import datetime
from typing import List, Optional
from flaskr.models.constants import MEAL

from pydantic import BaseModel, ConfigDict

from flaskr.constants import (
    START_BREAKFAST_TIME,
    START_DINNER_TIME,
    START_LUNCH_TIME,
)


class POIDTO(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, arbitrary_types_allowed=True
    )

    id: int
    name: str
    must_see: bool
    open_time: datetime.time
    close_time: datetime.time
    rating: float | None = None
    lat: float
    lon: float


class SimularMealPlaceCacheDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_place_id: int
    data_json: dict

    def to_dict(self):
        return {
            "id": self.id,
            "meal_plcae_id": self.meal_place_id,
            "data_json": self.data_json,
        }


class MealPlaceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    coords: str
    avg_check_rub: int
    open_time: datetime.time
    close_time: datetime.time


class SegmentDTO(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, arbitrary_types_allowed=True
    )

    id: int
    type: int
    start_time: datetime.time
    end_time: datetime.time
    poi: Optional[POIDTO] = None
    meal_places: Optional[List[MealPlaceDTO]] = None

    @property
    def meal_type(self) -> str | None:
        if self.type == MEAL:
            if (
                START_BREAKFAST_TIME <= self.start_time
                and self.start_time < START_LUNCH_TIME
            ):
                return "Завтрак"
            if (
                START_LUNCH_TIME <= self.start_time
                and self.start_time < START_DINNER_TIME
            ):
                return "Обед"
            if START_DINNER_TIME <= self.start_time:
                return "Ужин"
        return None




class SegmentCreate(BaseModel):
    type: str
    order: int
    start_time: datetime.time
    end_time: datetime.time
    poi_dgis_id: str | None = None
    city_id: int


class DayVariantCreate(BaseModel):
    name: str
    est_budget: int
    is_default: bool
    segments: List[SegmentCreate]


class DayCreate(BaseModel):
    day_order: int
    day_variants: List[DayVariantCreate]


class RouteCityCreate(BaseModel):
    city_id: int
    order: int


class RouteCreate(BaseModel):
    title: str
    duration_days: int
    estimated_budget_rub: int
    img: str
    city: RouteCityCreate
    days: List[DayCreate]

