from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='client')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    therapist_profile: Mapped['TherapistProfile | None'] = relationship(
        back_populates='user', cascade='all, delete-orphan', uselist=False
    )
    sessions: Mapped[list['UserSession']] = relationship(
        back_populates='user', cascade='all, delete-orphan'
    )


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped[User] = relationship(back_populates='sessions')


class TherapistProfile(Base):
    __tablename__ = 'therapist_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    bio: Mapped[str] = mapped_column(Text, default='')

    user: Mapped[User] = relationship(back_populates='therapist_profile')
    services: Mapped[list['TherapistService']] = relationship(
        back_populates='therapist', cascade='all, delete-orphan'
    )
    availability: Mapped[list['AvailabilitySlot']] = relationship(
        back_populates='therapist', cascade='all, delete-orphan'
    )
    bookings: Mapped[list['Booking']] = relationship(back_populates='therapist')


class Service(Base):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, default='')

    therapists: Mapped[list['TherapistService']] = relationship(
        back_populates='service', cascade='all, delete-orphan'
    )
    bookings: Mapped[list['Booking']] = relationship(back_populates='service')


class TherapistService(Base):
    __tablename__ = 'therapist_services'
    __table_args__ = (
        UniqueConstraint('therapist_id', 'service_id', name='uq_therapist_service'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    therapist_id: Mapped[int] = mapped_column(ForeignKey('therapist_profiles.id', ondelete='CASCADE'))
    service_id: Mapped[int] = mapped_column(ForeignKey('services.id', ondelete='CASCADE'))

    therapist: Mapped[TherapistProfile] = relationship(back_populates='services')
    service: Mapped[Service] = relationship(back_populates='therapists')


class AvailabilitySlot(Base):
    __tablename__ = 'availability_slots'
    __table_args__ = (
        UniqueConstraint('therapist_id', 'start_time', 'end_time', name='uq_therapist_slot'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    therapist_id: Mapped[int] = mapped_column(ForeignKey('therapist_profiles.id', ondelete='CASCADE'))
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    therapist: Mapped[TherapistProfile] = relationship(back_populates='availability')


class Booking(Base):
    __tablename__ = 'bookings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    therapist_id: Mapped[int] = mapped_column(ForeignKey('therapist_profiles.id', ondelete='CASCADE'))
    service_id: Mapped[int] = mapped_column(ForeignKey('services.id', ondelete='CASCADE'))
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    note: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    client: Mapped[User] = relationship(foreign_keys=[client_id])
    therapist: Mapped[TherapistProfile] = relationship(back_populates='bookings')
    service: Mapped[Service] = relationship(back_populates='bookings')
