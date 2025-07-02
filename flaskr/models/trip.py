from typing import TYPE_CHECKING
import uuid as module_uuid
from datetime import date, datetime, timedelta

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from .models import db

if TYPE_CHECKING:
    from .city import City
    from .route import DayVariant, Route
    from .user import Traveler


class TripSession(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[module_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, default=module_uuid.uuid4
    )
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    departure_city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))

    start_date: Mapped[date]
    end_date: Mapped[date]

    created_at: Mapped[datetime] = mapped_column(default=datetime.now())

    route: Mapped["Route"] = relationship()
    city: Mapped["City"] = relationship()


class TripParticipant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traveler.uuid")
    )
    session_id: Mapped[int] = mapped_column(ForeignKey("trip_session.id"))
    join_at: Mapped[datetime] = mapped_column(default=datetime.now())
    is_admin: Mapped[bool] = mapped_column(server_default="False")

    #   можно будет удалить когда перейду на uuid с id
    session: Mapped["TripSession"] = relationship()
    user: Mapped["Traveler"] = relationship(back_populates="participations")

    votes: Mapped[list["TripVote"]] = relationship(back_populates="participation")

    __table_tags__ = (
        Index(
            "one_admin_for_session",
            session_id,
            is_admin,
            unique=True,
            postgresql_where=("is_admin"),
        ),
    )


class TripInvite(db.Model):
    uuid: Mapped[module_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=module_uuid.uuid4
    )
    session_uuid: Mapped[module_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_session.uuid")
    )
    is_active: Mapped[bool] = mapped_column(server_default="True")

    expired_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now() + timedelta(1)
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())


class TripVote(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("trip_session.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("day_variant.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("trip_participant.id"))
    day_order: Mapped[int]
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(), onupdate=datetime.now()
    )

    day_variant: Mapped["DayVariant"] = relationship()
    participation: Mapped["TripParticipant"] = relationship(back_populates="votes")
