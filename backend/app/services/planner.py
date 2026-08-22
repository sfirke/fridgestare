import random
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session, joinedload

from app.models.meal import Meal, MealTagLink
from app.models.plan import PlanSlot, WeeklyPlan
from app.models.user import RecurringRule, User, UserPreferences

RECURRENCE_WEIGHTS = {"staple": 3.0, "regular": 2.0, "treat": 1.0}
SEASON_INDEX = {
    12: "winter",
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "fall",
    10: "fall",
    11: "fall",
}


def compute_week_start(reference_date: date, week_starts_on: int) -> date:
    offset = (reference_date.weekday() - week_starts_on) % 7
    return reference_date - timedelta(days=offset)


def current_local_date(timezone_name: str, now: datetime | None = None) -> date:
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        timezone = ZoneInfo("UTC")

    current_moment = now or datetime.now(tz=UTC)
    if current_moment.tzinfo is None:
        current_moment = current_moment.replace(tzinfo=UTC)
    return current_moment.astimezone(timezone).date()


def compute_planning_week_start(reference_date: date, week_starts_on: int) -> date:
    return compute_week_start(reference_date + timedelta(days=1), week_starts_on)


def compute_next_week_start(reference_date: date, week_starts_on: int) -> date:
    return compute_week_start(reference_date, week_starts_on) + timedelta(days=7)


def load_history(session: Session, user_id: int, before_week: date) -> list[PlanSlot]:
    horizon = before_week - timedelta(weeks=12)
    return (
        session.query(PlanSlot)
        .join(WeeklyPlan, WeeklyPlan.id == PlanSlot.plan_id)
        .filter(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.week_start_date >= horizon,
            WeeklyPlan.week_start_date < before_week,
        )
        .all()
    )


def rule_summary(rules: list[RecurringRule], day_index: int) -> dict:
    summary = {
        "takeout": False,
        "prefer_tags": [],
        "must_tags": [],
        "avoid_complex": False,
    }
    for rule in rules:
        if not rule.active or rule.day_of_week != day_index:
            continue
        if rule.rule_type == "takeout":
            summary["takeout"] = True
        if rule.rule_type == "prefer_tag":
            tag_name = rule.rule_payload.get("tag")
            if tag_name:
                summary["prefer_tags"].append(str(tag_name).lower())
        if rule.rule_type == "must_include_tag":
            tag_name = rule.rule_payload.get("tag")
            if tag_name:
                summary["must_tags"].append(str(tag_name).lower())
        if rule.rule_type == "avoid_complex":
            summary["avoid_complex"] = True
    return summary


def complexity_allowed(preferences: UserPreferences, meal: Meal, rule_info: dict) -> bool:
    if meal.complexity == "simple":
        return preferences.allow_simple
    if meal.complexity == "intermediate":
        return preferences.allow_intermediate
    if meal.complexity == "complex":
        return preferences.allow_complex and not rule_info["avoid_complex"]
    return True


def meal_tags(meal: Meal) -> set[str]:
    return {link.tag.name for link in meal.tag_links if link.tag is not None}


def effective_recurrence_tier(meal: Meal, slot_date: date) -> tuple[str, str, bool]:
    season = SEASON_INDEX[slot_date.month]
    override_map = {
        override.season: override.recurrence_tier for override in meal.seasonal_recurrence_overrides
    }
    effective = override_map.get(season, meal.recurrence_tier)
    return effective, season, season in override_map


# Each branch below applies one independent scoring rule; splitting them apart would
# obscure the rubric rather than clarify it.
def score_meal(  # pylint: disable=too-many-branches
    meal: Meal,
    slot_date: date,
    rule_info: dict,
    preferences: UserPreferences,
    history: list[PlanSlot],
    selected_meal_ids: set[int],
) -> tuple[float, str]:
    tags = meal_tags(meal)
    if rule_info["must_tags"] and not tags.intersection(rule_info["must_tags"]):
        return (-10_000.0, "Skipped because it does not satisfy a required day tag.")
    if not complexity_allowed(preferences, meal, rule_info):
        return (-10_000.0, "Skipped because the meal complexity is not allowed.")

    recurrence_tier, season, uses_seasonal_override = effective_recurrence_tier(meal, slot_date)
    if recurrence_tier == "none":
        return (-10_000.0, f"Skipped because it is disabled for {season}.")

    score = RECURRENCE_WEIGHTS.get(recurrence_tier, 1.5)
    notes: list[str] = []
    if uses_seasonal_override:
        notes.append(f"uses its {season} seasonal recurrence")
    if meal.id in selected_meal_ids:
        score -= 8
        notes.append("already used this week")
    if rule_info["prefer_tags"] and tags.intersection(rule_info["prefer_tags"]):
        score += 2.5
        notes.append("matches day-specific tag guidance")
    guidance = preferences.planning_guidance_text.lower()
    if guidance and any(tag in guidance for tag in tags):
        score += 1.5
        notes.append("matches planning guidance")

    for previous_slot in history:
        if previous_slot.meal_id != meal.id:
            continue
        age_days = (slot_date - previous_slot.slot_date).days
        if age_days <= 14 and previous_slot.outcome_status == "cooked":
            score -= 5
            notes.append("recently cooked")
        elif age_days <= 14 and previous_slot.outcome_status == "skipped":
            score -= 2
            notes.append("recently skipped")
        elif age_days <= 21:
            score -= 3
            notes.append("recently planned")

    if not notes:
        notes.append("fits your current plan settings")
    return score, "; ".join(notes)


