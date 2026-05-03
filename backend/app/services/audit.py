from datetime import datetime

from sqlalchemy.orm import Session

from app.models.activity import ActivityLog
from app.models.plan import PlanSlot


def serialize_slot(slot: PlanSlot) -> dict:
    return {
        "id": slot.id,
        "slot_date": slot.slot_date.isoformat(),
        "slot_type": slot.slot_type,
        "meal_id": slot.meal_id,
        "discovered_candidate_id": slot.discovered_candidate_id,
        "title_snapshot": slot.title_snapshot,
        "notes_snapshot": slot.notes_snapshot,
        "selection_reason": slot.selection_reason,
        "outcome_status": slot.outcome_status,
        "outcome_logged_at": slot.outcome_logged_at.isoformat() if slot.outcome_logged_at else None,
    }


def apply_slot_snapshot(slot: PlanSlot, snapshot: dict) -> None:
    slot.slot_type = snapshot["slot_type"]
    slot.meal_id = snapshot["meal_id"]
    slot.discovered_candidate_id = snapshot["discovered_candidate_id"]
    slot.title_snapshot = snapshot["title_snapshot"]
    slot.notes_snapshot = snapshot["notes_snapshot"]
    slot.selection_reason = snapshot["selection_reason"]
    slot.outcome_status = snapshot["outcome_status"]
    slot.outcome_logged_at = (
        datetime.fromisoformat(snapshot["outcome_logged_at"])
        if snapshot["outcome_logged_at"]
        else None
    )


def create_activity_log(
    session: Session,
    user_id: int,
    plan_id: int | None,
    event_type: str,
    payload: dict,
    undo_payload: dict | None = None,
    actor_type: str = "user",
    actor_id: int | None = None,
) -> ActivityLog:
    entry = ActivityLog(
        user_id=user_id,
        plan_id=plan_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        payload=payload,
        undo_payload=undo_payload,
    )
    session.add(entry)
    session.flush()
    return entry


def get_latest_undoable_action(session: Session, user_id: int, plan_id: int) -> ActivityLog | None:
    return (
        session.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.plan_id == plan_id,
            ActivityLog.undo_payload.isnot(None),
        )
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .first()
    )
