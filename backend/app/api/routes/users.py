from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import build_me_response, get_current_user, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    MeResponse,
    RecurringRuleOut,
    ScheduleRulesUpdate,
    UserPreferencesOut,
    UserPreferencesUpdate,
)
from app.services.users import replace_recurring_rules, update_preferences

router = APIRouter()


@router.get("/me", response_model=MeResponse)
def get_me(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    return build_me_response(session, current_user)


@router.patch("/me/preferences", response_model=UserPreferencesOut)
def patch_preferences(
    payload: UserPreferencesUpdate,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreferencesOut:
    return update_preferences(session, current_user, payload)


@router.patch("/me/schedule-rules", response_model=list[RecurringRuleOut])
def patch_schedule_rules(
    payload: ScheduleRulesUpdate,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RecurringRuleOut]:
    return replace_recurring_rules(session, current_user, payload.rules)
