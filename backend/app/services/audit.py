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
    action = (
        session.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.plan_id == plan_id,
            ActivityLog.undo_payload.isnot(None),
        )
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .first()
    )
    # Rows written before undo_payload used none_as_null hold the JSON value `null`,
    # which satisfies IS NOT NULL but reads back as None.
    return action if action is not None and action.undo_payload is not None else None


def plan_email_already_sent(session: Session, user_id: int, plan_id: int) -> bool:
    """True once a plan email has been dispatched for this plan.

    The scheduler polls far more often than it should send, so this is what keeps a
    week's email to exactly one delivery.
    """
    return (
        session.query(ActivityLog.id)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.plan_id == plan_id,
            ActivityLog.event_type == "send_email",
        )
        .first()
        is not None
    )


def clear_undo_history(session: Session, user_id: int, plan_id: int) -> None:
    """Drop pending undo snapshots for a plan.

    Regenerating a week replaces every slot row, so snapshots captured against the old
    rows no longer describe anything undoable; keeping them let "undo" splice a
    pre-regeneration meal back into the new week.
    """
    (
        session.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.plan_id == plan_id,
            ActivityLog.undo_payload.isnot(None),
        )
        .update({ActivityLog.undo_payload: None}, synchronize_session=False)
    )
