from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    lifetime = expires_minutes or settings.access_token_expire_minutes
    expires_at = datetime.now(tz=UTC) + timedelta(minutes=lifetime)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.app_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> int | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    subject = payload.get("sub")
    if subject is None:
        return None
    try:
        return int(subject)
    except (TypeError, ValueError):
        return None


def create_csrf_token() -> str:
    return token_urlsafe(32)
