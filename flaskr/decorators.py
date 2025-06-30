import functools

from flask import abort, request

from flaskr.services.travelers import get_or_create_traveler, get_uuid_traveler


def is_participant_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        trip_session_id = request.args.get("sessionId")
        if trip_session_id is None:
            abort(400, "Укажите id сессии")

        user_uuid = get_uuid_traveler()
        user = get_or_create_traveler(user_uuid)
        if (
            int(trip_session_id) not in [s.session_id for s in user.sessions]
            and "join" not in request.url
        ):
            abort(403)

        return view(**kwargs)

    return wrapped_view
