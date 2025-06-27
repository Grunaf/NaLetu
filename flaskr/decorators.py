import functools

from flask import abort, request, session as fk_session

from flaskr.models.models import db
from flaskr.models.user import User


def is_participant_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        trip_session_id = request.args.get("sessionId")
        if trip_session_id is None:
            abort(400, "Укажите id сессии")

        user = db.session.get(User, fk_session.get("uuid"))
        if user is not None:
            if (
                int(trip_session_id)
                not in [s.session_id for s in user.sessions]
                and "join" not in request.url
            ):
                abort(401)

        return view(**kwargs)

    return wrapped_view
