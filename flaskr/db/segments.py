from typing import List

from sqlalchemy import select
from sqlalchemy.orm import joinedload


from flaskr.models.models import db
from flaskr.models.route import Segment


def get_segment_by_poi(poi_id: int) -> Segment | None:
    stmt = select(Segment).where(Segment.poi_id == poi_id)
    return db.session.execute(stmt).scalars().first()

def get_segments_for_variants(variant_id: int) -> List[Segment]:
    stmt = (
        select(Segment)
        .options(joinedload(Segment.poi))
        .where(Segment.variant_id == variant_id)
        .order_by(Segment.order)
    )
    return db.session.execute(stmt).scalars().all()
