from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AvailabilitySlot, Booking, Service, TherapistProfile, TherapistService


ACTIVE_STATUSES = ['pending', 'confirmed']


def get_booking_end(start_time, duration_minutes):
    return start_time + timedelta(minutes=duration_minutes)


def validate_booking(
    db: Session,
    therapist: TherapistProfile,
    service: Service,
    start_time
):
    therapist_service = db.query(TherapistService).filter(
        TherapistService.therapist_id == therapist.id,
        TherapistService.service_id == service.id
    ).first()

    if therapist_service is None:
        raise HTTPException(status_code=400, detail='Therapist does not provide this service')

    end_time = get_booking_end(start_time, service.duration_minutes)

    slot = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.therapist_id == therapist.id,
        AvailabilitySlot.is_available.is_(True),
        AvailabilitySlot.start_time <= start_time,
        AvailabilitySlot.end_time >= end_time
    ).first()

    if slot is None:
        raise HTTPException(status_code=400, detail='Selected time is not available')

    conflict = db.query(Booking).filter(
        Booking.therapist_id == therapist.id,
        Booking.status.in_(ACTIVE_STATUSES),
        Booking.start_time < end_time,
        Booking.end_time > start_time
    ).first()

    if conflict is not None:
        raise HTTPException(status_code=409, detail='Selected time is already booked')

    return end_time
