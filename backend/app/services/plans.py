from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.meal import Meal, MealTagLink
from app.models.plan import PlanSlot, WeeklyPlan
from app.models.user import User
from app.schemas.plan import MoveSlotRequest, SetSlotRequest
from app.services.audit import (
    apply_slot_snapshot,
    clear_undo_history,
    create_activity_log,
    get_latest_undoable_action,
    serialize_slot,
)
from app.services.meals import load_meal_for_user
from app.services.planner import (
    compute_planning_week_start,
    current_local_date,
    generate_plan_payload,
    generate_slot_selection,
    load_history,
)


def plan_summary_to_schema(plan: WeeklyPlan) -> dict:
    return {
        "id": plan.id,
        "week_start_date": plan.week_start_date,
        "status": plan.status,
        "generation_source": plan.generation_source,
    }


def plan_to_schema(plan: WeeklyPlan) -> dict:
    return {
        "id": plan.id,
        "week_start_date": plan.week_start_date,
        "status": plan.status,
        "generation_source": plan.generation_source,
        "planner_explanation": plan.planner_explanation,
        "slots": [
            {
                "id": slot.id,
                "slot_date": slot.slot_date,
                "slot_order": slot.slot_order,
                "slot_type": slot.slot_type,
                "meal_id": slot.meal_id,
                "discovered_candidate_id": slot.discovered_candidate_id,
                "title_snapshot": slot.title_snapshot,
                "notes_snapshot": slot.notes_snapshot,
                "selection_reason": slot.selection_reason,
                "outcome_status": slot.outcome_status,
                "outcome_logged_at": slot.outcome_logged_at,
            }
            for slot in sorted(plan.slots, key=lambda item: item.slot_order)
        ],
    }


def load_plan_for_user(session: Session, user_id: int, plan_id: int) -> WeeklyPlan:
    plan = (
        session.query(WeeklyPlan)
        .options(joinedload(WeeklyPlan.slots))
        .filter(WeeklyPlan.user_id == user_id, WeeklyPlan.id == plan_id)
        .one_or_none()
    )
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


def load_plan_by_week(session: Session, user_id: int, week_start_date: date) -> WeeklyPlan | None:
    return (
        session.query(WeeklyPlan)
        .options(joinedload(WeeklyPlan.slots))
        .filter(WeeklyPlan.user_id == user_id, WeeklyPlan.week_start_date == week_start_date)
        .one_or_none()
    )


def list_plan_summaries(session: Session, user_id: int) -> list[dict]:
    plans = (
        session.query(WeeklyPlan)
        .filter(WeeklyPlan.user_id == user_id)
        .order_by(WeeklyPlan.week_start_date.desc())
        .all()
    )
    return [plan_summary_to_schema(plan) for plan in plans]


def current_planning_week_start(user: User) -> date:
    return compute_planning_week_start(current_local_date(user.timezone), user.week_starts_on)


def current_week_plan(session: Session, user: User) -> WeeklyPlan | None:
    week_start = current_planning_week_start(user)
    return load_plan_by_week(session, user.id, week_start)


def generate_week_plan(
    session: Session,
    user: User,
    week_start_date: date,
    force_regenerate: bool = False,
    generation_source: str = "manual",
) -> WeeklyPlan:
    existing = load_plan_by_week(session, user.id, week_start_date)
    if existing is not None and not force_regenerate:
        return existing

    slot_payloads, explanation = generate_plan_payload(session, user, week_start_date)
    if existing is None:
        plan = WeeklyPlan(
            user_id=user.id,
            week_start_date=week_start_date,
            generation_source=generation_source,
            planner_explanation=explanation,
        )
        session.add(plan)
        session.flush()
    else:
        plan = existing
        plan.slots.clear()
        session.flush()
        clear_undo_history(session, user.id, plan.id)
        plan.generation_source = generation_source
        plan.planner_explanation = explanation
    for payload in slot_payloads:
        plan.slots.append(PlanSlot(**payload))
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return load_plan_for_user(session, user.id, plan.id)


def reroll_slot(session: Session, user: User, plan_id: int, slot_id: int) -> WeeklyPlan:
    plan = load_plan_for_user(session, user.id, plan_id)
    slot = next((item for item in plan.slots if item.id == slot_id), None)
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    original = serialize_slot(slot)
    preferences = user.preferences
    if preferences is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Preferences are required"
        )
    meals = (
        session.query(Meal)
        .options(
            joinedload(Meal.tag_links).joinedload(MealTagLink.tag),
            joinedload(Meal.seasonal_recurrence_overrides),
        )
        .filter(Meal.user_id == user.id, Meal.is_archived.is_(False))
        .all()
    )
    history = load_history(session, user.id, plan.week_start_date)
    selected_meal_ids = {
        item.meal_id for item in plan.slots if item.id != slot.id and item.meal_id is not None
    }
    if slot.meal_id is not None:
        selected_meal_ids.add(slot.meal_id)
    slot_payload, note = generate_slot_selection(
        meals,
        preferences,
        user.recurring_rules,
        history,
        slot.slot_date,
        selected_meal_ids,
    )
    slot.slot_type = slot_payload["slot_type"]
    slot.meal_id = slot_payload["meal_id"]
    slot.discovered_candidate_id = slot_payload["discovered_candidate_id"]
    slot.title_snapshot = slot_payload["title_snapshot"]
    slot.notes_snapshot = slot_payload["notes_snapshot"]
    slot.selection_reason = slot_payload["selection_reason"]
    plan.generation_source = "reroll"
    if note:
        plan.planner_explanation = f"{plan.planner_explanation}\n- {note}"
    create_activity_log(
        session,
        user_id=user.id,
        plan_id=plan.id,
        event_type="reroll_slot",
        payload={"slot_id": slot.id},
        undo_payload={"slots": [original]},
    )
    session.commit()
    return load_plan_for_user(session, user.id, plan.id)


