from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.discovery import DiscoveryAcceptRequest, DiscoveryCandidateOut, DiscoverySuggestRequest
from app.schemas.meal import MealOut
from app.services.discovery import accept_candidate, candidate_to_schema, suggest_candidates
from app.services.meals import meal_to_schema

router = APIRouter()


@router.post("/suggest", response_model=list[DiscoveryCandidateOut])
def post_suggest(
    payload: DiscoverySuggestRequest,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DiscoveryCandidateOut]:
    candidates = suggest_candidates(session, current_user, payload.query)
    return [DiscoveryCandidateOut(**candidate_to_schema(candidate)) for candidate in candidates]


@router.post("/{candidate_id}/accept")
def post_accept_candidate(
    candidate_id: int,
    payload: DiscoveryAcceptRequest,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    candidate, meal = accept_candidate(
        session,
        current_user,
        candidate_id,
        plan_id=payload.plan_id,
        slot_id=payload.slot_id,
        apply_to_plan=payload.apply_to_plan,
    )
    return {
        "candidate": DiscoveryCandidateOut(**candidate_to_schema(candidate)).model_dump(),
        "meal": meal_to_schema(meal).model_dump() if meal is not None else None,
    }
