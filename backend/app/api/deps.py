from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import MeResponse, UserOut
from app.services.auth import get_user_id_from_token
from app.services.users import ensure_preferences


def get_current_user(
    request: Request,
    session: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.access_cookie_name)
    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_csrf(request: Request) -> None:
    settings = get_settings()
    cookie_value = request.cookies.get(settings.csrf_cookie_name)
    header_value = request.headers.get(settings.csrf_header_name)
    if not cookie_value or cookie_value != header_value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def build_me_response(session: Session, user: User) -> MeResponse:
    preferences = ensure_preferences(session, user)
    rules = sorted(user.recurring_rules, key=lambda item: (item.day_of_week, item.priority))
    return MeResponse(
        user=UserOut.model_validate(user),
        preferences=preferences,
        recurring_rules=rules,
    )
