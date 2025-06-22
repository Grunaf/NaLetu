import datetime

from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models import db

if TYPE_CHECKING:
    from .route import Segment


class POI(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    must_see: Mapped[bool] = mapped_column(default=False)
    open_time: Mapped[datetime.time | None] = mapped_column(default=None)
    close_time: Mapped[datetime.time | None] = mapped_column(default=None)
    rating: Mapped[float | None] = mapped_column(default=None)

    lat: Mapped[float]
    lon: Mapped[float]

    segment: Mapped["Segment"] = relationship(back_populates="poi")
