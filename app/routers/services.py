from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Service, TherapistProfile, TherapistService, User
from app.schemas import ServiceInput, ServiceOutput, TherapistOutput
from app.security import require_role

router = APIRouter(prefix='/api', tags=['services'])


@router.get('/services', response_model=list[ServiceOutput])
def list_services(db: Session = Depends(get_db)):
    return db.query(Service).order_by(Service.name).all()


@router.post('/services', response_model=ServiceOutput, status_code=201)
def create_service(
    data: ServiceInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_role('admin'))
):
    existing_service = db.query(Service).filter(Service.name == data.name.strip()).first()

    if existing_service is not None:
        raise HTTPException(status_code=409, detail='Service already exists')

    service = Service(**data.model_dump())
    service.name = service.name.strip()
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get('/therapists', response_model=list[TherapistOutput])
def list_therapists(db: Session = Depends(get_db)):
    therapists = db.query(TherapistProfile).join(User).order_by(User.name).all()
    result = []

    for therapist in therapists:
        result.append(
            TherapistOutput(
                id=therapist.id,
                name=therapist.user.name,
                email=therapist.user.email,
                bio=therapist.bio,
                service_ids=[item.service_id for item in therapist.services]
            )
        )

    return result


@router.post('/therapists/{therapist_id}/services/{service_id}', status_code=201)
def add_therapist_service(
    therapist_id: int,
    service_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role('admin'))
):
    therapist = db.get(TherapistProfile, therapist_id)
    service = db.get(Service, service_id)

    if therapist is None or service is None:
        raise HTTPException(status_code=404, detail='Therapist or service not found')

    existing = db.query(TherapistService).filter(
        TherapistService.therapist_id == therapist_id,
        TherapistService.service_id == service_id
    ).first()

    if existing is not None:
        raise HTTPException(status_code=409, detail='Service already assigned')

    db.add(TherapistService(therapist_id=therapist_id, service_id=service_id))
    db.commit()
    return {'message': 'Service assigned'}
