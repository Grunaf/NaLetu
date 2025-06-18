from typing import Optional
import uuid as m_uuid
from models.models import DayVariant, db, Route, City
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, JSON
from datetime import datetime, timedelta, date

class TripSession(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=m_uuid.uuid4())
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    departure_city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))

    start_date: Mapped[date]  = mapped_column(db.Date)
    end_date: Mapped[date] = mapped_column(db.Date)
    choices_json: Mapped[JSON] = mapped_column(type_=JSON)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now())
    participants: Mapped[list["TripParticipant"]] = relationship(back_populates="session")
    route: Mapped["Route"] = relationship()
    city: Mapped["City"] = relationship()

class User(db.Model):
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=m_uuid.uuid4())
    name: Mapped[Optional[str]] = mapped_column(default=None)

    sessions: Mapped[list["TripParticipant"]] = relationship(back_populates="user")

class TripParticipant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.uuid"), default=m_uuid.uuid4())
    session_id: Mapped[int] = mapped_column(ForeignKey("trip_session.id"))
    join_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now())
    is_admin: Mapped[bool] = mapped_column(server_default="False")

    session: Mapped["TripSession"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="sessions")
    
    votes: Mapped[list["TripVote"]] = relationship(back_populates="participant")

    __table_tags__ = (
        Index("one_admin_for_session", session_id, is_admin, unique=True, postgresql_where=("is_admin"))
    ,)

class TripInvite(db.Model):
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,  default=m_uuid.uuid4())
    session_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trip_session.uuid"))
    is_active: Mapped[bool] = mapped_column(server_default="True")
    expired_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda:datetime.now() + timedelta(1))
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now())

    session: Mapped[TripSession] = relationship

class TripVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("trip_session.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("day_variant.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("trip_participant.id"))
    day_order: Mapped[int]
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now(), onupdate=datetime.now())

    day_variant: Mapped["DayVariant"] = relationship()
    participant: Mapped["TripParticipant"] = relationship(back_populates="votes")

