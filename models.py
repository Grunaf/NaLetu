from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func

db = SQLAlchemy()

class Route(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    duration_days = db.Column(db.Integer)
    estimated_budget_rub = db.Column(db.Integer)

    days = relationship("Day", backref="route")
    cities     = relationship(
      "RouteCity",
      order_by="RouteCity.order",
      back_populates="route",
      cascade="all, delete-orphan"
    )
    img = db.Column(db.String) 

class TripSession(db.Model):
    id           = db.Column(db.String, primary_key=True)  # uuid-сессии
    route_id     = db.Column(db.String, ForeignKey("route.id"))
    departure_city_id = db.Column(db.Integer, ForeignKey("city.id"), nullable=False)

    start_date     = db.Column(db.Date,   nullable=False)
    end_date   = db.Column(db.Date,   nullable=False)
    choices_json = db.Column(db.Text)

    created_at   = db.Column(db.DateTime, default=datetime.now)
    participants = relationship("TripParticipant", back_populates="session")
    route = relationship("Route")
    city = relationship("City")

class TripParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    session_id = db.Column(db.String, ForeignKey("trip_session.id"), nullable=False)

    join_at = db.Column(db.DateTime, default=func.now())
    session = relationship("TripSession", back_populates="participants")
    votes = relationship("TripVote", back_populates="participant")

class TripVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, ForeignKey("trip_session.id"), nullable=False)
    variant_id = db.Column(db.Integer, ForeignKey("day_variant.id"), nullable=False)
    participant_id = db.Column(db.Integer, ForeignKey("trip_participant.id"), nullable=False)
    day_order = db.Column(db.Integer, nullable=False)

    day_variant = relationship("DayVariant")
    participant = relationship("TripParticipant", back_populates="votes")

    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_order = db.Column(db.Integer)
    route_id = db.Column(db.String, ForeignKey("route.id"))
    variants = relationship("DayVariant", backref="day")


class DayVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    est_budget = db.Column(db.Integer)
    day_id = db.Column(db.Integer, ForeignKey("day.id"))
    segments = relationship("Segment", backref="variant")
    lodgings = relationship("LodgingOption", backref="variant")

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
    route_id     = db.Column(db.String, ForeignKey("route.id"), nullable=False)
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

    start_time = db.Column(db.Time, nullable=True)
    end_time   = db.Column(db.Time, nullable=True)

    # POI
    poi_name = db.Column(db.String)
    must_see = db.Column(db.Boolean)
    open_hours = db.Column(db.String)
    rating = db.Column(db.Float)

    # Meal
    meal_type = db.Column(db.String)
    meal_options_json = db.Column(db.Text)

    # Lodging
    lodging_name = db.Column(db.String)

    # Transition
    city_id   = db.Column(db.Integer, ForeignKey("route_city.id"), nullable=True)
    city      = relationship("RouteCity")
    transition_option    = relationship("TransitionOption")

class TransitionOption(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    mode          = db.Column(db.String, nullable=False)   # пешком, автобус, такси…
    time_min      = db.Column(db.Integer, nullable=False)
    cost_rub      = db.Column(db.Integer, nullable=True)
    is_default    = db.Column(db.Boolean, default=False)
    segment_id    = db.Column(db.Integer, ForeignKey("segment.id"), nullable=False)


class LodgingOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, ForeignKey("day_variant.id"))
    name = db.Column(db.String)
    type = db.Column(db.String)
    location_id = db.Column(db.String, nullable=True)

    distance_km = db.Column(db.Float, nullable=True)
    city_id     = db.Column(db.Integer, ForeignKey("route_city.id"), nullable=True)
    city        = relationship("RouteCity")

class TransportCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_city_id  = db.Column(db.Integer, ForeignKey("city.id"), nullable=False)
    end_city_id    = db.Column(db.Integer, ForeignKey("city.id"), nullable=False)
    data_json = db.Column(db.JSON, nullable=False)
    date_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
class MealPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    coords = db.Column(db.String)
    cuisine = db.Column(db.String)
    website = db.Column(db.String)
    avg_check_rub = db.Column(db.Integer)
    opening_hours = db.Column(db.String)
    rating = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, onupdate=func.now())


class PriceEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String)
    object_id = db.Column(db.String)
    last_known_price = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    source_url = db.Column(db.String)
