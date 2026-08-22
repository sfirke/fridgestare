from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.email import EmailPreviewOut, SendEmailResponse
from app.schemas.plan import (
    GeneratePlanRequest,
    MoveSlotRequest,
    OutcomeStatusUpdate,
    PlanOut,
    PlanSummaryOut,
    RerollSlotRequest,
    SetSlotRequest,
)
from app.services.email import preview_plan_email, send_plan_email
from app.services.plans import (
    current_planning_week_start,
    current_week_plan,
    generate_week_plan,
    list_plan_summaries,
    load_plan_by_week,
    move_slot_contents,
    plan_to_schema,
    reroll_slot,
    set_slot_contents,
    undo_last_action,
    update_outcome_status,
)

router = APIRouter()


@router.get("", response_model=list[PlanSummaryOut])
def get_plan_history(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlanSummaryOut]:
    return [PlanSummaryOut(**plan) for plan in list_plan_summaries(session, current_user.id)]


@router.get("/current", response_model=PlanOut)
def get_current_plan(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    plan = current_week_plan(session, current_user)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No plan for the active planning week"
        )
    return PlanOut(**plan_to_schema(plan))


@router.get("/week/{week_start}", response_model=PlanOut)
def get_week_plan(
    week_start: date,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    plan = load_plan_by_week(session, current_user.id, week_start)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return PlanOut(**plan_to_schema(plan))


@router.post("/generate", response_model=PlanOut)
def post_generate_plan(
    payload: GeneratePlanRequest,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    week_start = payload.week_start_date or current_planning_week_start(current_user)
    plan = generate_week_plan(
        session,
        current_user,
        week_start_date=week_start,
        force_regenerate=payload.force_regenerate,
    )
    return PlanOut(**plan_to_schema(plan))


@router.post("/{plan_id}/reroll-slot", response_model=PlanOut)
def post_reroll_slot(
    plan_id: int,
    payload: RerollSlotRequest,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    return PlanOut(**plan_to_schema(reroll_slot(session, current_user, plan_id, payload.slot_id)))


@router.post("/{plan_id}/move-slot", response_model=PlanOut)
def post_move_slot(
    plan_id: int,
    payload: MoveSlotRequest,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    return PlanOut(**plan_to_schema(move_slot_contents(session, current_user, plan_id, payload)))


@router.post("/{plan_id}/set-slot", response_model=PlanOut)
def post_set_slot(
    plan_id: int,
    payload: SetSlotRequest,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    return PlanOut(**plan_to_schema(set_slot_contents(session, current_user, plan_id, payload)))


@router.post("/{plan_id}/undo", response_model=PlanOut)
def post_undo(
    plan_id: int,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    return PlanOut(**plan_to_schema(undo_last_action(session, current_user, plan_id)))


@router.post("/{plan_id}/slots/{slot_id}/outcome-status", response_model=PlanOut)
def post_outcome_status(
    plan_id: int,
    slot_id: int,
    payload: OutcomeStatusUpdate,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    return PlanOut(
        **plan_to_schema(
            update_outcome_status(session, current_user, plan_id, slot_id, payload.outcome_status)
        )
    )


@router.post("/{plan_id}/send-email", response_model=SendEmailResponse)
def post_send_email(
    plan_id: int,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SendEmailResponse:
    delivery_mode, _ = send_plan_email(session, current_user, plan_id)
    return SendEmailResponse(status="queued", delivery_mode=delivery_mode)


@router.get("/{plan_id}/email-preview", response_model=EmailPreviewOut)
def get_email_preview(
    plan_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmailPreviewOut:
    subject, html, delivery_mode = preview_plan_email(session, current_user, plan_id)
    return EmailPreviewOut(subject=subject, html=html, delivery_mode=delivery_mode)
