from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginInput, LoginOutput, RegisterInput, UserOutput
from app.security import check_password, create_token, get_current_user, hash_password

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/register', response_model=LoginOutput, status_code=201)
def register(data: RegisterInput, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email.lower()).first()

    if existing_user is not None:
        raise HTTPException(status_code=409, detail='Email already registered')

    user = User(
        name=data.name.strip(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role='client'
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(db, user)
    return LoginOutput(token=token, user=user)


@router.post('/login', response_model=LoginOutput)
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()

    if user is None or not check_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Wrong email or password')

    token = create_token(db, user)
    return LoginOutput(token=token, user=user)


@router.get('/me', response_model=UserOutput)
def get_me(user: User = Depends(get_current_user)):
    return user
