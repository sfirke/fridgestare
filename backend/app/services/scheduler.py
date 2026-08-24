import logging
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.timezones import resolve_timezone
from app.db.session import SessionLocal
from app.models.user import User, UserPreferences
from app.services.audit import plan_email_already_sent
from app.services.email import send_plan_email
from app.services.plans import current_planning_week_start, generate_week_plan

logger = logging.getLogger("app.services.scheduler")

CHECK_INTERVAL_MINUTES = 30


def local_now(timezone_name: str, now: datetime | None = None) -> datetime:
    """Return the current moment in the user's timezone, falling back to UTC."""
    return (now or datetime.now(tz=UTC)).astimezone(resolve_timezone(timezone_name))


def email_window_is_open(preferences: UserPreferences, moment: datetime) -> bool:
    """True once the user's chosen weekday and send time have arrived locally.

    The "already sent" check is what stops this from re-firing on every tick for the
    rest of the day; this only decides whether the week's send is due yet.
    """
    if moment.weekday() != preferences.email_day_of_week:
        return False
    return moment.timetz().replace(tzinfo=None) >= preferences.email_local_time


def deliver_scheduled_email(session: Session, user: User) -> bool:
    """Generate the planning week if needed and email it once. True if sent."""
    preferences = user.preferences
    if preferences is None or not preferences.email_enabled:
        return False
    if not email_window_is_open(preferences, local_now(user.timezone)):
        return False

    week_start = current_planning_week_start(user)
    plan = generate_week_plan(
        session, user, week_start, force_regenerate=False, generation_source="scheduled"
    )
    if plan_email_already_sent(session, user.id, plan.id):
        return False

    send_plan_email(session, user, plan.id, actor_type="scheduler")
    return True


def run_scheduled_generation() -> None:
    session = SessionLocal()
    try:
        users = session.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            try:
                if deliver_scheduled_email(session, user):
                    logger.info("Sent the scheduled weekly plan email to user_id=%s.", user.id)
            except Exception:  # pylint: disable=broad-exception-caught
                # One user's failure must not stop the rest of the run.
                session.rollback()
                logger.exception("Scheduled plan delivery failed for user_id=%s.", user.id)
    finally:
        session.close()


def initialize_scheduler() -> BackgroundScheduler | None:
    settings = get_settings()
    if not settings.scheduler_enabled:
        return None
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_scheduled_generation,
        trigger="interval",
        minutes=CHECK_INTERVAL_MINUTES,
        id="fridgestare_scheduled_generation",
        replace_existing=True,
        # The scheduler lives in the API process, so it must never stack runs: two
        # overlapping ticks would both see an unsent plan and both send it. Ticks
        # missed while the process was down are dropped rather than replayed.
        max_instances=1,
        coalesce=True,
        misfire_grace_time=CHECK_INTERVAL_MINUTES * 60,
    )
    logger.info(
        "Scheduler enabled; checking every %s minutes for plans due to send.",
        CHECK_INTERVAL_MINUTES,
    )
    return scheduler
