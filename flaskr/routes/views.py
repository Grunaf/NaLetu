import datetime
from datetime import date

import shortuuid
from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)
from flask import session as fk_session
from werkzeug.wrappers.response import Response

from config import Config
from flaskr.constants import (
    CITY_NOT_FOUND,
    DEFAULT_CITY_SLUG,
    INVALID_INVITE,
    INVITE_NOT_FOUND,
    PARTIAL_VOTES,
    SESSION_NOT_FOUND,
    SESSION_UUID_REQUIRED,
    TRANSPORTS_NOT_FOUND,
)
from flaskr.db.cities import get_city_by_slug
from flaskr.db.participations import (
    create_participant,
    get_session_named_participations,
)
from flaskr.db.segments import get_segments_for_variants
from flaskr.db.trip_invites import deactivate_trip_invite, get_trip_invite_by_uuid
from flaskr.db.trip_sessions import get_trip_session_by_uuid
from flaskr.decorators import is_participant_required
from flaskr.models.constants import MEAL as MEAL_TYPE
from flaskr.models.constants import POI as POI_TYPE
from flaskr.models.models import db
from flaskr.models.route import POI, Day, DayVariant, Route, Segment
from flaskr.models.trip import TripInvite, TripVote
from flaskr.schemas.city import City
from flaskr.schemas.route import DayRead
from flaskr.schemas.segment import MealPlaceDTO, SegmentDTO
from flaskr.schemas.trip import (
    TripSessionBase,
)
from flaskr.schemas.users import Traveler as TravelerRead
from flaskr.services.get_f_api_transports import get_transports
from flaskr.services.get_meal_places import get_f_db_meal_places_near_poi
from flaskr.services.routes import get_routes_for_departure_city
from flaskr.services.sessions import get_traveler_trip_sessions
from flaskr.services.travelers import (
    get_uuid_traveler,
    is_traveler_in_session,
)
from flaskr.services.voting import (
    get_days_with_winner_variant,
    get_travelers_choosed_variant,
    get_voting_attributes,
)
from flaskr.utils import format_transports

YA_MAP_API_KEY = Config.YA_MAP_API_KEY

mod = Blueprint("views", __name__)


@mod.route("/")
@mod.route("/city/")
@mod.route("/city/<city_slug>/routes/")
def catalog_routes(city_slug: str | None = None) -> str:
    if city_slug is None:
        city = get_city_by_slug(DEFAULT_CITY_SLUG)
    else:
        city = get_city_by_slug(city_slug)

    user_city = City.model_validate(city).model_dump()
    fk_session["user_city"] = user_city

    if city is None:
        abort(404, CITY_NOT_FOUND)

    routes_db = get_routes_for_departure_city(city.location, city.lat)
    routes = []
    for route in routes_db:
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

    traveler_uuid = get_uuid_traveler()
    sessions = get_traveler_trip_sessions(traveler_uuid)

    return render_template(
        "catalog.html", routes=routes, sessions=sessions, show_user_city=True
    )


@mod.route("/session/<short_uuid>/trip-setup/")
@mod.route("/trip-setup/")
@is_participant_required
def trip_setup(short_uuid: str | None = None) -> str:
    if short_uuid is None:
        short_uuid = request.args.get("session_uuid")
    if not short_uuid:
        abort(400, SESSION_UUID_REQUIRED)

    session_uuid = shortuuid.decode(short_uuid)
    trip_session = get_trip_session_by_uuid(session_uuid)
    if trip_session is None:
        abort(404, SESSION_NOT_FOUND)

    departure_city = trip_session.city
    trip_session_read = TripSessionBase(
        short_uuid=short_uuid,
        start_date=trip_session.start_date,
        end_date=trip_session.end_date,
        departure_city_name=departure_city.name,
    )
    trip_session_read.short_uuid = short_uuid
    route = trip_session.route
    plan = {
        "title": route.title,
        "durations_day": route.duration_days,
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
            for d in sorted(route.days, key=lambda d: d.day_order)
        ],
    }
    voting_attributes = get_voting_attributes(trip_session.id, route.duration_days)

    user_uuid = get_uuid_traveler()
    travelers = get_session_named_participations(trip_session.id)
    other_travelers = [
        TravelerRead.model_validate(traveler.user)
        for traveler in travelers
        if traveler.user_uuid != user_uuid
    ]

    show_name_modal = False if fk_session.get("user_name") else True

    return render_template(
        "trip-setup.html",
        show_name_modal=show_name_modal,
        voting_attributes=voting_attributes,
        trip_session=trip_session_read,
        other_travelers=other_travelers,
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

    user_uuid = get_uuid_traveler()
    travelers = get_session_named_participations(session.id)
    other_travelers = [
        TravelerRead.model_validate(traveler.user)
        for traveler in travelers
        if traveler.user_uuid != user_uuid
    ]

    departure_city_name = session.city.name

    return render_template(
        "trip-itinerary.html",
        route=route,
        session=session,
        departure_city_name=departure_city_name,
        other_travelers=other_travelers,
        days=days,
        transports=transports,
        POI_TYPE=POI_TYPE,
        MEAL_TYPE=MEAL_TYPE,
        ya_map_js_api_key=YA_MAP_API_KEY,
    )


@mod.route("/join/<short_invite_uuid>")
def join_to_session(short_invite_uuid: str) -> Response:
    invite_uuid = shortuuid.decode(short_invite_uuid)
    invite: TripInvite | None = get_trip_invite_by_uuid(invite_uuid)

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
