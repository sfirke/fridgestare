from datetime import UTC, datetime, time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import RecurringRule, User, UserPreferences
from app.schemas.user import RecurringRuleIn, UserPreferencesUpdate
from app.services.auth import create_user_password_hash


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.query(User).filter(User.email.ilike(email.strip())).one_or_none()


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
        password_hash=create_user_password_hash(password),
        is_admin=is_admin,
        timezone=timezone,
        week_starts_on=week_starts_on,
    )
    session.add(user)
    session.flush()
    session.add(
        UserPreferences(
            user_id=user.id,
            novel_meal_ratio=0.15,
            takeout_frequency_per_week=1.0,
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


def update_preferences(session: Session, user: User, payload: UserPreferencesUpdate) -> UserPreferences:
    preferences = ensure_preferences(session, user)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(preferences, field_name, value)
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
    return session.query(RecurringRule).filter(RecurringRule.user_id == user.id).order_by(RecurringRule.day_of_week, RecurringRule.priority).all()
