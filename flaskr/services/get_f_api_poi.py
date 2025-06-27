import datetime
import json
import os
from typing import List

import requests
from models.models import POI, db
from pydantic import BaseModel
from sqlalchemy import select

from config import DGIS_API_URI_GET_BY_ID, DGIS_API_URI_HINT

fields_for_poi = "items.point,items.reviews,items.schedule,items.reviews"
dgis_params = {"key": os.getenv("DGIS_API_KEY"), "locale": "ru_RU"}


def get_hints_object(object_name: str, location: str):
    resp = requests.get(
        DGIS_API_URI_HINT,
        {
            "q": object_name,
            "type": "branch",
            "location": location,
            "suggest_type": "object",
            **dgis_params,
        },
    )
    if resp.status_code != 200:
        return None, resp.status_code

    result = resp.json()
    code = result["meta"]["code"]

    if code == 404:
        return None, 404
    if code == 400:
        return None, 400

    items = result["result"]["items"]
    return [{"name": item["name"], "id": item["id"]} for item in items], None


def fetch_poi_from_dgis(dgis_id: str) -> dict:
    response = requests.get(
        DGIS_API_URI_GET_BY_ID, {"id": dgis_id, "fields": fields_for_poi, **dgis_params}
    )

    if response.status_code != 200:
        print(f"[Ошибка запроса] Статус: {response.status_code}")
        return

    data = response.json()
    result_code = data["meta"]["code"]

    if result_code in (400, 404):
        print(f"[Ошибка запроса] Статус: {result_code}")
        return None

    return data


class POICreate(BaseModel):
    dgis_id: str
    name: str
    must_see: bool = False
    rating: float | None = 0
    open_time: datetime.time
    close_time: datetime.time
    lat: float
    lon: float


def parse_poi_data(data: dict, dgis_id: str) -> POICreate:
    items: List[dict] = data["result"]["items"]

    name = items[0].get("name")
    schedule_for_monday = items[0].get("schedule").get("Mon").get("working_hours")[0]
    open_time = datetime.time.fromisoformat(schedule_for_monday.get("from"))

    close_time_string = (
        schedule_for_monday.get("to")
        if schedule_for_monday.get("to") != "24:00"
        else "00:00"
    )
    close_time = datetime.time.fromisoformat(close_time_string)

    reviews = items[0].get("reviews")
    rating = None
    review_count = None
    must_see = False
    if reviews is not None and reviews.get("is_reviewable"):
        try:
            rating = float(reviews.get("general_rating"))
            review_count = int(reviews.get("general_review_count"))
            must_see = rating == 5 and review_count > 300
        except TypeError:
            print("Ошибка с получением рейтинга")
            raise TypeError

    point: dict = items[0].get("point")
    lat_str, lon_str = point.values()
    lat = float(lat_str)
    lon = float(lon_str)

    return POICreate(
        dgis_id=dgis_id,
        name=name,
        must_see=must_see,
        rating=rating,
        open_time=open_time,
        close_time=close_time,
        lat=lat,
        lon=lon,
    )


def create_or_get_poi(dgis_id: str) -> POI:
    stmt = select(POI).where(POI.dgis_id == dgis_id)
    existing_poi = db.session.execute(stmt).scalar()
    if existing_poi:
        return existing_poi

    data = fetch_poi_from_dgis(dgis_id=dgis_id)
    poi_create = parse_poi_data(data, dgis_id)

    poi = POI(
        dgis_id=dgis_id,
        name=poi_create.name,
        must_see=poi_create.must_see,
        rating=poi_create.rating,
        open_time=poi_create.open_time,
        close_time=poi_create.close_time,
        lat=poi_create.lat,
        lon=poi_create.lon,
    )

    db.session.add(poi)
    db.session.commit()
    return poi
