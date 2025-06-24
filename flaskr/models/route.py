from datetime import time
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, Index, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flaskr.models.models import db


if TYPE_CHECKING:
    from .city import City
    from .poi import POI


class Route(db.Model):
    __tablename__ = "route"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    duration_days: Mapped[int]
    estimated_budget_rub: Mapped[int]
    days: Mapped[list["Day"]] = relationship(back_populates="route")
    img: Mapped[str]

    cities: Mapped[list["RouteCity"]] = relationship(
        order_by="RouteCity.order",
        cascade="all, delete-orphan"
    )


class Day(db.Model):
    __tablename__ = "day"
    id: Mapped[int] = mapped_column(primary_key=True)
    day_order: Mapped[int]
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    route: Mapped["Route"] = relationship(back_populates="days")

    default_variant: Mapped["DayVariant"] = relationship(
        primaryjoin="DayVariant.day_id == Day.id and DayVariant.is_default == True",
        overlaps="variants, day",
    )
    variants: Mapped[list["DayVariant"]] = relationship(
        order_by="DayVariant.id",
        back_populates="day",
        primaryjoin="DayVariant.day_id == Day.id",
        cascade="all, delete-orphan",
    )


class DayVariant(db.Model):
    __tablename__ = "day_variant"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    est_budget: Mapped[int]
    day_id: Mapped[int] = mapped_column(ForeignKey("day.id"))
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)

    day: Mapped["Day"] = relationship(
        back_populates="variants", foreign_keys=[day_id]
    )

    __table_args__ = (
        Index(
            "only_one_default_variant",
            day_id,
            is_default,
            unique=True,
            postgresql_where=("is_default"),
        ),
    )


class RouteCity(db.Model):
    __tablename__ = "route_city"

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))
    order: Mapped[int]

    # связь обратно к маршруту
    city: Mapped["City"] = relationship()
    route: Mapped["Route"] = relationship(back_populates="cities")


class Segment(db.Model):
    __tablename__ = "segment"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("day_variant.id"))
    type: Mapped[int] = mapped_column(SmallInteger)
    order: Mapped[int]
    start_time: Mapped[time | None]
    end_time: Mapped[time | None]

    variant: Mapped["DayVariant"] = relationship()

    attached_next_segment_id: Mapped[int | None] = mapped_column(
        ForeignKey("segment.id"), default=None
    )
    attached_next_segment: Mapped["Segment"] = relationship()

    poi_id: Mapped[int | None] = mapped_column(
        ForeignKey("poi.id"), default=None
    )
    poi: Mapped["POI"] = relationship()

    lodging_name: Mapped[str | None] = mapped_column(default=None)

    city_id: Mapped[int] = mapped_column(ForeignKey("route_city.id"))
    city: Mapped["RouteCity"] = relationship()
