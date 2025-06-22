import datetime
from typing import Optional

from sqlalchemy import JSON, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from .models import db


class MealPlace(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    coords: Mapped[str]
    open_time: Mapped[Optional[datetime.time]]
    close_time: Mapped[Optional[datetime.time]]
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))

    cuisine: Mapped[str]
    avg_check_rub: Mapped[Optional[int]]
    rating: Mapped[Optional[float]]
    website: Mapped[Optional[str]]

    updated_at: Mapped[datetime.datetime] = mapped_column(
        onupdate=datetime.datetime.now()
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now()
    )


class SimularMealPlaceCache(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    meal_place_id: Mapped[int] = mapped_column(ForeignKey("meal_place.id"))
    data_json: Mapped[JSON] = mapped_column(type_=JSON)

    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now(), onupdate=datetime.datetime.now()
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now()
    )
