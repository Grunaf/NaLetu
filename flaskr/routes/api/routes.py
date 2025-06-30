from flask import Blueprint, abort, jsonify, request
from pydantic import ValidationError

from flaskr.db.route import add_route_db
from flaskr.models.constants import REVERSED_SEGMENT_TYPE
from flaskr.models.route import Day, DayVariant, Route, RouteCity, Segment
from flaskr.schemas.route import DayCreate, DayVariantCreate
from flaskr.schemas.segment import (
    RouteCityCreate,
    RouteCreate,
    SegmentCreate,
)
from flaskr.services.get_f_api_poi import create_or_get_poi

mod = Blueprint("api/route", __name__, url_prefix="/api/route")


def from_segments_create_to_segments(segments_create: SegmentCreate):
    segments = []
    for segment in segments_create:
        poi_id = (
            create_or_get_poi(segment.poi_dgis_id).id
            if segment.poi_dgis_id is not None
            else None
        )

        segments.append(
            Segment(
                type=segment.type,
                order=segment.order,
                start_time=segment.start_time,
                end_time=segment.end_time,
                poi_id=poi_id,
                city_id=segment.city_id,
            )
        )
    return segments


def from_variants_create_to_variants(variants_create: DayVariantCreate):
    return [
        DayVariant(
            name=variant.name,
            est_budget=variant.est_budget,
            is_default=variant.is_default,
            segments=from_segments_create_to_segments(variant.segments),
        )
        for variant in variants_create
    ]


def from_route_city_create_to_route_city(route_city_create: RouteCityCreate):
    return RouteCity(city_id=route_city_create.city_id, order=1)


def from_days_create_to_days(days_create: DayCreate):
    return [
        Day(
            day_order=day.day_order,
            variants=from_variants_create_to_variants(day.day_variants),
        )
        for day in days_create
    ]


def from_route_create_to_route(route_create: RouteCreate) -> Route:
    route_city = from_route_city_create_to_route_city(route_create.city)

    days = from_days_create_to_days(route_create.days)
    return Route(
        title=route_create.title,
        days=days,
        duration_days=len(days),
        estimated_budget_rub=0,
        img=route_create.img,
        cities=[route_city],
    )


def parse_segments(variant):
    return [
        SegmentCreate(
            type=REVERSED_SEGMENT_TYPE.get(segment.get("type").lower()),
            order=index,
            start_time=segment.get("start_time"),
            end_time=segment.get("end_time"),
            poi_dgis_id=segment.get("poi_dgis_id"),
            city_id=segment.get("city_id"),
        )
        for index, segment in enumerate(variant)
    ]


def parse_variants(day):
    return [
        DayVariantCreate(
            name="",
            est_budget=0,
            segments=parse_segments(variant),
            is_default=(index == 0),
        )
        for index, variant in enumerate(day)
    ]


def parseDays(days):
    return [
        DayCreate(day_order=day_order, day_variants=parse_variants(day))
        for day_order, day in enumerate(days, start=1)
    ]


def parse_route_data(data):
    city_id = data.get("city_id")
    title = data.get("title")

    days = data.get("days")
    duration_days = len(days)

    estimated_budget_rub = 0
    img = data.get("img")

    route_city = RouteCityCreate(city_id=city_id, order=1)
    return RouteCreate(
        title=title,
        duration_days=duration_days,
        estimated_budget_rub=estimated_budget_rub,
        city=route_city,
        img=img,
        days=parseDays(days),
    )


@mod.route("/", methods=["POST"])
def create_route():
    try:
        route_create = parse_route_data(request.json)
    except ValidationError as error:
        abort(400, f"Данные не прошли валидацию {error.errors()}")

    route = from_route_create_to_route(route_create)
    add_route_db(route)

    return jsonify({"message": "Succesful created"}), 201
