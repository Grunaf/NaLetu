# utils/meal_fetcher.py
from datetime import datetime, timedelta
from models import MealPlace, db
from utils.fetch_meals_2gis import fetch_meals_2gis  # твоя функция с запросом к 2GIS

from sqlalchemy import func
import math


def haversine_distance(lat1, lon1, lat2, lon2):
    # Возвращает расстояние в километрах
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_or_refresh_meals(lat, lon, radius_km=0.7, freshness_days=7):
    cutoff = datetime.utcnow() - timedelta(days=freshness_days)
    # Сначала пытаемся найти в БД
    candidates = MealPlace.query.all()

    nearby = []
    for m in candidates:
        try:
            m_lat, m_lon = map(float, m.coords.split(','))
            if haversine_distance(lat, lon, m_lat, m_lon) <= radius_km:
                nearby.append(m)
        except:
            continue

    fresh = [m for m in nearby if m.updated_at and m.updated_at > cutoff]

    if len(fresh) >= 3:
        return fresh[:5]

    # Обновим из API
    fetched = fetch_meals_2gis(lat, lon, radius=int(radius_km * 1000), limit=5)

    result = []
    for item in fetched:
        existing = MealPlace.query.filter_by(name=item["name"], coords=item["coords"]).first()
        if existing:
            existing.avg_check_rub = item["avg_check_rub"]
            existing.rating = item["rating"]
            existing.opening_hours = item["opening_hours"]
            existing.updated_at = datetime.utcnow()
            result.append(existing)
        else:
            new = MealPlace(
                name=item["name"],
                coords=item["coords"],
                cuisine=item["cuisine"],
                website=item["website"],
                avg_check_rub=item["avg_check_rub"],
                opening_hours=item["opening_hours"],
                rating=item["rating"],
                updated_at=datetime.utcnow()
            )
            db.session.add(new)
            result.append(new)

    db.session.commit()
    return result
