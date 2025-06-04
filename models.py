from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

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

class City(db.Model):
    __tablename__ = 'city'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    yandex_code = db.Column(db.String, nullable=False, unique=True)  # Для API

    def __repr__(self):
        return f"<City {self.name}>"

class RouteCity(db.Model):
    __tablename__ = 'route_city'

    id           = db.Column(db.Integer, primary_key=True)
    route_id     = db.Column(db.String, ForeignKey('route.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    order        = db.Column(db.Integer, nullable=False)     # порядковый номер в маршруте

    route = relationship('Route', back_populates='cities')
    city = db.relationship("City")

class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_number = db.Column(db.Integer)
    route_id = db.Column(db.String, ForeignKey('route.id'))
    variants = relationship("DayVariant", backref="day")


class DayVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.String)
    name = db.Column(db.String)
    est_budget = db.Column(db.Integer)
    day_id = db.Column(db.Integer, ForeignKey('day.id'))
    segments = relationship("Segment", backref="variant")
    lodgings = relationship("LodgingOption", backref="variant")

class TransportCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_city = db.Column(db.String, nullable=False)
    to_city = db.Column(db.String, nullable=False)
    transport_data_json = db.Column(db.JSON, nullable=False)
    date_for = db.Column(db.Date, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Segment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, ForeignKey('day_variant.id'))
    type = db.Column(db.String)  # poi, meal, transport_segment, transport_back
    arrival_window = db.Column(db.String)

    # POI
    poi_name = db.Column(db.String)
    must_see = db.Column(db.Boolean)
    poi_description_json = db.Column(db.Text)

    # Meal
    meal_type = db.Column(db.String)
    meal_options_json = db.Column(db.Text)

    alt_transport_json = db.Column(db.Text)  # например: [{"mode": "автобус", "time_min": 10, "cost_rub": 50}]
    transition_reason = db.Column(db.String)  # например: "перейти в музей", "успеть на вокзал"

class LodgingOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, ForeignKey('day_variant.id'))
    name = db.Column(db.String)
    avg_check_rub = db.Column(db.Integer)  # либо через PriceEntry
    type = db.Column(db.String)

class MealPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    coords = db.Column(db.String)
    cuisine = db.Column(db.String)
    website = db.Column(db.String)
    avg_check_rub = db.Column(db.Integer)  # либо через PriceEntry
    opening_hours = db.Column(db.String)
    rating = db.Column(db.Float)
    updated_at = db.Column(db.DateTime)

class PriceEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String)      # 'poi' / 'meal' / 'lodging' / 'transport'
    object_id = db.Column(db.String)        # внешний ID (например, poi_id или имя)
    last_known_price = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime)
    source_url = db.Column(db.String)       # опционально — откуда брали

class TripSession(db.Model):
    id = db.Column(db.String, primary_key=True)
    route_id     = db.Column(db.String, ForeignKey('route.id'))
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))

    check_in     = db.Column(db.Date)
    check_out    = db.Column(db.Date)
    choices_json = db.Column(db.Text)   # что выбрал пользователь (варианты по дням)
    created_at   = db.Column(db.DateTime, default=datetime.now)
    # варианты связать с DayVariant через JSON или отдельной таблицей

    route = db.relationship("Route")
    city = db.relationship("City")

class TripParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, ForeignKey("trip_session.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("session_id", "name", name="unique_participant"),)

class TripVote(db.Model):
    __tablename__ = "trip_vote"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('trip_session.id'), nullable=False)

    participant_id = db.Column(db.Integer, db.ForeignKey('trip_participant.id'), nullable=False)
    participant = db.relationship("TripParticipant", backref="votes")

    day_number = db.Column(db.Integer, nullable=False)
    variant_id = db.Column(db.String, nullable=False)  # например: "1A", "2B"

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
