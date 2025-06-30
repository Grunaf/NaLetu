import datetime
import json
import uuid
from datetime import date

from flask import Blueprint, abort, jsonify, redirect, request, url_for
from flask import session as fk_session
from sqlalchemy import select

from flaskr.db.cities import get_city
from flaskr.db.trip_invites import get_trip_invite_by_uuid
from flaskr.db.trip_sessions import (
    get_trip_session_by_id,
    get_trip_session_by_uuid,
    get_trip_session_where_user_admin,
)
from flaskr.models.city import City
from flaskr.models.meal_place import MealPlace
from flaskr.models.models import db
from flaskr.models.route import Route
from flaskr.models.trip import (
    TripInvite,
    TripParticipant,
    TripSession,
    TripVote,
)
from flaskr.models.user import Traveler
from flaskr.schemas.segment import SimularMealPlaceCacheDTO
from flaskr.schemas.city import City as CityRead
from flaskr.schemas.trip import TripVoteDTO
from flaskr.services.get_f_api_transports import get_transports_f_db_or_api
from flaskr.services.get_meal_places import get_nearby_cuisins_spots
from flaskr.services.session_utils import get_voting_attributes

mod = Blueprint("api/session", __name__, url_prefix="/api/session")


@mod.route("/update_departure_city", methods=["POST"])
def get_cities():
    cities = City.query.all()
    if cities is None:
        return abort(404, "Городов нет в бд")
    return jsonify(cities)


@mod.route("/update_transports", methods=["POST"])
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
    _ = get_transports_f_db_or_api(session.end_date, route.cities[0].city, session.city)
    return jsonify({"message": "Transport updated "})


@mod.route("/create_or_get", methods=["POST"])
def create_session_or_get_exist_where_admin():
    data = request.json or {}
    route_id = int(data["routeId"])
    if not (route_id):
        abort(400, "Нужно указать routeId")

    departure_city_id = int(data["departureCityId"])
    fk_session["user_city"] = CityRead.model_validate(
        get_city(departure_city_id)
    ).model_dump()
    user_uuid = fk_session.get("uuid")

    sessions_user_admin = get_trip_session_where_user_admin(user_uuid)
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
        end_date=datetime.datetime.today()
        + datetime.timedelta(days=route.duration_days),
    )

    db.session.add(trip_session)
    db.session.commit()
    db.session.add(
        TripParticipant(user_uuid=user_uuid, session_id=trip_session.id, is_admin=True)
    )
    db.session.commit()

    return jsonify({"sessionId": trip_session.id})


@mod.route("/add_user_name", methods=["POST"])
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


@mod.route("/join_by_token/<uuid:token>")
def join_to_session(token):
    invite: TripInvite = get_trip_invite_by_uuid(token)

    if invite is None:
        abort(404, "Приглашение не найдено")

    user = db.session.get(Traveler, fk_session.get("uuid"))
    for trip_participant in user.sessions:
        if trip_participant.session.uuid == invite.session_uuid:
            return redirect(
                url_for("views.trip_setup", sessionId=trip_participant.session.id)
            )

    if datetime.datetime.now() > invite.expired_at or invite.is_active is False:
        abort(401, "Срок приглашения истек или им уже воспользовались")
    invite.is_active = False
    db.session.commit()

    session = get_trip_session_by_uuid(invite.session_uuid)

    trip_participant = TripParticipant(
        user_uuid=fk_session.get("uuid"), session_id=session.id
    )
    db.session.add(trip_participant)
    db.session.commit()

    return redirect(url_for("views.trip_setup", sessionId=session.id))


@mod.route("/<uuid:session_uuid>/create_invite", methods=["POST"])
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
            "link": url_for("api/session.join_to_session", token=invite.uuid),
            "token": invite.uuid,
        }
    )


@mod.route("/vote", methods=["POST"])
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
        abort(
            403,
            "Пользователь не является участником сессии, в которой голосует",
        )

    session = get_trip_session_by_id(session_id)

    voting_attributes = get_voting_attributes(session_id, session.route.duration_days)
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
            TripVoteDTO.model_validate(vote).model_dump() for vote in trip_votes_to_add
        ]
    )
