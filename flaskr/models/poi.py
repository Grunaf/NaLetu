import datetime

from sqlalchemy.orm import Mapped, mapped_column

from .models import db


class POI(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    must_see: Mapped[bool] = mapped_column(default=False)
    open_time: Mapped[datetime.time | None] = mapped_column(default=None)
    close_time: Mapped[datetime.time | None] = mapped_column(default=None)
    rating: Mapped[float | None] = mapped_column(default=None)

    lat: Mapped[float]
    lon: Mapped[float]
