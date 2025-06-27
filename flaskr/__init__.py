import datetime
import functools
import json
import os
import uuid
from collections import defaultdict
from datetime import date
from typing import List
from urllib.parse import unquote

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
    session as fk_session,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from models.meal_place import MealPlace
from models.models import POI, City, Day, DayVariant, Route, RouteCity, Segment, db
from models.trip import Traveler, TripInvite, TripParticipant, TripSession, TripVote
from services.api_object import (
    create_or_get_poi,
    fetch_poi_from_dgis,
    get_hints_object,
    parse_poi_data,
)
from services.get_f_api_meal_places import get_nearby_cuisins_spots
from services.get_f_api_transports import get_transports_f_db_or_api
from services.get_meal_places import get_f_db_meal_places_near_poi
from services.session_utils import (
    DayRead,
    get_days_with_winner_variant,
    get_participants_by_session_id,
    get_participants_votes,
    get_voting_attributes,
)

from .DTOs.segmentDTO import MealPlaceDTO, SegmentDTO, SimularMealPlaceCacheDTO
from .DTOs.tripDTO import TripVoteDTO
from .utils import format_transports


class SegmentCreate(BaseModel):
    type: str
    order: int
    start_time: datetime.time
    end_time: datetime.time
    poi_dgis_id: str | None = None
    city_id: int


class DayVariantCreate(BaseModel):
    name: str
    est_budget: int
    is_default: bool
    segments: List[SegmentCreate]


class DayCreate(BaseModel):
    day_order: int
    day_variants: List[DayVariantCreate]


class RouteCityCreate(BaseModel):
    city_id: int
    order: int


