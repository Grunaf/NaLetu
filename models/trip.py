import uuid as m_uuid
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Index, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.models import City, DayVariant, Route, db

ADMIN = 0
MODERATOR = 1
ROLE = {ADMIN: "admin", MODERATOR: "moderator"}

NEW = 0
APPROVED = 1
REJECTED = 2
STATUC_REQUEST = {NEW: "new", APPROVED: "approved", REJECTED: "rejected"}


class DataEntryMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(), onupdate=datetime.now()
    )


class TripSession(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, default=m_uuid.uuid4()
    )
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    departure_city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))

    start_date: Mapped[date] = mapped_column(db.Date)
    end_date: Mapped[date] = mapped_column(db.Date)
    choices_json: Mapped[JSON] = mapped_column(type_=JSON)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now())
    participants: Mapped[list["TripParticipant"]] = relationship(
        back_populates="session"
    )
    route: Mapped["Route"] = relationship()
    city: Mapped["City"] = relationship()


class UserMixin:
    uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=m_uuid.uuid4()
    )
    name: Mapped[Optional[str]] = mapped_column(default=None)


class Traveler(UserMixin, db.Model):
    __tablename__ = "traveler"
    sessions: Mapped[list["TripParticipant"]] = relationship(back_populates="user")


class Staff(UserMixin, db.Model):
    __tablename__ = "staff"

    first_name: Mapped[str]
    last_name: Mapped[str]
    login: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    role: Mapped[int] = mapped_column(SmallInteger, default=MODERATOR)
    request: Mapped["AdditionRequest"] = relationship(back_populates="staff")

    @property
    def is_authenticated(self):
        return self.role == ADMIN or (
            self.role == MODERATOR and
            self.request.status == APPROVED
            )

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.uuid

    def __unicode__(self):
        return self.username


class AdditionRequest(DataEntryMixin, db.Model):
    __tablename__ = "addition_request"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=NEW)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.uuid"))

    staff: Mapped[Staff] = relationship(back_populates="request")


class TripParticipant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traveler.uuid"), default=m_uuid.uuid4()
    )
    session_id: Mapped[int] = mapped_column(ForeignKey("trip_session.id"))
    join_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now())
    is_admin: Mapped[bool] = mapped_column(server_default="False")

    session: Mapped["TripSession"] = relationship(back_populates="participants")
    user: Mapped["Traveler"] = relationship(back_populates="sessions")

    votes: Mapped[list["TripVote"]] = relationship(back_populates="participant")

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
    uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=m_uuid.uuid4()
    )
    session_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_session.uuid")
    )
    is_active: Mapped[bool] = mapped_column(server_default="True")
    expired_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=lambda: datetime.now() + timedelta(1)
    )
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now())

    session: Mapped[TripSession] = relationship


class TripVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("trip_session.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("day_variant.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("trip_participant.id"))
    day_order: Mapped[int]
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now(), onupdate=datetime.now()
    )

    day_variant: Mapped["DayVariant"] = relationship()
    participant: Mapped["TripParticipant"] = relationship(back_populates="votes")
