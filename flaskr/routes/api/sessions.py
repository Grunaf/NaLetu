import datetime
from datetime import date

import shortuuid
from flask import Blueprint, Response, abort, jsonify, request, url_for
from flask import session as fk_session

from flaskr.constants import (
    DEPARTURE_CITY_ID,
    MAX_PARTICIPANT_COUNT,
    ROUTE_ID,
    SESSION_NOT_FOUND,
    SESSION_UUID_REQUIRED,
)
from flaskr.db.cities import get_city
from flaskr.db.participations import (
    create_participant,
    get_session_participations,
    is_many_travelers_in_session,
)
from flaskr.db.trip_invites import (
    create_trip_invite as create_trip_invite_db,
)
from flaskr.db.trip_sessions import (
    create_trip_session,
    delete_trip_session,
    get_trip_session_by_uuid,
)
from flaskr.models.cities import City
from flaskr.models.models import db
from flaskr.models.route import Route
from flaskr.models.trip import (
    TripParticipant,
    TripSession,
    TripVote,
)
from flaskr.routes.constants import API_SESSION_URI
from flaskr.schemas.city import City as CityRead
from flaskr.schemas.trip import TripVoteDTO
from flaskr.services.get_f_api_transports import get_transports
from flaskr.services.travelers import get_or_create_traveler, get_uuid_traveler
from flaskr.services.voting import get_voting_attributes

mod = Blueprint("api/session", __name__, url_prefix=API_SESSION_URI)


@mod.route("/update_departure_city", methods=["POST"])
def get_cities() -> Response:
    cities = City.query.all()
    if cities is None:
        return abort(404, "Городов нет в бд")
    return jsonify(cities)


@mod.route("/update_transports", methods=["POST"])
def update_transports_in_db() -> Response:
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

    _ = get_transports(session.start_date, session.city, route.cities[0].city)
    _ = get_transports(session.end_date, route.cities[0].city, session.city)
    return jsonify({"message": "Transport updated "})


@mod.route("/", methods=["POST"])
def create_session() -> tuple[Response, int]:
    data = request.json or {}
    route_id = data.get("routeId")
    if route_id is None:
        return jsonify({"error": ROUTE_ID.REQUIRED}), 400
    try:
        route_id = int(route_id)
    except ValueError:
        return jsonify({"error": ROUTE_ID.IS_NOT_INT}), 400

    departure_city_id = data.get("departureCityId")
    if departure_city_id is None:
        return jsonify({"error": DEPARTURE_CITY_ID.REQUIRED}), 400
    departure_city_id = int(departure_city_id)

    fk_session["user_city"] = CityRead.model_validate(
        get_city(departure_city_id)
    ).model_dump()

    user_uuid = get_uuid_traveler()
    user_name = fk_session.get("user_name")
    _ = get_or_create_traveler(user_uuid, user_name)

    route = db.session.get(Route, route_id)
    if route is None:
        return jsonify({"error": "Маршрут не найден"}), 404

    today = datetime.datetime.today()
    end_date = today + datetime.timedelta(days=route.duration_days)

    trip_session = create_trip_session(
        route_id=route_id,
        departure_city_id=departure_city_id,
        start_date=today,
        end_date=end_date,
    )
    session_uuid = trip_session.uuid

    _ = create_participant(user_uuid, trip_session.id, is_admin=True)

    short_uuid = shortuuid.encode(session_uuid)
    return jsonify({"session_uuid": short_uuid}), 201


@mod.route("/<short_uuid>", methods=["DELETE"])
def delete_sesion(short_uuid: str) -> Response:
    if short_uuid is None:
        abort(400, SESSION_UUID_REQUIRED)
    session_uuid = shortuuid.decode(short_uuid)
    row_count = delete_trip_session(session_uuid)
    if row_count == 0:
        abort(404, "Сессии не сущесвует")
    return Response(status=204)


@mod.route("/add_user_name", methods=["POST"])
def add_user_name() -> Response:
    data = request.json or {}
    user_uuid = get_uuid_traveler()

    user_name = data["user_name"]

    traveler = get_or_create_traveler(user_uuid, name=user_name)
    traveler.name = user_name
    fk_session["user_name"] = user_name

    db.session.commit()

    return jsonify({"message": "participant name added to db"})


@mod.route("/<short_uuid>/create_invite", methods=["POST"])
def create_trip_invite(short_uuid: str) -> Response:
    session_uuid = shortuuid.decode(short_uuid)
    session = get_trip_session_by_uuid(session_uuid)
    if session is None:
        abort(404, SESSION_NOT_FOUND)

    participants = get_session_participations(session.id)
    if len(participants) >= MAX_PARTICIPANT_COUNT:
        abort(422, "Группа заполнена")

    invite = create_trip_invite_db(session_uuid)
    short_invite_uuid = shortuuid.encode(invite.uuid)
    return jsonify(
        {
            "link": url_for(
                "views.join_to_session",
                short_invite_uuid=short_invite_uuid,
                _external=True,
            ),
            "token": short_invite_uuid,
        }
    )


@mod.route("/vote", methods=["POST"])
def vote() -> Response:
    data = request.json or {}
    choices = data["choices"]

    short_uuid = data.get("session_uuid")
    if short_uuid is None:
        abort(400, "Session uuid обязателен")
    session_uuid = shortuuid.decode(short_uuid)

    session = get_trip_session_by_uuid(session_uuid)
    if session is None:
        abort(404, "Сессия не найдена")

    user_uuid = get_uuid_traveler()

    participant = TripParticipant.query.filter_by(
        user_uuid=user_uuid, session_id=session.id
    ).first()
    if participant is None:
        abort(
            403,
            "Пользователь не является участником сессии, в которой голосует",
        )

    voting_attributes = get_voting_attributes(session.id, session.route.duration_days)
    if voting_attributes["is_voting_completed"] and is_many_travelers_in_session(
        session.id
    ):
        abort(422, "Голосование завершилось")

    exist_participant_votes = TripVote.query.filter_by(
        participant_id=participant.id, session_id=session.id
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
                        session_id=session.id,
                    )
                )

    db.session.add_all(trip_votes_to_add)
    db.session.commit()

    return jsonify(
        votes=[
            TripVoteDTO.model_validate(vote).model_dump() for vote in trip_votes_to_add
        ]
    )
