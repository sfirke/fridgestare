from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.user import User
from app.services.email import send_plan_email
from app.services.plans import current_planning_week_start, generate_week_plan


def run_scheduled_generation() -> None:
    session = SessionLocal()
    try:
        users = session.query(User).join(User.preferences).filter(User.is_active.is_(True)).all()
        for user in users:
            preferences = user.preferences
            if preferences is None or not preferences.email_enabled:
                continue
            week_start = current_planning_week_start(user)
            plan = generate_week_plan(
                session, user, week_start, force_regenerate=False, generation_source="scheduled"
            )
            send_plan_email(session, user, plan.id)
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
        minutes=30,
        id="fridgestare_scheduled_generation",
        replace_existing=True,
    )
    return scheduler
