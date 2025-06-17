import datetime

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from models.models import db

class MealPlace(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[Optional[str]]
    coords: Mapped[str]
    cuisine: Mapped[str]
    website: Mapped[Optional[str]]
    avg_check_rub: Mapped[Optional[int]]
    open_time: Mapped[Optional[datetime.time]]
    close_time: Mapped[Optional[datetime.time]]
    rating: Mapped[Optional[float]]
    updated_at: Mapped[datetime.datetime] = mapped_column(onupdate=datetime.datetime.now())
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))

class SimularMealPlaceCache(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    meal_place_id: Mapped[int] = mapped_column(ForeignKey("meal_place.id"))
    data_json: Mapped[JSON] = mapped_column(type_=JSON)
    updated_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now())

    # def to_dict(self):
    #     return {"id": self.id, "meal_place_id": self.meal_place_id, "data_json": self.data_json, ""}
