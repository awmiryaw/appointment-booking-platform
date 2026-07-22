import hashlib
import hmac
import os
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserSession


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 120000)
    return f'{salt.hex()}:{password_hash.hex()}'


def check_password(password: str, saved_password: str) -> bool:
    try:
        salt_hex, hash_hex = saved_password.split(':', 1)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False

    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 120000)
    return hmac.compare_digest(password_hash.hex(), hash_hex)


def create_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(UserSession(token=token, user_id=user.id))
    db.commit()
    return token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
) -> User:
    if authorization is None or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Authentication required')

    token = authorization[7:]
    session = db.query(UserSession).filter(UserSession.token == token).first()

    if session is None or not session.user.is_active:
        raise HTTPException(status_code=401, detail='Invalid token')

    return session.user


def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail='Permission denied')
        return user

    return checker