def move_slot_contents(
    session: Session, user: User, plan_id: int, payload: MoveSlotRequest
) -> WeeklyPlan:
    plan = load_plan_for_user(session, user.id, plan_id)
    source = next((slot for slot in plan.slots if slot.id == payload.source_slot_id), None)
    target = next((slot for slot in plan.slots if slot.id == payload.target_slot_id), None)
    if source is None or target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    undo_payload = {"slots": [serialize_slot(source), serialize_slot(target)]}
    fields = [
        "slot_type",
        "meal_id",
        "discovered_candidate_id",
        "title_snapshot",
        "notes_snapshot",
        "selection_reason",
        "outcome_status",
        "outcome_logged_at",
    ]
    source_values = {field: getattr(source, field) for field in fields}
    target_values = {field: getattr(target, field) for field in fields}
    for field, value in source_values.items():
        setattr(target, field, value)
    for field, value in target_values.items():
        setattr(source, field, value)
    create_activity_log(
        session,
        user.id,
        plan.id,
        event_type="move_slot",
        payload=payload.model_dump(),
        undo_payload=undo_payload,
    )
    session.commit()
    return load_plan_for_user(session, user.id, plan.id)


def set_slot_contents(
    session: Session, user: User, plan_id: int, payload: SetSlotRequest
) -> WeeklyPlan:
    plan = load_plan_for_user(session, user.id, plan_id)
    slot = next((item for item in plan.slots if item.id == payload.slot_id), None)
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    undo_payload = {"slots": [serialize_slot(slot)]}
    slot.slot_type = payload.slot_type
    slot.discovered_candidate_id = payload.discovered_candidate_id
    slot.meal_id = payload.meal_id
    if payload.slot_type == "meal" and payload.meal_id is not None:
        meal = load_meal_for_user(session, user.id, payload.meal_id)
        slot.discovered_candidate_id = None
        slot.title_snapshot = meal.title
        slot.notes_snapshot = meal.notes
        slot.selection_reason = "Manually selected by the user."
    elif payload.slot_type == "leftover":
        if payload.meal_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Leftovers require a meal"
            )
        meal = load_meal_for_user(session, user.id, payload.meal_id)
        slot.discovered_candidate_id = None
        slot.title_snapshot = meal.title
        slot.notes_snapshot = meal.notes
        slot.selection_reason = "Marked as leftovers by the user."
    elif payload.slot_type == "takeout":
        slot.meal_id = None
        slot.discovered_candidate_id = None
        slot.title_snapshot = payload.title_snapshot or "Takeout Night"
        slot.notes_snapshot = payload.notes_snapshot or ""
        slot.selection_reason = "Marked as takeout by the user."
    else:
        slot.meal_id = None
        slot.discovered_candidate_id = None
        slot.title_snapshot = payload.title_snapshot or "Unplanned"
        slot.notes_snapshot = payload.notes_snapshot or ""
        slot.selection_reason = "Cleared by the user."
    create_activity_log(
        session,
        user.id,
        plan.id,
        event_type="set_slot",
        payload=payload.model_dump(),
        undo_payload=undo_payload,
    )
    session.commit()
    return load_plan_for_user(session, user.id, plan.id)


def update_outcome_status(
    session: Session, user: User, plan_id: int, slot_id: int, outcome_status: str | None
) -> WeeklyPlan:
    plan = load_plan_for_user(session, user.id, plan_id)
    slot = next((item for item in plan.slots if item.id == slot_id), None)
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    undo_payload = {"slots": [serialize_slot(slot)]}
    slot.outcome_status = outcome_status
    slot.outcome_logged_at = datetime.now(tz=UTC) if outcome_status else None
    create_activity_log(
        session,
        user.id,
        plan.id,
        event_type="outcome_status",
        payload={"slot_id": slot_id, "outcome_status": outcome_status},
        undo_payload=undo_payload,
    )
    session.commit()
    return load_plan_for_user(session, user.id, plan.id)


def undo_last_action(session: Session, user: User, plan_id: int) -> WeeklyPlan:
    plan = load_plan_for_user(session, user.id, plan_id)
    action = get_latest_undoable_action(session, user.id, plan_id)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No undoable action available"
        )
    slot_map = {slot.id: slot for slot in plan.slots}
    for snapshot in action.undo_payload.get("slots", []):
        slot = slot_map.get(snapshot["id"])
        if slot is not None:
            apply_slot_snapshot(slot, snapshot)
    action.undo_payload = None
    create_activity_log(
        session,
        user.id,
        plan.id,
        event_type="undo",
        payload={"undid_activity_id": action.id},
        undo_payload=None,
    )
    session.commit()
    return load_plan_for_user(session, user.id, plan.id)
