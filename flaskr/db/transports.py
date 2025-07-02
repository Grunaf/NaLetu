from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.transport import TransportCache


def get_transport_cache(date, from_city_id, to_city_id) -> TransportCache | None:
    stmt = select(TransportCache).filter_by(
        date_at=date, start_city_id=from_city_id, end_city_id=to_city_id
    )
    return db.session.execute(stmt).scalar()


def create_transport_cache(
    date, from_city_id, to_city_id, transport_segments
) -> TransportCache:
    transport_cache = TransportCache(
        start_city_id=from_city_id,
        end_city_id=to_city_id,
        data_json=transport_segments,
        date_at=date,
    )
    db.session.add(transport_cache)
    db.session.commit()
    return transport_cache
