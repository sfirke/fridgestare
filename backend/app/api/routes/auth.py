from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import build_me_response, get_current_user, require_csrf
from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.core.security import create_access_token, create_csrf_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth import authenticate_user

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_db),
) -> LoginResponse:
    enforce_rate_limit(request, bucket="login", limit=8, window_seconds=60, identifier=payload.email.lower())
    settings = get_settings()
    user = authenticate_user(session, payload.email, payload.password)
    access_token = create_access_token(user.id)
    csrf_token = create_csrf_token()
    response.set_cookie(
        key=settings.access_cookie_name,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return LoginResponse(me=build_me_response(session, user))


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    response: Response,
    _: None = Depends(require_csrf),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    settings = get_settings()
    response.delete_cookie(settings.access_cookie_name)
    response.delete_cookie(settings.csrf_cookie_name)
    return {"status": f"logged out {current_user.email}"}


@router.get("/me", response_model=LoginResponse)
def auth_me(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LoginResponse:
    return LoginResponse(me=build_me_response(session, current_user))
