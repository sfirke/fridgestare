from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.clients.mailgun import MailgunAdapter
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.user import User
from app.services.audit import create_activity_log
from app.services.plans import load_plan_for_user

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["html", "xml"])
)


def render_plan_email(user: User, plan) -> tuple[str, str]:
    settings = get_settings()
    token = create_access_token(user.id, expires_minutes=60 * 24 * 7)
    link = f"{settings.app_base_url}/plans/{plan.week_start_date}?token={token}"
    subject = f"Your Fridgestare plan for {plan.week_start_date.isoformat()}"
    html = env.get_template("plan_email.html").render(user=user, plan=plan, link=link)
    return subject, html


def send_plan_email(session: Session, user: User, plan_id: int) -> tuple[str, str]:
    settings = get_settings()
    plan = load_plan_for_user(session, user.id, plan_id)
    subject, html = render_plan_email(user, plan)
    adapter = MailgunAdapter(settings.mailgun_api_key, settings.mailgun_domain)
    sent = adapter.send(settings.mail_from_address, user.email, subject, html)
    delivery_mode = "mailgun" if sent else "mock"
    if sent:
        plan.status = "scheduled_sent"
        session.add(plan)
    create_activity_log(
        session,
        user.id,
        plan_id,
        event_type="send_email",
        payload={"subject": subject, "delivery_mode": delivery_mode},
        actor_type="scheduler" if delivery_mode == "mailgun" else "user",
    )
    session.commit()
    return delivery_mode, html


def preview_plan_email(session: Session, user: User, plan_id: int) -> tuple[str, str, str]:
    plan = load_plan_for_user(session, user.id, plan_id)
    subject, html = render_plan_email(user, plan)
    return subject, html, "preview"
