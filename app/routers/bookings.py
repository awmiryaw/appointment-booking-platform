from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.booking_logic import validate_booking
from app.database import get_db
from app.models import Booking, Service, TherapistProfile, User
from app.schemas import BookingInput, BookingOutput, BookingStatusInput
from app.security import get_current_user

router = APIRouter(prefix='/api/bookings', tags=['bookings'])


def booking_output(booking: Booking):
    return BookingOutput(
        id=booking.id,
        client_id=booking.client_id,
        client_name=booking.client.name,
        therapist_id=booking.therapist_id,
        therapist_name=booking.therapist.user.name,
        service_id=booking.service_id,
        service_name=booking.service.name,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        note=booking.note
    )


@router.post('', response_model=BookingOutput, status_code=201)
def create_booking(
    data: BookingInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role != 'client':
        raise HTTPException(status_code=403, detail='Only clients can create bookings')

    therapist = db.get(TherapistProfile, data.therapist_id)
    service = db.get(Service, data.service_id)

    if therapist is None or service is None:
        raise HTTPException(status_code=404, detail='Therapist or service not found')

    end_time = validate_booking(db, therapist, service, data.start_time)

    booking = Booking(
        client_id=user.id,
        therapist_id=therapist.id,
        service_id=service.id,
        start_time=data.start_time,
        end_time=end_time,
        note=data.note.strip()
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking_output(booking)


@router.get('', response_model=list[BookingOutput])
def list_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    query = db.query(Booking).options(
        joinedload(Booking.client),
        joinedload(Booking.therapist).joinedload(TherapistProfile.user),
        joinedload(Booking.service)
    )

    if user.role == 'client':
        query = query.filter(Booking.client_id == user.id)
    elif user.role == 'therapist':
        query = query.filter(Booking.therapist_id == user.therapist_profile.id)

    bookings = query.order_by(Booking.start_time.desc()).all()
    return [booking_output(item) for item in bookings]


@router.patch('/{booking_id}/status', response_model=BookingOutput)
def update_booking_status(
    booking_id: int,
    data: BookingStatusInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    allowed_statuses = ['confirmed', 'rejected', 'cancelled']

    if data.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail='Invalid booking status')

    booking = db.query(Booking).options(
        joinedload(Booking.client),
        joinedload(Booking.therapist).joinedload(TherapistProfile.user),
        joinedload(Booking.service)
    ).filter(Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(status_code=404, detail='Booking not found')

    if user.role == 'client':
        if booking.client_id != user.id or data.status != 'cancelled':
            raise HTTPException(status_code=403, detail='Permission denied')
    elif user.role == 'therapist':
        if booking.therapist_id != user.therapist_profile.id or data.status == 'cancelled':
            raise HTTPException(status_code=403, detail='Permission denied')
    elif user.role != 'admin':
        raise HTTPException(status_code=403, detail='Permission denied')

    booking.status = data.status
    db.commit()
    db.refresh(booking)
    return booking_output(booking)
