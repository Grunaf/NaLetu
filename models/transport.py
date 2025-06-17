import datetime

from models.models import db
from sqlalchemy import ForeignKey

class TransportCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_city_id  = db.Column(db.Integer, ForeignKey("city.id"), nullable=False)
    end_city_id    = db.Column(db.Integer, ForeignKey("city.id"), nullable=False)
    data_json = db.Column(db.JSON, nullable=False)
    date_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.datetime.now())
  

class TransportPriceEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String)
    object_id = db.Column(db.Integer)
    last_known_price = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, onupdate=datetime.datetime.now())
    source_url = db.Column(db.String)
