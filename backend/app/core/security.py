from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from app.core.config import get_settings

# argon2-cffi directly rather than passlib: passlib is unmaintained and imports the
# stdlib `crypt` module, which Python 3.13 removed. The hash format is identical, so
# credentials written by the previous passlib-backed build still verify.
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (Argon2Error, ValueError):
        # Wrong password, or a malformed/unknown hash: both are simply "not verified".
        return False


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
