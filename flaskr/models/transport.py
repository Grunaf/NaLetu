import datetime

from sqlalchemy import ForeignKey, JSON, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from flaskr.models.models import db


class TransportCache(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    start_city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))
    end_city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))
    data_json: Mapped[JSON] = mapped_column(type_=(JSON))
    date_at: Mapped[datetime.date] = mapped_column(db.DateTime)
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        onupdate=datetime.datetime.now(), default=datetime.datetime.now()
    )


class TransportPriceEntry(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[int] = mapped_column(SmallInteger)
    object_id: Mapped[int]
    last_known_price: Mapped[int]
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now(), onupdate=datetime.datetime.now()
    )
    source_url: Mapped[str]


class TransitionOption(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str]
    time_min: Mapped[int]
    cost_rub: Mapped[int | None]
    is_default: Mapped[bool] = mapped_column(default=False)
    segment_id: Mapped[int] = mapped_column(ForeignKey("segment.id"))
