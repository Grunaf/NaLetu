from flaskr.services.sessions import get_traveler_trip_sessions
from tests.factories import (
    TravelerFactory,
    TripParticipationFactory,
    TripSessionFactory,
)


def test_get_traveler_trip_sessions_if_no_session():
    traveler = TravelerFactory.create()

    sessions = get_traveler_trip_sessions(traveler.uuid)

    assert len(sessions) == 0


def test_get_traveler_trip_sessions_not_owned():
    traveler = TravelerFactory.create()
    TripParticipationFactory.create_batch(3)

    sessions = get_traveler_trip_sessions(traveler.uuid)

    assert len(sessions) == 0


def test_get_traveler_trip_sessions_owned():
    traveler = TravelerFactory.create()
    TripSessionFactory.create_batch(2)
    TripParticipationFactory.create_batch(3, user=traveler)

    sessions = get_traveler_trip_sessions(traveler.uuid)

    assert len(sessions) == 3