def build_plan_explanation(slot_explanations: list[str], constraint_notes: list[str]) -> str:
    lines = ["Weekly plan generated from your meal library and recent history."]
    lines.extend(f"- {note}" for note in constraint_notes)
    lines.extend(f"- {line}" for line in slot_explanations)
    return "\n".join(lines)


def choose_scored_meal(scored: list[tuple[Meal, float, str]]) -> tuple[Meal, float, str]:
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    if len(ranked) == 1:
        return ranked[0]

    selection_pool = [candidate for candidate in ranked if candidate[1] >= ranked[0][1] - 1.5]
    if len(selection_pool) < min(3, len(ranked)):
        selection_pool = ranked[: min(3, len(ranked))]

    weight_floor = min(candidate[1] for candidate in selection_pool)
    weights = [(candidate[1] - weight_floor) + 1.0 for candidate in selection_pool]
    return random.choices(selection_pool, weights=weights, k=1)[0]


def slot_can_be_reused(slot_payload: dict) -> bool:
    return slot_payload["slot_type"] == "meal" and slot_payload["meal_id"] is not None


def slot_explanation(slot_payload: dict) -> str:
    slot_date = slot_payload["slot_date"]
    title = slot_payload["title_snapshot"]
    reason = slot_payload["selection_reason"]
    if slot_payload["slot_type"] == "takeout":
        return f"{slot_date:%A}: Takeout Night because {reason}"
    if slot_payload["slot_type"] == "leftover":
        return f"{slot_date:%A}: Leftovers ({title}) because {reason}"
    if slot_payload["slot_type"] == "empty":
        return f"{slot_date:%A}: Unplanned because {reason}"
    return f"{slot_date:%A}: {title} because {reason}"


def previous_week_leftover_sources(history: list[PlanSlot], week_start_date: date) -> list[dict]:
    previous_week_start = week_start_date - timedelta(days=7)
    return [
        {
            "meal_id": slot.meal_id,
            "title_snapshot": slot.title_snapshot,
            "notes_snapshot": slot.notes_snapshot,
            "slot_date": slot.slot_date,
        }
        for slot in sorted(history, key=lambda item: item.slot_date)
        if previous_week_start <= slot.slot_date < week_start_date
        and slot.meal_id is not None
        and slot.slot_type in {"meal", "leftover"}
    ]


def apply_leftover_preferences(
    slot_payloads: list[dict],
    history: list[PlanSlot],
    week_start_date: date,
    leftovers_target: int,
) -> list[str]:
    if leftovers_target <= 0:
        return []

    notes: list[str] = []
    previous_week_sources = previous_week_leftover_sources(history, week_start_date)
    previous_week_index = 0
    leftovers_selected = 0
    reserved_source_indices: set[int] = set()

    for target_index in range(len(slot_payloads) - 1, -1, -1):
        if leftovers_selected >= leftovers_target:
            break
        target_slot = slot_payloads[target_index]
        if not slot_can_be_reused(target_slot) or target_index in reserved_source_indices:
            continue

        source_index = next(
            (
                candidate_index
                for candidate_index in range(target_index - 1, -1, -1)
                if slot_can_be_reused(slot_payloads[candidate_index])
                and candidate_index not in reserved_source_indices
            ),
            None,
        )
        if source_index is not None:
            source_slot = slot_payloads[source_index]
            reserved_source_indices.add(source_index)
            target_slot.update(
                {
                    "slot_type": "leftover",
                    "meal_id": source_slot["meal_id"],
                    "discovered_candidate_id": None,
                    "title_snapshot": source_slot["title_snapshot"],
                    "notes_snapshot": source_slot["notes_snapshot"],
                    "selection_reason": (
                        f"Saved for leftovers from {source_slot['slot_date']:%A}'s "
                        f"{source_slot['title_snapshot']}."
                    ),
                }
            )
            leftovers_selected += 1
            continue

        if previous_week_index < len(previous_week_sources):
            source_slot = previous_week_sources[previous_week_index]
            previous_week_index += 1
            target_slot.update(
                {
                    "slot_type": "leftover",
                    "meal_id": source_slot["meal_id"],
                    "discovered_candidate_id": None,
                    "title_snapshot": source_slot["title_snapshot"],
                    "notes_snapshot": source_slot["notes_snapshot"],
                    "selection_reason": (
                        f"Saved for leftovers from last week's {source_slot['title_snapshot']}."
                    ),
                }
            )
            leftovers_selected += 1

    if leftovers_selected < leftovers_target:
        notes.append(
            "Leftover preference could not be fully satisfied because there were not "
            "enough earlier meals to reuse."
        )
    return notes


