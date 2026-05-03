import re
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.clients.openrouter import OpenRouterAdapter
from app.core.config import get_settings
from app.models.meal import Meal
from app.models.user import User
from app.schemas.plan import MoveSlotRequest, SetSlotRequest
from app.services.audit import create_activity_log, serialize_slot
from app.services.plans import (
    load_plan_for_user,
    move_slot_contents,
    plan_to_schema,
    reroll_slot,
    set_slot_contents,
)

WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def extract_days(message: str) -> list[str]:
    lowered = message.lower()
    return [day for day in WEEKDAY_INDEX if day in lowered]


def slot_for_day(plan, weekday_name: str):
    target_weekday = WEEKDAY_INDEX[weekday_name]
    return next((slot for slot in plan.slots if slot.slot_date.weekday() == target_weekday), None)


def find_meal_by_title(session: Session, user_id: int, phrase: str) -> Meal | None:
    cleaned = phrase.strip().lower()
    return (
        session.query(Meal)
        .filter(Meal.user_id == user_id, Meal.is_archived.is_(False), Meal.title.ilike(f"%{cleaned}%"))
        .order_by(Meal.title.asc())
        .first()
    )


def choose_meal_by_tag_or_complexity(session: Session, user_id: int, tag: str | None = None, complexity: str | None = None) -> Meal | None:
    query = session.query(Meal).filter(Meal.user_id == user_id, Meal.is_archived.is_(False))
    if complexity:
        query = query.filter(Meal.complexity == complexity)
    meals = query.order_by(Meal.title.asc()).all()
    if tag:
        lowered = tag.lower()
        meals = [meal for meal in meals if lowered in meal.title.lower() or lowered in meal.notes.lower() or any(lowered == link.tag.name for link in meal.tag_links if link.tag)]
    return meals[0] if meals else None


def parse_with_llm(plan_summary: dict, message: str) -> dict | None:
    settings = get_settings()
    adapter = OpenRouterAdapter(settings.openrouter_api_key, settings.openrouter_model)
    system_prompt = (
        "You translate meal planning chat into JSON. "
        "Return keys action, source_day, target_day, tag, complexity, meal_title."
    )
    return adapter.parse_chat_intent(system_prompt, f"Plan: {plan_summary}. Message: {message}")


def apply_chat_message(session: Session, user: User, plan_id: int, message: str) -> tuple[dict, str]:
    plan = load_plan_for_user(session, user.id, plan_id)
    lowered = message.lower().strip()
    days = extract_days(lowered)
    llm_intent = parse_with_llm(plan_to_schema(plan), message)
    if llm_intent:
        days = [llm_intent.get("source_day"), llm_intent.get("target_day")]
        days = [day for day in days if day]
        lowered = f"{llm_intent.get('action', '')} {message}".strip()

    if "swap" in lowered and len(days) >= 2:
        source = slot_for_day(plan, days[0])
        target = slot_for_day(plan, days[1])
        if source and target:
            updated = move_slot_contents(
                session,
                user,
                plan_id,
                MoveSlotRequest(source_slot_id=source.id, target_slot_id=target.id),
            )
            return plan_to_schema(updated), f"Swapped {days[0].title()} and {days[1].title()}."

    if ("move" in lowered or "swap" in lowered) and len(days) >= 2:
        source = slot_for_day(plan, days[0])
        target = slot_for_day(plan, days[1])
        if source and target:
            updated = move_slot_contents(
                session,
                user,
                plan_id,
                MoveSlotRequest(source_slot_id=source.id, target_slot_id=target.id),
            )
            return plan_to_schema(updated), f"Moved the {days[0].title()} meal onto {days[1].title()}."

    if "takeout" in lowered and days:
        slot = slot_for_day(plan, days[0])
        if slot:
            updated = set_slot_contents(
                session,
                user,
                plan_id,
                SetSlotRequest(slot_id=slot.id, slot_type="takeout"),
            )
            return plan_to_schema(updated), f"Marked {days[0].title()} as takeout."

    if ("reroll" in lowered or "replace" in lowered) and days:
        slot = slot_for_day(plan, days[0])
        if slot:
            updated = reroll_slot(session, user, plan_id, slot.id)
            return plan_to_schema(updated), f"Rerolled {days[0].title()}."

    if "simpler" in lowered and days:
        slot = slot_for_day(plan, days[0])
        meal = choose_meal_by_tag_or_complexity(session, user.id, complexity="simple")
        if slot and meal:
            updated = set_slot_contents(
                session,
                user,
                plan_id,
                SetSlotRequest(slot_id=slot.id, meal_id=meal.id, slot_type="meal"),
            )
            return plan_to_schema(updated), f"Picked a simpler meal for {days[0].title()}."

    tag_match = re.search(r"(?:a|an) ([a-z\-]+) on (monday|tuesday|wednesday|thursday|friday|saturday|sunday)", lowered)
    if tag_match:
        tag_name, day_name = tag_match.groups()
        slot = slot_for_day(plan, day_name)
        meal = choose_meal_by_tag_or_complexity(session, user.id, tag=tag_name)
        if slot and meal:
            updated = set_slot_contents(
                session,
                user,
                plan_id,
                SetSlotRequest(slot_id=slot.id, meal_id=meal.id, slot_type="meal"),
            )
            return plan_to_schema(updated), f"Put {meal.title} on {day_name.title()}."

    title_match = re.search(r"put (.+) on (monday|tuesday|wednesday|thursday|friday|saturday|sunday)", lowered)
    if title_match:
        meal_phrase, day_name = title_match.groups()
        slot = slot_for_day(plan, day_name)
        meal = find_meal_by_title(session, user.id, meal_phrase)
        if slot and meal:
            updated = set_slot_contents(
                session,
                user,
                plan_id,
                SetSlotRequest(slot_id=slot.id, meal_id=meal.id, slot_type="meal"),
            )
            return plan_to_schema(updated), f"Put {meal.title} on {day_name.title()}."

    create_activity_log(
        session,
        user.id,
        plan_id,
        event_type="chat_noop",
        payload={"message": message, "created_at": datetime.now(tz=UTC).isoformat()},
        actor_type="llm",
    )
    session.commit()
    return plan_to_schema(plan), "I couldn't translate that request into a safe plan edit."
