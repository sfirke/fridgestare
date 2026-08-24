import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.clients.mailgun import MailgunAdapter
from app.core.config import get_settings
from app.models.user import User
from app.services.audit import create_activity_log
from app.services.plans import load_plan_for_user

logger = logging.getLogger("app.services.email")

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["html", "xml"])
)


def render_plan_email(user: User, plan) -> tuple[str, str]:
    settings = get_settings()
    # AnyHttpUrl normalizes a bare host to a trailing slash, so strip it before joining.
    base_url = str(settings.app_base_url).rstrip("/")
    link = f"{base_url}/plans/{plan.week_start_date}"
    subject = f"Your Fridgestare plan for {plan.week_start_date.isoformat()}"
    html = TEMPLATE_ENV.get_template("plan_email.html").render(user=user, plan=plan, link=link)
    return subject, html


def send_plan_email(
    session: Session, user: User, plan_id: int, actor_type: str = "user"
) -> tuple[str, str]:
    """Send a plan email and record it.

    Raises MailgunDeliveryError when Mailgun is configured but the send fails. Nothing
    is written to the activity log in that case, so the plan is not treated as sent and
    the next scheduler tick tries again.
    """
    settings = get_settings()
    plan = load_plan_for_user(session, user.id, plan_id)
    subject, html = render_plan_email(user, plan)
    adapter = MailgunAdapter(
        settings.mailgun_api_key, settings.mailgun_domain, settings.mailgun_base_url
    )
    result = adapter.send(settings.mail_from_address, user.email, subject, html)
    delivery_mode = "mailgun" if result.delivered else "mock"
    if result.delivered:
        plan.status = "scheduled_sent"
        session.add(plan)
    else:
        logger.warning(
            "Mailgun is not configured; plan_id=%s for user_id=%s was rendered but not sent.",
            plan_id,
            user.id,
        )
    create_activity_log(
        session,
        user.id,
        plan_id,
        event_type="send_email",
        payload={"subject": subject, "delivery_mode": delivery_mode},
        actor_type=actor_type,
    )
    session.commit()
    return delivery_mode, html


def preview_plan_email(session: Session, user: User, plan_id: int) -> tuple[str, str, str]:
    plan = load_plan_for_user(session, user.id, plan_id)
    subject, html = render_plan_email(user, plan)
    return subject, html, "preview"
