from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, hash_password, verify_password
from app.models.user import User


def authenticate_user(session: Session, email: str, password: str) -> User:
    user = session.query(User).filter(User.email == email.strip().lower()).one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user


def create_user_password_hash(password: str) -> str:
    return hash_password(password)


def get_user_id_from_token(token: str | None) -> int | None:
    if not token:
        return None
    return decode_access_token(token)
