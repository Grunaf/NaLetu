import functools

from flask import abort, request, session as fk_session
import shortuuid

from flaskr.db.trip_sessions import get_trip_session_by_uuid
from flaskr.services.travelers import get_or_create_traveler, get_uuid_traveler


def is_participant_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        short_uuid = request.args.get("session_uuid")
        if short_uuid is None:
            abort(400, "Укажите uuid сессии")

        session_uuid = shortuuid.decode(short_uuid)
        session = get_trip_session_by_uuid(session_uuid)
        if session is None:
            abort(404, "Сессия не найдена")

        user_uuid = get_uuid_traveler()
        user_name = fk_session.get("user_name")
        user = get_or_create_traveler(user_uuid, user_name)
        if (
            int(session.id)
            not in [participation.session_id for participation in user.participations]
            and "join" not in request.url
        ):
            abort(403)

        return view(**kwargs)

    return wrapped_view
