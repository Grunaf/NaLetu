from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

db = SQLAlchemy()

class TripSession(db.Model):
    id           = db.Column(db.String, primary_key=True)  # uuid-сессии
    route_id     = db.Column(db.String, ForeignKey('route.id'))

    departure_city = db.Column(db.String, nullable=False)
    departure_lat  = db.Column(db.Float, nullable=False)
    departure_lon  = db.Column(db.Float, nullable=False)


    check_in     = db.Column(db.Date,   nullable=False)
    check_out    = db.Column(db.Date,   nullable=False)
    choices_json = db.Column(db.Text)   # что выбрал пользователь (варианты по дням)
    created_at   = db.Column(db.DateTime, default=datetime.now)
    # варианты связать с DayVariant через JSON или отдельной таблицей

class Route(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    duration_days = db.Column(db.Integer)
    estimated_budget_rub = db.Column(db.Integer)

    transports = relationship("TransportOption", backref="route")
    days = relationship("Day", backref="route")
    cities     = relationship(
      "RouteCity",
      order_by="RouteCity.order",
      back_populates="route",
      cascade="all, delete-orphan"
    )
    img = db.Column(db.String) 


class TransportOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.String, ForeignKey('route.id'))

    mode = db.Column(db.String)
    start_city_id  = db.Column(db.Integer, ForeignKey('route_city.id'), nullable=False)
    end_city_id    = db.Column(db.Integer, ForeignKey('route_city.id'), nullable=False)
    start_city     = relationship('RouteCity', foreign_keys=[start_city_id])
    end_city       = relationship('RouteCity', foreign_keys=[end_city_id])
    
    start_time_min = db.Column(db.Integer, nullable=False)
    start_cost_rub = db.Column(db.Integer, nullable=False)
    end_time_min   = db.Column(db.Integer, nullable=False)
    end_cost_rub   = db.Column(db.Integer, nullable=False)



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

class TransitionOption(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    segment_id    = db.Column(db.Integer, ForeignKey('segment.id'), nullable=False)
    mode          = db.Column(db.String, nullable=False)   # пешком, автобус, такси…
    time_min      = db.Column(db.Integer, nullable=False)
    cost_rub      = db.Column(db.Integer, nullable=True)
    is_default    = db.Column(db.Boolean, default=False)   # предпочитаемый вариант

class Segment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, ForeignKey('day_variant.id'))
    type = db.Column(db.String)  # poi, meal, transport_segment, transport_back
    order = db.Column(db.Integer, nullable=False)

    start_time = db.Column(db.Time, nullable=True)
    end_time   = db.Column(db.Time, nullable=True)

    # POI
    poi_name = db.Column(db.String)
    must_see = db.Column(db.Boolean)
    arrival_window = db.Column(db.String)
    rating = db.Column(db.Float)

    # Meal
    meal_type = db.Column(db.String)
    meal_options_json = db.Column(db.Text)

    # Lodging
    lodging_name = db.Column(db.String)

    # Transition
    city_id   = db.Column(db.Integer, ForeignKey('route_city.id'), nullable=True)
    city      = relationship('RouteCity')

    # если type=='transport_segment'
    transport_option_id = db.Column(db.Integer, ForeignKey('transport_option.id'), nullable=True)
    transport_option    = relationship('TransportOption')


class LodgingOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, ForeignKey('day_variant.id'))
    name = db.Column(db.String)
    type = db.Column(db.String)
    location_id = db.Column(db.String, nullable=True)

    distance_km = db.Column(db.Float, nullable=True)
    city_id     = db.Column(db.Integer, ForeignKey('route_city.id'), nullable=True)
    city        = relationship('RouteCity')


class RouteCity(db.Model):
    __tablename__ = 'route_city'

    id           = db.Column(db.Integer, primary_key=True)
    route_id     = db.Column(db.String, ForeignKey('route.id'), nullable=False)
    # city_id      = db.Column(db.Integer, ForeignKey('route_city.id'), nullable=False)
    name         = db.Column(db.String, nullable=False)      # например, "Москва"
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    station_code = db.Column(db.String, nullable=True)       # код Яндекс.Расписаний

    order        = db.Column(db.Integer, nullable=False)     # порядковый номер в маршруте

    # связь обратно к маршруту
    # city =  relationship('City', back_populates='route_cities')
    route = relationship('Route', back_populates='cities')

# class City(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String, nullable=False)
#     lat = db.Column(db.Float)
#     lon = db.Column(db.Float)
#     yandex_code = db.Column(db.String, nullable=False)
#     route_cities = relationship('RouteCity', back_populates='city') 

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
