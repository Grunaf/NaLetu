from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models import db


if TYPE_CHECKING:
    from .city import City
    from .poi import POI


class Route(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    duration_days: Mapped[int]
    estimated_budget_rub: Mapped[int]
    days: Mapped[list["Day"]] = relationship(back_populates="route")
    img: Mapped[str]

    cities: Mapped[list["RouteCity"]] = relationship(
        order_by="RouteCity.order",
        back_populates="route",
        cascade="all, delete-orphan",
    )


class Day(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    day_order: Mapped[int]
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))

    route: Mapped["Route"] = relationship()
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
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    est_budget: Mapped[int]
    day_id: Mapped[int] = mapped_column(ForeignKey("day.id"))
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)

    segments: Mapped["Segment"] = relationship(back_populates="variant")
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
    city: Mapped["City"] = relationship(back_populates="route_cities")
    route: Mapped["Route"] = relationship(back_populates="cities")


class Segment(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("day_variant.id"))
    type: Mapped[int] = mapped_column(SmallInteger)
    order: Mapped[int]
    start_time: Mapped[time | None]
    end_time: Mapped[time | None]

    variant: Mapped["DayVariant"] = relationship(back_populates="segment")

    attached_next_segment_id: Mapped[int | None] = mapped_column(
        ForeignKey("segment.id"), default=None
    )
    attached_next_segment: Mapped["Segment"] = relationship()

    poi_id: Mapped[int | None] = mapped_column(
        ForeignKey("poi.id"), default=None
    )
    poi: Mapped["POI"] = relationship(back_populates="segment")

    lodging_name: Mapped[str | None] = mapped_column(default=None)

    city_id: Mapped[int] = mapped_column(ForeignKey("route_city.id"))
    city: Mapped["RouteCity"] = relationship()
