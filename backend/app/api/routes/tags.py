from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.meal import TagSuggestionOut
from app.services.meals import get_tag_suggestions

router = APIRouter()


@router.get("/suggestions", response_model=list[TagSuggestionOut])
def get_suggestions(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TagSuggestionOut]:
    return [TagSuggestionOut(name=name) for name in get_tag_suggestions(session, current_user.id)]