def generate_slot_selection(
    meals: list[Meal],
    preferences: UserPreferences,
    rules: list[RecurringRule],
    history: list[PlanSlot],
    slot_date: date,
    selected_meal_ids: set[int],
) -> tuple[dict, str | None]:
    day_index = slot_date.weekday()
    rule_info = rule_summary(rules, day_index)
    if rule_info["takeout"]:
        return {
            "slot_type": "takeout",
            "meal_id": None,
            "discovered_candidate_id": None,
            "title_snapshot": "Takeout Night",
            "notes_snapshot": "",
            "selection_reason": "Recurring rule prefers takeout for this day.",
        }, None

    scored: list[tuple[Meal, float, str]] = []
    for meal in meals:
        score, reason = score_meal(
            meal, slot_date, rule_info, preferences, history, selected_meal_ids
        )
        if score > -500:
            scored.append((meal, score, reason))

    if not scored:
        note = "No eligible meals matched this day; leaving the slot unplanned."
        return {
            "slot_type": "empty",
            "meal_id": None,
            "discovered_candidate_id": None,
            "title_snapshot": "Unplanned",
            "notes_snapshot": "",
            "selection_reason": note,
        }, note

    meal, _, reason = choose_scored_meal(scored)
    selected_meal_ids.add(meal.id)
    explanation = f"{slot_date:%A}: {meal.title} because it {reason}."
    return {
        "slot_type": "meal",
        "meal_id": meal.id,
        "discovered_candidate_id": None,
        "title_snapshot": meal.title,
        "notes_snapshot": meal.notes,
        "selection_reason": reason,
    }, explanation


# Orchestrates the plan-generation pipeline (query meals, fill slots, backfill takeout,
# apply leftovers, explain); the local variables are each pipeline stage's output.
def generate_plan_payload(  # pylint: disable=too-many-locals
    session: Session, user: User, week_start_date: date
) -> tuple[list[dict], str]:
    preferences = user.preferences
    if preferences is None:
        raise ValueError("User preferences must exist before planning.")
    meals = (
        session.query(Meal)
        .options(
            joinedload(Meal.tag_links).joinedload(MealTagLink.tag),
            joinedload(Meal.seasonal_recurrence_overrides),
        )
        .filter(Meal.user_id == user.id, Meal.is_archived.is_(False))
        .order_by(Meal.title.asc())
        .all()
    )
    history = load_history(session, user.id, week_start_date)
    selected_meal_ids: set[int] = set()
    slot_payloads: list[dict] = []
    constraint_notes: list[str] = []

    takeout_target = round(preferences.takeout_frequency_per_week)
    takeout_days_selected = 0
    for offset in range(7):
        slot_date = week_start_date + timedelta(days=offset)
        slot_payload, note = generate_slot_selection(
            meals,
            preferences,
            user.recurring_rules,
            history,
            slot_date,
            selected_meal_ids,
        )
        if slot_payload["slot_type"] == "takeout":
            takeout_days_selected += 1
        slot_payloads.append({**slot_payload, "slot_date": slot_date, "slot_order": offset})
        if note:
            constraint_notes.append(note)

    if takeout_target > takeout_days_selected:
        remaining = takeout_target - takeout_days_selected
        for slot_payload in reversed(slot_payloads):
            if remaining == 0:
                break
            if slot_payload["slot_type"] == "meal":
                slot_payload.update(
                    {
                        "slot_type": "takeout",
                        "meal_id": None,
                        "title_snapshot": "Takeout Night",
                        "notes_snapshot": "",
                        "selection_reason": "Added to satisfy your weekly takeout preference.",
                    }
                )
                remaining -= 1
        if remaining:
            constraint_notes.append(
                "Takeout preference could not be fully satisfied because several "
                "slots were already constrained."
            )

    constraint_notes.extend(
        apply_leftover_preferences(
            slot_payloads, history, week_start_date, preferences.leftovers_per_week
        )
    )

    slot_explanations = [slot_explanation(slot_payload) for slot_payload in slot_payloads]

    return slot_payloads, build_plan_explanation(slot_explanations, constraint_notes)
