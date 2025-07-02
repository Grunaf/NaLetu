import datetime
from datetime import date

import shortuuid
from werkzeug.wrappers.response import Response
from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)
from flask import session as fk_session

from config import Config
from flaskr.constants import (
    INVALID_INVITE,
    INVITE_NOT_FOUND,
    PARTIAL_VOTES,
    SESSION_NOT_FOUND,
    SESSION_UUID_REQUIRED,
    TRANSPORTS_NOT_FOUND,
)
from flaskr.db.participants import create_participant, get_named_participants
from flaskr.db.segments import get_segments_for_variants
from flaskr.db.trip_invites import deactivate_trip_invite, get_trip_invite_by_uuid
from flaskr.db.trip_sessions import get_trip_session_by_uuid
from flaskr.decorators import is_participant_required
from flaskr.models.constants import MEAL as MEAL_TYPE
from flaskr.models.constants import POI as POI_TYPE
from flaskr.models.models import db
from flaskr.models.route import POI, Day, DayVariant, Route, Segment
from flaskr.models.trip import TripInvite, TripVote
from flaskr.schemas.route import DayRead
from flaskr.schemas.segment import MealPlaceDTO, SegmentDTO
from flaskr.schemas.users import Traveler as TravelerRead
from flaskr.services.get_f_api_transports import get_transports
from flaskr.services.get_meal_places import get_f_db_meal_places_near_poi
from flaskr.services.travelers import get_uuid_traveler, is_traveler_in_session
from flaskr.services.voting import (
    get_days_with_winner_variant,
    get_travelers_choosed_variant,
    get_voting_attributes,
)
from flaskr.utils import format_transports

YA_MAP_API_KEY = Config.YA_MAP_API_KEY

mod = Blueprint("views", __name__)


@mod.route("/")
@mod.route("/routes")
def catalog_routes() -> str:
    routes = []
    for route in Route.query.all():
        start = route.cities[0]
        est_budget_rub = (
            route.estimated_budget_rub
            if route.estimated_budget_rub != 0
            else "Цена не указана"
        )
        data = {
            "id": route.id,
            "title": route.title,
            "duration_days": route.duration_days,
            "estimated_budget_rub": est_budget_rub,
            "img": route.img,
            "start_coords": [start.city.lat, start.city.lon],
        }

        pois = (
            POI.query.join(Segment, POI.id == Segment.poi_id)
            .join(DayVariant, Segment.variant_id == DayVariant.id)
            .join(Day, DayVariant.day_id == Day.id)
            .filter(Day.route_id == route.id, Segment.type == POI_TYPE)
            .all()
        )
        # 3) кладём список упрощённых POI
        data["pois"] = [{"name": p.name, "rating": p.rating} for p in pois]
        routes.append(data)

    return render_template("catalog.html", routes=routes)


@mod.route("/trip-setup/")
@is_participant_required
def trip_setup() -> str:
    short_uuid = request.args.get("session_uuid")
    if not short_uuid:
        abort(400, SESSION_UUID_REQUIRED)

    session_uuid = shortuuid.decode(short_uuid)
    trip_session = get_trip_session_by_uuid(session_uuid)
    if not trip_session:
        abort(404, SESSION_NOT_FOUND)
    plan = {
        "session_uuid": short_uuid,
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
                        "travelers_choosed": get_travelers_choosed_variant(
                            v.id, trip_session.id
                        ),
                    }
                    for v in d.variants
                ],
            }
            for d in sorted(trip_session.route.days, key=lambda d: d.day_order)
        ],
    }
    voting_attributes = get_voting_attributes(
        trip_session.id, trip_session.route.duration_days
    )

    participants = get_named_participants(trip_session.id)
    user_uuid = get_uuid_traveler()
    other_travelers = [
        TravelerRead.model_validate(participant.user)
        for participant in participants
        if participant.user_uuid != user_uuid
    ]
    show_name_modal = False if fk_session.get("user_name") else True

    return render_template(
        "trip-setup.html",
        show_name_modal=show_name_modal,
        voting_attributes=voting_attributes,
        participants=other_travelers,
        plan=plan,
        today=date.today(),
    )


@mod.route("/trip-itinerary/")
@is_participant_required
def trip_itinerary() -> str:
    short_uuid = request.args.get("session_uuid")
    if not short_uuid:
        abort(400, SESSION_UUID_REQUIRED)

    session_uuid = shortuuid.decode(short_uuid)
    session = get_trip_session_by_uuid(session_uuid)
    if not session:
        abort(404)

    route = db.session.get(Route, session.route_id)
    if not route:
        abort(404)

    votes = list(TripVote.query.filter_by(session_id=session.id).all())
    days_with_winner_variant: list[DayRead] = get_days_with_winner_variant(
        votes, session.route.duration_days
    )
    days = []
    if len(days_with_winner_variant) != len(route.days):
        abort(500, PARTIAL_VOTES)
    for day_count, day in enumerate(route.days):
        day_with_variant: DayRead = days_with_winner_variant[day_count]
        variant_id = day_with_variant.variant.id

        segments_for_variants = get_segments_for_variants(variant_id)

        segment_dtos = []
        for i in range(len(segments_for_variants)):
            current_segment = segments_for_variants[i]
            if current_segment.type == MEAL_TYPE and i != 0:
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
                segment_dtos.append(SegmentDTO(**model_dump, meal_places=meal_places))
                continue
            segment_dtos.append(SegmentDTO.model_validate(segments_for_variants[i]))

        days.append(
            {
                "day_order": day.day_order,
                "variant_id": variant_id,
                "segments": segment_dtos,
            }
        )
    if session.departure_city_id != route.cities[0].city_id:
        transports_to_with_data_json = get_transports(
            session.start_date, session.city, route.cities[0].city
        )
        transports_from_with_data_json = get_transports(
            session.end_date, route.cities[0].city, session.city
        )
        if (
            transports_from_with_data_json is None
            or transports_to_with_data_json is None
        ):
            abort(500, TRANSPORTS_NOT_FOUND)
        transports_to_json = transports_to_with_data_json.data_json
        transports_from_json = transports_from_with_data_json.data_json
        transports = {}

        transports["there"] = [format_transports(t_to) for t_to in transports_to_json]
        transports["back"] = [
            format_transports(t_from) for t_from in transports_from_json
        ]
    else:
        transports = None

    return render_template(
        "trip-itinerary.html",
        route=route,
        session=session,
        days=days,
        transports=transports,
        POI_TYPE=POI_TYPE,
        MEAL_TYPE=MEAL_TYPE,
        ya_map_js_api_key=YA_MAP_API_KEY,
    )


@mod.route("/join/<short_invite_uuid>")
def join_to_session(short_invite_uuid: str) -> Response:
    invite_uuid = shortuuid.decode(short_invite_uuid)
    invite: TripInvite = get_trip_invite_by_uuid(invite_uuid)

    if invite is None:
        abort(404, INVITE_NOT_FOUND)

    user_uuid = get_uuid_traveler()
    session_uuid = invite.session_uuid
    if not is_traveler_in_session(user_uuid, session_uuid):
        if datetime.datetime.now() > invite.expired_at or invite.is_active is False:
            abort(410, INVALID_INVITE)

        session = get_trip_session_by_uuid(session_uuid)
        if session is None:
            abort(500, SESSION_NOT_FOUND)
        user_uuid = get_uuid_traveler()

        _ = create_participant(user_uuid=user_uuid, session_id=session.id)
        deactivate_trip_invite(invite)

    short_uuid = shortuuid.encode(session_uuid)
    return redirect(url_for("views.trip_setup", session_uuid=short_uuid))
