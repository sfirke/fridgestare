from datetime import UTC, datetime, time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.timezones import is_valid_timezone
from app.models.user import RecurringRule, User, UserPreferences
from app.schemas.user import RecurringRuleIn, UserPreferencesUpdate


def validate_timezone_name(timezone: str) -> str:
    candidate = timezone.strip()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Timezone is required")
    if not is_valid_timezone(candidate):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timezone")
    return candidate


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.query(User).filter(User.email == email.strip().lower()).one_or_none()


def ensure_preferences(session: Session, user: User) -> UserPreferences:
    preferences = user.preferences
    if preferences is None:
        preferences = UserPreferences(user_id=user.id, updated_at=datetime.now(tz=UTC))
        session.add(preferences)
        session.flush()
        session.refresh(preferences)
    return preferences


def create_user(
    session: Session,
    email: str,
    password: str,
    is_admin: bool = False,
    timezone: str = "UTC",
    week_starts_on: int = 0,
) -> User:
    existing = get_user_by_email(session, email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    user = User(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        is_admin=is_admin,
        timezone=validate_timezone_name(timezone),
        week_starts_on=week_starts_on,
    )
    session.add(user)
    session.flush()
    session.add(
        UserPreferences(
            user_id=user.id,
            takeout_frequency_per_week=1.0,
            leftovers_per_week=0,
            allow_simple=True,
            allow_intermediate=True,
            allow_complex=True,
            planning_guidance_text="",
            dietary_notes="",
            email_enabled=False,
            email_day_of_week=6,
            email_local_time=time(hour=9),
            updated_at=datetime.now(tz=UTC),
        )
    )
    session.commit()
    session.refresh(user)
    return user


def update_preferences(
    session: Session, user: User, payload: UserPreferencesUpdate
) -> UserPreferences:
    preferences = ensure_preferences(session, user)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        if field_name == "timezone":
            user.timezone = validate_timezone_name(str(value))
            continue
        if field_name == "week_starts_on":
            user.week_starts_on = int(value)
            continue
        setattr(preferences, field_name, value)
    session.add(user)
    session.add(preferences)
    session.commit()
    session.refresh(preferences)
    return preferences


def replace_recurring_rules(
    session: Session,
    user: User,
    rules: list[RecurringRuleIn],
) -> list[RecurringRule]:
    session.query(RecurringRule).filter(RecurringRule.user_id == user.id).delete()
    new_rules = [
        RecurringRule(
            user_id=user.id,
            day_of_week=rule.day_of_week,
            rule_type=rule.rule_type,
            rule_payload=rule.rule_payload,
            priority=rule.priority,
            active=rule.active,
        )
        for rule in rules
    ]
    session.add_all(new_rules)
    session.commit()
    return (
        session.query(RecurringRule)
        .filter(RecurringRule.user_id == user.id)
        .order_by(RecurringRule.day_of_week, RecurringRule.priority)
        .all()
    )


def set_user_password(session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session, email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_users(session: Session) -> list[User]:
    return session.query(User).order_by(User.email).all()
