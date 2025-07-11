import datetime
from typing import Any, Optional

from sqlalchemy import JSON, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models import DataEntryMixin, db


class MealPlace(DataEntryMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    coords: Mapped[str]
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))

    type: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    open_time: Mapped[Optional[datetime.time]]
    close_time: Mapped[Optional[datetime.time]]

    cuisine: Mapped[int] = mapped_column(SmallInteger)
    avg_check_rub: Mapped[Optional[int]]
    rating: Mapped[Optional[float]]
    website: Mapped[Optional[str]]

    city: Mapped["City"] = relationship()


class SimularMealPlaceCache(DataEntryMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    meal_place_id: Mapped[int] = mapped_column(ForeignKey("meal_place.id"))
    data_json: Mapped[dict[str, Any]] = mapped_column(type_=JSON)
