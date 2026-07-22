from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import AvailabilitySlot


def login(client, email, password):
    response = client.post('/api/auth/login', json={
        'email': email,
        'password': password
    })
    return response.json()['token']


def test_create_booking(client):
    token = login(client, 'client@example.com', 'client123')

    availability = client.get('/api/availability').json()[0]
    response = client.post('/api/bookings', json={
        'therapist_id': 1,
        'service_id': 1,
        'start_time': availability['start_time'],
        'note': 'First appointment'
    }, headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 201
    assert response.json()['status'] == 'pending'
    assert response.json()['service_name'] == 'Relaxing Massage'


def test_prevent_overlapping_booking(client):
    first_token = login(client, 'client@example.com', 'client123')

    register = client.post('/api/auth/register', json={
        'name': 'Second Client',
        'email': 'second@example.com',
        'password': 'second123'
    })
    second_token = register.json()['token']

    availability = client.get('/api/availability').json()[0]
    booking_data = {
        'therapist_id': 1,
        'service_id': 1,
        'start_time': availability['start_time'],
        'note': ''
    }

    first = client.post('/api/bookings', json=booking_data, headers={
        'Authorization': f'Bearer {first_token}'
    })
    second = client.post('/api/bookings', json=booking_data, headers={
        'Authorization': f'Bearer {second_token}'
    })

    assert first.status_code == 201
    assert second.status_code == 409


def test_booking_outside_availability(client):
    token = login(client, 'client@example.com', 'client123')
    start_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=20)

    response = client.post('/api/bookings', json={
        'therapist_id': 1,
        'service_id': 1,
        'start_time': start_time.isoformat(),
        'note': ''
    }, headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 400



def test_therapist_can_confirm_booking(client):
    client_token = login(client, 'client@example.com', 'client123')
    therapist_token = login(client, 'sara@example.com', 'sara123')
    availability = client.get('/api/availability').json()[0]

    created = client.post('/api/bookings', json={
        'therapist_id': 1,
        'service_id': 1,
        'start_time': availability['start_time'],
        'note': ''
    }, headers={'Authorization': f'Bearer {client_token}'})

    booking_id = created.json()['id']
    response = client.patch(f'/api/bookings/{booking_id}/status', json={
        'status': 'confirmed'
    }, headers={'Authorization': f'Bearer {therapist_token}'})

    assert response.status_code == 200
    assert response.json()['status'] == 'confirmed'


def test_client_cannot_confirm_booking(client):
    token = login(client, 'client@example.com', 'client123')
    availability = client.get('/api/availability').json()[0]

    created = client.post('/api/bookings', json={
        'therapist_id': 1,
        'service_id': 1,
        'start_time': availability['start_time'],
        'note': ''
    }, headers={'Authorization': f'Bearer {token}'})

    booking_id = created.json()['id']
    response = client.patch(f'/api/bookings/{booking_id}/status', json={
        'status': 'confirmed'
    }, headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 403
