from datetime import UTC, datetime
from urllib.parse import quote_plus

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.clients.tavily import TavilyAdapter
from app.core.config import get_settings
from app.models.plan import DiscoveredRecipeCandidate
from app.models.user import User
from app.schemas.meal import MealCreate
from app.services.meals import create_meal
from app.services.plans import load_plan_for_user, set_slot_contents
from app.schemas.plan import SetSlotRequest


def candidate_to_schema(candidate: DiscoveredRecipeCandidate) -> dict:
    return {
        "id": candidate.id,
        "title": candidate.title,
        "summary": candidate.summary,
        "source_url": candidate.source_url,
        "complexity": candidate.complexity,
        "reasoning": candidate.reasoning,
        "accepted_meal_id": candidate.accepted_meal_id,
        "created_at": candidate.created_at,
    }


def fallback_candidates(user: User, query: str) -> list[dict]:
    guidance = user.preferences.planning_guidance_text if user.preferences else ""
    phrase = query.strip() or guidance.strip() or "weekday dinner"
    base_query = quote_plus(phrase)
    return [
        {
            "title": f"Skillet {phrase.title()}",
            "summary": f"A discovered recipe suggestion shaped around {phrase}.",
            "source_url": f"https://www.seriouseats.com/search?q={base_query}",
            "complexity": "simple",
            "reasoning": "Fallback discovery suggestion generated locally because no web provider is configured.",
        },
        {
            "title": f"Sheet Pan {phrase.title()}",
            "summary": f"An easy weeknight option that fits {phrase}.",
            "source_url": f"https://www.bonappetit.com/search?q={base_query}",
            "complexity": "intermediate",
            "reasoning": "Fallback discovery suggestion generated locally because no web provider is configured.",
        },
    ]


def build_discovery_query(user: User, query: str | None) -> str:
    preferences = user.preferences
    dietary = preferences.dietary_notes if preferences else ""
    guidance = preferences.planning_guidance_text if preferences else ""
    parts = ["dinner recipe"]
    if query:
        parts.append(query)
    if dietary:
        parts.append(f"dietary notes: {dietary}")
    if guidance:
        parts.append(f"guidance: {guidance}")
    return "; ".join(parts)


def suggest_candidates(session: Session, user: User, query: str | None) -> list[DiscoveredRecipeCandidate]:
    settings = get_settings()
    built_query = build_discovery_query(user, query)
    adapter = TavilyAdapter(settings.tavily_api_key)
    results = adapter.search(built_query)
    if not results:
        results = fallback_candidates(user, query or "dinner")
    candidates: list[DiscoveredRecipeCandidate] = []
    for item in results:
        candidate = DiscoveredRecipeCandidate(
            user_id=user.id,
            title=item["title"],
            summary=item["summary"],
            source_url=item["source_url"],
            complexity=item.get("complexity", "intermediate"),
            reasoning=item.get("reasoning", "Matches your current preferences."),
            created_at=datetime.now(tz=UTC),
        )
        session.add(candidate)
        candidates.append(candidate)
    session.commit()
    return candidates


def accept_candidate(
    session: Session,
    user: User,
    candidate_id: int,
    plan_id: int | None = None,
    slot_id: int | None = None,
    apply_to_plan: bool = True,
):
    candidate = (
        session.query(DiscoveredRecipeCandidate)
        .filter(DiscoveredRecipeCandidate.user_id == user.id, DiscoveredRecipeCandidate.id == candidate_id)
        .one_or_none()
    )
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discovery candidate not found")
    if candidate.accepted_meal_id is None:
        meal = create_meal(
            session,
            user.id,
            MealCreate(
                title=candidate.title,
                notes=candidate.summary,
                complexity=candidate.complexity,
                source_url=candidate.source_url,
                source_note="Agent sourced discovery",
                tags=[],
            ),
            agent_sourced=True,
        )
        candidate.accepted_meal_id = meal.id
        session.add(candidate)
        session.commit()
    else:
        meal = candidate.accepted_meal
    if apply_to_plan and plan_id and slot_id and meal is not None:
        set_slot_contents(
            session,
            user,
            plan_id,
            SetSlotRequest(slot_id=slot_id, meal_id=meal.id, slot_type="meal"),
        )
    return candidate, meal
