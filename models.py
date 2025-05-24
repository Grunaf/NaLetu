from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

db = SQLAlchemy()

class Route(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    entry_info_json = db.Column(db.Text)
    duration_days = db.Column(db.Integer)
    estimated_budget_rub = db.Column(db.Integer)

    transports = relationship("TransportOption", backref="route")
    days = relationship("Day", backref="route")
    img = db.Column(db.String) 


class TransportOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.String, ForeignKey('route.id'))

    mode = db.Column(db.String)
    there_from = db.Column(db.String)
    there_to = db.Column(db.String)
    there_time_min = db.Column(db.Integer)
    there_cost_rub = db.Column(db.Integer)

    back_from = db.Column(db.String)
    back_to = db.Column(db.String)
    back_time_min = db.Column(db.Integer)
    back_cost_rub = db.Column(db.Integer)


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


class Segment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, ForeignKey('day_variant.id'))
    type = db.Column(db.String)  # poi, meal, transport_segment, transport_back

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
    walk_time_min = db.Column(db.Integer)  # сколько идти пешком
    walk_distance_m = db.Column(db.Integer)  # опционально, если считаешь метры
    alt_transport_json = db.Column(db.Text)  # например: [{"mode": "автобус", "time_min": 10, "cost_rub": 50}]
    transition_reason = db.Column(db.String)  # например: "перейти в музей", "успеть на вокзал"



class LodgingOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, ForeignKey('day_variant.id'))
    name = db.Column(db.String)
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
