from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.meal import BulkFastAddRequest, MealCreate, MealOut, MealUpdate
from app.services.meals import (
    archive_meal,
    bulk_fast_add,
    create_meal,
    export_meals_csv,
    list_meals,
    load_meal_for_user,
    meal_to_schema,
    update_meal,
)

router = APIRouter()


@router.get("", response_model=list[MealOut])
def get_meals(
    include_archived: bool = False,
    complexity: str | None = None,
    recurrence_tier: str | None = None,
    tag: str | None = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MealOut]:
    return [
        meal_to_schema(meal)
        for meal in list_meals(
            session,
            current_user.id,
            include_archived=include_archived,
            complexity=complexity,
            recurrence_tier=recurrence_tier,
            tag=tag,
        )
    ]


@router.post("", response_model=MealOut, status_code=status.HTTP_201_CREATED)
def post_meal(
    payload: MealCreate,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealOut:
    meal = create_meal(session, current_user.id, payload)
    return meal_to_schema(meal)


@router.post("/bulk-fast-add", response_model=list[MealOut], status_code=status.HTTP_201_CREATED)
def post_bulk_fast_add(
    payload: BulkFastAddRequest,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MealOut]:
    meals = bulk_fast_add(session, current_user.id, payload.meals)
    return [meal_to_schema(meal) for meal in meals]


@router.get("/export.csv")
def get_export_csv(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    csv_text = export_meals_csv(session, current_user.id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="fridgestare-meals.csv"'},
    )


@router.get("/{meal_id}", response_model=MealOut)
def get_meal(
    meal_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealOut:
    return meal_to_schema(load_meal_for_user(session, current_user.id, meal_id))


@router.patch("/{meal_id}", response_model=MealOut)
def patch_meal(
    meal_id: int,
    payload: MealUpdate,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MealOut:
    meal = update_meal(session, current_user.id, meal_id, payload)
    return meal_to_schema(meal)


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: int,
    _: None = Depends(require_csrf),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    archive_meal(session, current_user.id, meal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
