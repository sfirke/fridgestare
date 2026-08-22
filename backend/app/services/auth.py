from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, hash_password, verify_password
from app.models.user import User

# Verified against a throwaway hash when the email is unknown, so a miss costs the same
# time as a wrong password and cannot be used to enumerate accounts.
_DUMMY_PASSWORD_HASH = hash_password("fridgestare-timing-equalizer")


def authenticate_user(session: Session, email: str, password: str) -> User:
    user = session.query(User).filter(User.email == email.strip().lower()).one_or_none()
    if user is None:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user


def get_user_id_from_token(token: str | None) -> int | None:
    if not token:
        return None
    return decode_access_token(token)
