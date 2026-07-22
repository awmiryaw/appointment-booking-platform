from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import AvailabilitySlot, Service, TherapistProfile, TherapistService, User
from app.security import hash_password


def seed_database(db: Session):
    if db.query(User).first() is not None:
        return

    admin = User(
        name='Admin User',
        email='admin@example.com',
        password_hash=hash_password('admin123'),
        role='admin'
    )
    therapist_user = User(
        name='Sara Rossi',
        email='sara@example.com',
        password_hash=hash_password('sara123'),
        role='therapist'
    )
    client = User(
        name='Demo Client',
        email='client@example.com',
        password_hash=hash_password('client123'),
        role='client'
    )
    db.add_all([admin, therapist_user, client])
    db.flush()

    therapist = TherapistProfile(
        user_id=therapist_user.id,
        bio='Massage therapist focused on relaxation and recovery.'
    )
    db.add(therapist)

    relaxing = Service(
        name='Relaxing Massage',
        duration_minutes=60,
        price_cents=5500,
        description='A full-body relaxing massage.'
    )
    sports = Service(
        name='Sports Massage',
        duration_minutes=45,
        price_cents=5000,
        description='A focused massage for muscle recovery.'
    )
    db.add_all([relaxing, sports])
    db.flush()

    db.add_all([
        TherapistService(therapist_id=therapist.id, service_id=relaxing.id),
        TherapistService(therapist_id=therapist.id, service_id=sports.id)
    ])

    start = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    db.add(
        AvailabilitySlot(
            therapist_id=therapist.id,
            start_time=start,
            end_time=start + timedelta(hours=8)
        )
    )

    db.commit()
