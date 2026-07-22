from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine
from app.routers import auth, availability, bookings, services
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title='Appointment Booking Platform',
    version='1.0.0',
    description='API for therapist availability and appointment booking.',
    lifespan=lifespan
)

app.include_router(auth.router)
app.include_router(services.router)
app.include_router(availability.router)
app.include_router(bookings.router)

static_dir = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=static_dir), name='static')


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/')
def home():
    return FileResponse(static_dir / 'index.html')
