import csv
from io import StringIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.meal import Meal, MealTag, MealTagLink
from app.schemas.meal import MealCreate, MealOut, MealTagOut, MealUpdate

STARTER_TAGS = [
    "soup",
    "tacos",
    "quick",
    "cozy",
    "company",
    "takeout-inspired",
]


def normalize_tag_name(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def load_meal_for_user(session: Session, user_id: int, meal_id: int) -> Meal:
    meal = (
        session.query(Meal)
        .options(joinedload(Meal.tag_links).joinedload(MealTagLink.tag))
        .filter(Meal.user_id == user_id, Meal.id == meal_id)
        .one_or_none()
    )
    if meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    return meal


def ensure_tags(session: Session, user_id: int, tag_names: list[str]) -> list[MealTag]:
    normalized = [normalize_tag_name(name) for name in tag_names if normalize_tag_name(name)]
    if not normalized:
        return []
    existing_tags = (
        session.query(MealTag)
        .filter(MealTag.user_id == user_id, MealTag.name.in_(normalized))
        .all()
    )
    existing_map = {tag.name: tag for tag in existing_tags}
    created_tags: list[MealTag] = []
    for tag_name in normalized:
        if tag_name not in existing_map:
            tag = MealTag(user_id=user_id, name=tag_name)
            session.add(tag)
            session.flush()
            existing_map[tag_name] = tag
            created_tags.append(tag)
    return [existing_map[name] for name in dict.fromkeys(normalized)]


def replace_meal_tags(session: Session, meal: Meal, tag_names: list[str]) -> None:
    meal.tag_links.clear()
    for tag in ensure_tags(session, meal.user_id, tag_names):
        meal.tag_links.append(MealTagLink(tag_id=tag.id, meal_id=meal.id, tag=tag))


def meal_to_schema(meal: Meal) -> MealOut:
    tags = [MealTagOut(id=link.tag.id, name=link.tag.name) for link in meal.tag_links if link.tag is not None]
    return MealOut(
        id=meal.id,
        title=meal.title,
        notes=meal.notes,
        meal_type=meal.meal_type,
        complexity=meal.complexity,
        recurrence_tier=meal.recurrence_tier,
        seasonality_mode=meal.seasonality_mode,
        dietary_exclusions=meal.dietary_exclusions,
        source_note=meal.source_note,
        source_url=meal.source_url,
        agent_sourced=meal.agent_sourced,
        is_archived=meal.is_archived,
        tags=tags,
        created_at=meal.created_at,
        updated_at=meal.updated_at,
    )


def create_meal(session: Session, user_id: int, payload: MealCreate, agent_sourced: bool = False) -> Meal:
    meal = Meal(
        user_id=user_id,
        title=payload.title.strip(),
        notes=payload.notes,
        complexity=payload.complexity,
        recurrence_tier=payload.recurrence_tier,
        seasonality_mode=payload.seasonality_mode,
        dietary_exclusions=payload.dietary_exclusions,
        source_note=payload.source_note,
        source_url=payload.source_url,
        agent_sourced=agent_sourced,
    )
    session.add(meal)
    session.flush()
    replace_meal_tags(session, meal, payload.tags)
    session.commit()
    return load_meal_for_user(session, user_id, meal.id)


def bulk_fast_add(session: Session, user_id: int, payloads: list[MealCreate]) -> list[Meal]:
    meals = []
    for payload in payloads:
        meal = Meal(
            user_id=user_id,
            title=payload.title.strip(),
            notes=payload.notes,
            complexity=payload.complexity,
            recurrence_tier=payload.recurrence_tier,
            seasonality_mode=payload.seasonality_mode,
            dietary_exclusions=payload.dietary_exclusions,
            source_note=payload.source_note,
            source_url=payload.source_url,
        )
        session.add(meal)
        session.flush()
        replace_meal_tags(session, meal, payload.tags)
        meals.append(meal)
    session.commit()
    return [load_meal_for_user(session, user_id, meal.id) for meal in meals]


def list_meals(
    session: Session,
    user_id: int,
    include_archived: bool = False,
    complexity: str | None = None,
    recurrence_tier: str | None = None,
    tag: str | None = None,
) -> list[Meal]:
    query = session.query(Meal).options(joinedload(Meal.tag_links).joinedload(MealTagLink.tag)).filter(Meal.user_id == user_id)
    if not include_archived:
        query = query.filter(Meal.is_archived.is_(False))
    if complexity:
        query = query.filter(Meal.complexity == complexity)
    if recurrence_tier:
        query = query.filter(Meal.recurrence_tier == recurrence_tier)
    meals = query.order_by(Meal.title.asc()).all()
    if tag:
        normalized_tag = normalize_tag_name(tag)
        meals = [meal for meal in meals if normalized_tag in {link.tag.name for link in meal.tag_links if link.tag}]
    return meals


def update_meal(session: Session, user_id: int, meal_id: int, payload: MealUpdate) -> Meal:
    meal = load_meal_for_user(session, user_id, meal_id)
    updates = payload.model_dump(exclude_unset=True)
    tags = updates.pop("tags", None)
    for field_name, value in updates.items():
        setattr(meal, field_name, value)
    if tags is not None:
        replace_meal_tags(session, meal, tags)
    session.add(meal)
    session.commit()
    return load_meal_for_user(session, user_id, meal.id)


def archive_meal(session: Session, user_id: int, meal_id: int) -> None:
    meal = load_meal_for_user(session, user_id, meal_id)
    meal.is_archived = True
    session.add(meal)
    session.commit()


def export_meals_csv(session: Session, user_id: int) -> str:
    meals = list_meals(session, user_id, include_archived=True)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "title",
            "complexity",
            "recurrence_tier",
            "seasonality_mode",
            "tags",
            "dietary_exclusions",
            "notes",
            "source_note",
            "source_url",
            "agent_sourced",
            "is_archived",
            "created_at",
            "updated_at",
        ]
    )
    for meal in meals:
        writer.writerow(
            [
                meal.id,
                meal.title,
                meal.complexity,
                meal.recurrence_tier,
                meal.seasonality_mode,
                ", ".join(sorted(link.tag.name for link in meal.tag_links if link.tag)),
                " | ".join(meal.dietary_exclusions),
                meal.notes,
                meal.source_note,
                meal.source_url,
                meal.agent_sourced,
                meal.is_archived,
                meal.created_at.isoformat(),
                meal.updated_at.isoformat(),
            ]
        )
    return buffer.getvalue()


def get_tag_suggestions(session: Session, user_id: int) -> list[str]:
    existing = session.query(MealTag.name).filter(MealTag.user_id == user_id).all()
    names = {row[0] for row in existing}
    return sorted(names.union(STARTER_TAGS))
