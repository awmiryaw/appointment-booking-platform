from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AvailabilitySlot, TherapistProfile, User
from app.schemas import AvailabilityInput, AvailabilityOutput
from app.security import get_current_user

router = APIRouter(prefix='/api/availability', tags=['availability'])


@router.get('', response_model=list[AvailabilityOutput])
def list_availability(
    therapist_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.is_available.is_(True),
        AvailabilitySlot.end_time > datetime.now(timezone.utc).replace(tzinfo=None)
    )

    if therapist_id is not None:
        query = query.filter(AvailabilitySlot.therapist_id == therapist_id)

    return query.order_by(AvailabilitySlot.start_time).all()


@router.post('', response_model=AvailabilityOutput, status_code=201)
def create_availability(
    data: AvailabilityInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role not in ['therapist', 'admin']:
        raise HTTPException(status_code=403, detail='Permission denied')

    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail='End time must be after start time')

    if user.role == 'therapist':
        therapist = user.therapist_profile
    else:
        raise HTTPException(status_code=400, detail='Admin must use a therapist account for availability')

    overlap = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.therapist_id == therapist.id,
        AvailabilitySlot.start_time < data.end_time,
        AvailabilitySlot.end_time > data.start_time
    ).first()

    if overlap is not None:
        raise HTTPException(status_code=409, detail='Availability overlaps another slot')

    slot = AvailabilitySlot(
        therapist_id=therapist.id,
        start_time=data.start_time,
        end_time=data.end_time
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot
