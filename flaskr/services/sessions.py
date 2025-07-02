from flaskr.models.trip import TripParticipant


def is_many_travelers_in_session(session_id: int) -> bool:
    participations = TripParticipant.query.filter_by(session_id=session_id).all()
    return len(participations) > 1
