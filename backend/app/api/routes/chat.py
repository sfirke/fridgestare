from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.plan import PlanOut
from app.services.chat import apply_chat_message

router = APIRouter()


@router.post("/{plan_id}/chat", response_model=ChatResponse)
def post_chat(
    plan_id: int,
    payload: ChatRequest,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    plan, explanation = apply_chat_message(session, current_user, plan_id, payload.message)
    return ChatResponse(plan=PlanOut(**plan), explanation=explanation)
