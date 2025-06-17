import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, JSON, MetaData
from sqlalchemy.types import Boolean
from sqlalchemy.schema import Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

metadata = MetaData(
    naming_convention={
        "pk": "pk_%(table_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s"
})
db = SQLAlchemy(metadata=metadata)

class Route(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    duration_days: Mapped[int]
    estimated_budget_rub: Mapped[int]

    days: Mapped[list["Day"]] = relationship(back_populates="route")
    cities: Mapped[list["RouteCity"]] = relationship(
      order_by="RouteCity.order",
      back_populates="route",
      cascade="all, delete-orphan"
    )
    img: Mapped[str]


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_order = db.Column(db.Integer)
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))

    route: Mapped["Route"] = relationship() 
    default_variant: Mapped["DayVariant"] = relationship(primaryjoin="DayVariant.day_id == Day.id"
                                    " and DayVariant.is_default == True", overlaps="variants, day")
    variants: Mapped[list["DayVariant"]] = relationship(order_by="DayVariant.id", back_populates="day",
                            primaryjoin="DayVariant.day_id == Day.id", cascade="all, delete-orphan")


class DayVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    est_budget = db.Column(db.Integer)
    day_id = db.Column(db.Integer, ForeignKey("day.id"))
    is_default: Mapped[bool] = mapped_column(Boolean, server_default="True")

    segments = relationship("Segment", backref="variant")
    # lodgings = relationship("LodgingOption", backref="variant")
    day = relationship("Day", back_populates="variants", foreign_keys=[day_id])
    __table_args__ = (
        Index("only_one_default_variant", day_id, is_default, unique=True, postgresql_where=("is_default"))
    ,)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    yandex_code = db.Column(db.String, nullable=False)

    route_cities = relationship("RouteCity", back_populates="city") 


class RouteCity(db.Model):
    __tablename__ = "route_city"

    id           = db.Column(db.Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    city_id      = db.Column(db.Integer, ForeignKey("city.id"), nullable=False)
    order        = db.Column(db.Integer, nullable=False)

    # связь обратно к маршруту
    city =  relationship("City", back_populates="route_cities")
    route = relationship("Route", back_populates="cities")

class Segment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, ForeignKey("day_variant.id"))
    type = db.Column(db.String)  # poi, meal, transport_segment, transport_back
    order = db.Column(db.Integer, nullable=False)
    attached_next_segment_id = db.Column(db.Integer, ForeignKey("segment.id"))
    attached_next_segment = relationship("Segment")

    start_time = db.Column(db.Time, nullable=True)
    end_time   = db.Column(db.Time, nullable=True)

    poi_id = db.Column(db.Integer, ForeignKey("poi.id"))
    poi = relationship("POI", back_populates="segment")

    # Lodging
    lodging_name = db.Column(db.String)

    city_id   = db.Column(db.Integer, ForeignKey("route_city.id"))
    city      = relationship("RouteCity")

class POI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    must_see = db.Column(db.Boolean)
    open_time = db.Column(db.Time)
    close_time = db.Column(db.Time)
    rating = db.Column(db.Float)
    
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

    segment = relationship("Segment", back_populates="poi")

class TransitionOption(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    mode          = db.Column(db.String, nullable=False)   # пешком, автобус, такси…
    time_min      = db.Column(db.Integer, nullable=False)
    cost_rub      = db.Column(db.Integer, nullable=True)
    is_default    = db.Column(db.Boolean, default=False)
    segment_id    = db.Column(db.Integer, ForeignKey("segment.id"), nullable=False)



class PriceEntry(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str]
    object_id: Mapped[int]
    price: Mapped[int]
    updated_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now(), onupdate=datetime.datetime.now())