class RouteCreate(BaseModel):
    title: str
    duration_days: int
    estimated_budget_rub: int
    img: str
    city: RouteCityCreate
    days: List[DayCreate]


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["YA_MAP_JS_API_KEY"] = os.getenv("YA_MAP_JS_API_KEY")  # в config

    limiter = Limiter(get_remote_address, app=app)

    app.jinja_env.filters["loads"] = json.loads
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    if test_config is None:
        app.config.from_pyfile("config.py", silent=False)
    else:
        app.config.from_mapping(test_config)

    @app.context_processor
    def inject_common_vars():
        return {"cities": City.query.all()}

    @app.before_request
    def ensure_participant_joined():
        if fk_session.get("uuid") is None:
            user_uuid = uuid.uuid4()
            fk_session["uuid"] = user_uuid

            user = Traveler(uuid=user_uuid)
            db.session.add(user)
            db.session.commit()

    def is_participant_required(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            trip_session_id = request.args.get("sessionId")
            if trip_session_id is None:
                abort(400, "Укажите id сессии")

            user = db.session.get(Traveler, fk_session.get("uuid"))
            if user is not None:
                if (
                    int(trip_session_id) not in [s.session_id for s in user.sessions]
                    and "join" not in request.url
                ):
                    abort(401)

            return view(**kwargs)

        return wrapped_view

    @app.route("/routes")
    def catalog_routes():
        routes = []
        for r in Route.query.all():
            # берём первый город как базу
            start = r.cities[0]
            data = {
                "id": r.id,
                "title": r.title,
                "duration_days": r.duration_days,
                "estimated_budget_rub": r.estimated_budget_rub,
                "img": r.img,
                "start_coords": [start.city.lat, start.city.lon],
            }

            pois = (
                POI.query.join(Segment, POI.id == Segment.poi_id)
                .join(DayVariant, Segment.variant_id == DayVariant.id)
                .join(Day, DayVariant.day_id == Day.id)
                .filter(Day.route_id == r.id, Segment.type == "poi")
                .all()
            )
            # 3) кладём список упрощённых POI
            data["pois"] = [{"name": p.name, "rating": p.rating} for p in pois]
            routes.append(data)

        return render_template("catalog.html", routes=routes)

    @app.route("/trip-setup/")
    @is_participant_required
    def trip_setup():
        session_id = request.args.get("sessionId")
        if not session_id:
            abort(400, "sessionId обязателен")

        trip_session = db.session.get(TripSession, session_id)
        if not trip_session:
            abort(404, "Сессия не найден")
        plan = {
            "session_id": trip_session.id,
            "session_uuid": trip_session.uuid,
            "title": trip_session.route.title,
            "durations_day": trip_session.route.duration_days,
            "day_variants": [
                {
                    "day": d.day_order,
                    "budget_for_default": d.default_variant.est_budget,
                    "variants": [
                        {
                            "id": v.id,
                            "name": v.name,
                            "est_budget": v.est_budget,
                            "is_default": v.is_default,
                        }
                        for v in d.variants
                    ],
                }
                for d in sorted(trip_session.route.days, key=lambda d: d.day_order)
            ],
        }
        voting_attributes = get_voting_attributes(
            session_id, trip_session.route.duration_days
        )

        participants = get_participants_by_session_id(session_id)
        participants_votes = get_participants_votes(participants)

        show_name_modal = False if fk_session.get("user_name") else True

        return render_template(
            "trip-setup.html",
            show_name_modal=show_name_modal,
            voting_attributes=voting_attributes,
            participants_votes=participants_votes,
            plan=plan,
            today=date.today(),
        )

    @app.route("/trip-itinerary/")
    @is_participant_required
    def trip_itinerary():
        session_id = request.args.get("sessionId")
        if not session_id:
            abort(400)

        session = db.session.get(TripSession, session_id)
        if not session:
            abort(404)

        route = db.session.get(Route, session.route_id)
        if not route:
            abort(404)

        votes = list(TripVote.query.filter_by(session_id=session_id).all())
        days_with_winner_variant: list[DayRead] = get_days_with_winner_variant(
            votes, session.route.duration_days
        )
        days = []
        if len(days_with_winner_variant) != len(route.days):
            abort(500, "Выбранных вариантов меньше, чем дней в поездке")
        for day_count, day in enumerate(route.days):
            day_with_variant: DayRead = days_with_winner_variant[day_count]
            variant_id = day_with_variant.variant.id

            stmt = (
                select(Segment)
                .options(joinedload(Segment.poi))
                .where(Segment.variant_id == variant_id)
                .order_by(Segment.order)
            )
            segments_for_variants = db.session.execute(stmt).scalars().all()

            segment_dtos = []
            for i in range(len(segments_for_variants)):
                current_segment = segments_for_variants[i]
                if current_segment.type == "meal" and i != 0:
                    meal_places = [
                        MealPlaceDTO.model_validate(i)
                        for i in get_f_db_meal_places_near_poi(
                            segments_for_variants[i - 1].poi
                        )
                    ]
                    model_dump = SegmentDTO.model_validate(
                        segments_for_variants[i]
                    ).model_dump()
                    del model_dump["meal_places"]
                    segment_dtos.append(
                        SegmentDTO(**model_dump, meal_places=meal_places)
                    )
                    continue
                segment_dtos.append(SegmentDTO.model_validate(segments_for_variants[i]))

            days.append(
                {
                    "day_order": day.day_order,
                    "variant_id": variant_id,
                    "segments": segment_dtos,
                }
            )

        transports_to_with_data_json = get_transports_f_db_or_api(
            session.start_date, session.city, route.cities[0].city
        )
        transports_from_with_data_json = get_transports_f_db_or_api(
            session.end_date, route.cities[0].city, session.city
        )
        transports_to_json = transports_to_with_data_json.data_json
        transports_from_json = transports_from_with_data_json.data_json
        transports = defaultdict()

        transports["there"] = [format_transports(t_to) for t_to in transports_to_json]
        transports["back"] = [
            format_transports(t_from) for t_from in transports_from_json
        ]

        return render_template(
            "trip-itinerary.html",
            route=route,
            session=session,
            days=days,
            transports=transports,
            ya_map_js_api_key=app.config["YA_MAP_JS_API_KEY"],
        )

    @app.route("/api/session/update_departure_city", methods=["POST"])
    def get_cities():
        data = request.json
        cities = City.query.all()
        if cities is None:
            return abort(404, "Городов нет в бд")
        return jsonify(cities)

    @app.route("/api/session/update_transports", methods=["POST"])
    def update_transports_in_db():
        data = request.json or {}
        start_date = date.fromisoformat(data.get("startDate"))
        if start_date is None:
            abort(400, "Отсутствует дата для поиска")

        session_id = data.get("sessionId")
        if session_id is None:
            abort(400, "Отсутствует id session для поиска")
        session = db.session.get(TripSession, session_id)
        session.start_date = start_date
        session.end_date = start_date + datetime.timedelta(session.route.duration_days)
        db.session.commit()
        route = db.session.get(Route, session.route_id)

        _ = get_transports_f_db_or_api(
            session.start_date, session.city, route.cities[0].city
        )
        _ = get_transports_f_db_or_api(
            session.end_date, route.cities[0].city, session.city
        )
        return jsonify({"message": "Transport updated "})

    @app.route("/api/session/create_or_get", methods=["POST"])
    def create_session_or_get_exist_where_admin():
        data = request.json or {}
        route_id = int(data["routeId"])
        departure_city_id = int(data["departureCityId"])
        if not (route_id):
            abort(400, "Нужно указать routeId")

        user_uuid = fk_session.get("uuid")
        stmt = (
            select(TripParticipant)
            .where(TripParticipant.user_uuid == user_uuid)
            .where(TripParticipant.is_admin == True)
        )
        sessions_user_admin = db.session.execute(stmt).scalars().all()
        exist_trip_session = list(
            filter(lambda s: s.session.route_id == route_id, sessions_user_admin)
        )

        if len(exist_trip_session) != 0:
            return jsonify({"sessionId": exist_trip_session[0].session.id})

        route = db.session.get(Route, route_id)
        sid = uuid.uuid4()
        trip_session = TripSession(
            uuid=sid,
            route_id=route_id,
            departure_city_id=departure_city_id,
            start_date=datetime.datetime.today(),
            end_date=datetime.datetime.today() + datetime.timedelta(days=route.duration_days),
            choices_json='{}'
        )

        db.session.add(trip_session)
        db.session.commit()
        db.session.add(
            TripParticipant(
                user_uuid=user_uuid, session_id=trip_session.id, is_admin=True
            )
        )
        db.session.commit()

        return jsonify({"sessionId": trip_session.id})

    @app.route("/api/session/add_user_name", methods=["POST"])
    def add_user_name():
        data = request.json or {}
        user_uuid = fk_session.get("uuid")

        user_name = data["user_name"]
        user = db.session.get(Traveler, user_uuid)
        user.name = user_name
        fk_session["user_name"] = user_name

        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "participant name added to db"})

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

    @app.route("/api/route/create/", methods=["POST"])
    def create_route():
        try:
            route_create = parse_route_data(request.json)
        except ValidationError:
            abort(400, "Данные не проходят валидацию")
        route = from_route_create_to_route(route_create)

        db.session.add(route)
        db.session.commit()
        return jsonify({"message": "Succesful created"}), 201

    def parse_segments(variant):
        return [
            SegmentCreate(
                type=segment.get("type"),
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

    @app.route("/api/poi/create_or_get", methods=["POST"])
    def create_poi_by_dgis_id():
        data = request.json or {}
        dgis_id = data.get("dgis_id")

        if dgis_id is None:
            abort(400, "Не указан dgis_id точки")

        data = fetch_poi_from_dgis(dgis_id)
        poi_dgis = parse_poi_data(data, dgis_id)
        poi = create_or_get_poi(poi_dgis)
        return jsonify({"id": poi.id})

    @app.route("/api/session/join_by_token/<uuid:token>")
    def join_to_session(token):
        stmt = select(TripInvite).where(TripInvite.uuid == token)
        invite: TripInvite = db.session.execute(stmt).scalars().first()

        if invite is None:
            abort(404, "Приглашение не найдено")

        user = db.session.get(Traveler, fk_session.get("uuid"))
        for trip_participant in user.sessions:
            if trip_participant.session.uuid == invite.session_uuid:
                return redirect(
                    url_for("trip_setup", sessionId=trip_participant.session.id)
                )

        if datetime.datetime.now() > invite.expired_at or invite.is_active is False:
            abort(401, "Срок приглашения истек или им уже воспользовались")
        invite.is_active = False
        db.session.commit()

        stmt = select(TripSession).where(TripSession.uuid == invite.session_uuid)
        session = db.session.execute(stmt).scalars().first()

        trip_participant = TripParticipant(
            user_uuid=fk_session.get("uuid"), session_id=session.id
        )
        db.session.add(trip_participant)
        db.session.commit()

        return redirect(url_for("trip_setup", sessionId=session.id))

    @app.route("/api/session/<uuid:session_uuid>/create_invite", methods=["POST"])
    def create_trip_invite(session_uuid):
        stmt = select(TripSession).where(TripSession.uuid == session_uuid)
        session = db.session.execute(stmt).scalars().first()
        if session is None:
            abort(404, "Сессия не найдена")
        invite = TripInvite(uuid=uuid.uuid4(), session_uuid=session_uuid)
        db.session.add(invite)
        db.session.commit()
        return jsonify(
            {
                "link": url_for("join_to_session", token=invite.uuid),
                "token": invite.uuid,
            }
        )

    @app.route("/api/session/vote", methods=["POST"])
    def vote():
        data = request.json or {}
        choices = data["choices"]
        session_id = data["session_id"]
        user_uuid = fk_session.get("uuid")
        if user_uuid is None:
            abort(401, "Пользователь не имеет uuid")

        participant = TripParticipant.query.filter_by(
            user_uuid=user_uuid, session_id=session_id
        ).first()
        if participant is None:
            abort(403, "Пользователь не является участником сессии, в которой голосует")

        stmt = select(TripSession).where(TripSession.id == session_id)
        session = db.session.execute(stmt).scalars().first()

        voting_attributes = get_voting_attributes(
            session_id, session.route.duration_days
        )
        if voting_attributes["is_completed_vote"]:
            abort(422, "Голосование завершилось")

        exist_participant_votes = TripVote.query.filter_by(
            participant_id=participant.id, session_id=session_id
        ).all()
        trip_votes_to_add = []
        for choice in choices:
            if exist_participant_votes:
                for v_id, day_order in choice.items():
                    for vote in exist_participant_votes:
                        if vote.day_order == int(day_order) and vote.variant_id != int(
                            v_id
                        ):
                            vote.variant_id = int(v_id)
            else:
                for v_id, day_order in choice.items():
                    trip_votes_to_add.append(
                        TripVote(
                            participant_id=participant.id,
                            variant_id=v_id,
                            day_order=day_order,
                            session_id=session_id,
                        )
                    )

        db.session.add_all(trip_votes_to_add)
        db.session.commit()

        return jsonify(
            votes=[
                TripVoteDTO.model_validate(vote).model_dump()
                for vote in trip_votes_to_add
            ]
        )

    @app.route("/api/poi_hints")
    @limiter.limit("10 per minute")
    def get_poi_hints():
        object_name = unquote(request.args.get("q"))
        location = unquote(request.args.get("location"))
        hints_object, error_code = get_hints_object(object_name, location)

        if error_code == 400:
            return jsonify({"error": "Метод на найден"}), 400
        if error_code == 404:
            return jsonify({"error": "Ничего не найдено"}), 404
        if error_code is not None:
            return jsonify({"error": "Непредвиденная ошибка"}), error_code

        return jsonify(hints_object)

    @app.route("/api/meal_place/<int:meal_place_id>/get_simulars")
    def get_simulars_meal_places(meal_place_id):
        meal_place = db.session.get(MealPlace, meal_place_id)
        if meal_place is None:
            abort(404)
        simular_meal_places_result = get_nearby_cuisins_spots(
            coords=meal_place.coords,
            cuisine=meal_place.cuisine,
            meal_place_id=meal_place_id,
        )
        if simular_meal_places_result is None:
            return ("", 204)
        return jsonify(
            {
                "simular_meal_places_result": json.dumps(
                    [
                        SimularMealPlaceCacheDTO.model_validate(spot).to_dict()
                        for spot in simular_meal_places_result[:4]
                    ]
                )
            }
        )

    @app.route("/<path:filename>")
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)

    return app
