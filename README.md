# Appointment Booking and Availability Platform

A full-stack appointment booking project built with FastAPI, SQLAlchemy and PostgreSQL.

The platform allows clients to register, view therapists and services, check available time slots and create booking requests. Therapists can manage availability and review their appointments. Admin users can manage services and therapist-service assignments.

## Main Features

- Client registration and login
- Token-based authentication
- Client, therapist and admin roles
- Service catalogue
- Therapist profiles
- Therapist-service assignments
- Availability management
- Booking requests
- Booking conflict prevention
- Booking confirmation, rejection and cancellation
- PostgreSQL support with Docker
- SQLite fallback for a quick local run
- Automated API tests
- Simple responsive web interface
- Interactive API documentation

## Technologies

- Python
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- SQLite
- Pydantic
- Pytest
- Docker
- HTML, CSS and JavaScript

## Project Structure

```text
appointment-booking-platform/
├── app/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── availability.py
│   │   ├── bookings.py
│   │   └── services.py
│   ├── static/
│   │   ├── app.js
│   │   ├── index.html
│   │   └── style.css
│   ├── booking_logic.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── seed.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_bookings.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md
```

## Run Locally

Create a virtual environment and install the packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the application:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

The local setup uses SQLite automatically.

## Run with Docker and PostgreSQL

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:8000
```

## Demo Accounts

The application creates sample data on the first run.

```text
Client
client@example.com
client123

Therapist
sara@example.com
sara123

Admin
admin@example.com
admin123
```

These accounts are only for the local demo.

## Run Tests

```bash
pytest
```

The test suite checks registration, authentication, booking creation, availability validation and overlapping booking prevention.

## Booking Rules

A booking is accepted only when:

- the therapist provides the selected service;
- the appointment fits inside an available time slot;
- the appointment does not overlap a pending or confirmed booking.

New bookings start with the `pending` status. Therapists can confirm or reject them, and clients can cancel their own bookings.

## API Routes

Main routes include:

```text
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me
GET    /api/services
GET    /api/therapists
GET    /api/availability
POST   /api/availability
POST   /api/bookings
GET    /api/bookings
PATCH  /api/bookings/{booking_id}/status
GET    /api/health
```

## Notes

The code uses a simple database-backed token system so authentication stays easy to follow. Passwords are stored using PBKDF2 with a random salt.
