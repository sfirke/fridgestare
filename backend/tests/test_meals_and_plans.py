from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.models.meal import Meal, MealSeasonalRecurrenceOverride
from app.services.planner import score_meal
from app.services.plans import current_planning_week_start


def create_meal(
    client,
    csrf_token: str,
    title: str,
    tags: list[str],
    complexity: str = "intermediate",
    recurrence_tier: str = "regular",
    seasonal_recurrence_overrides: list[dict] | None = None,
):
    response = client.post(
        "/api/meals",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "title": title,
            "tags": tags,
            "complexity": complexity,
            "recurrence_tier": recurrence_tier,
            "seasonal_recurrence_overrides": seasonal_recurrence_overrides or [],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_current_planning_week_start_uses_user_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    user = SimpleNamespace(timezone="America/Los_Angeles", week_starts_on=0)

    monkeypatch.setattr("app.services.plans.current_local_date", lambda timezone_name: date(2026, 5, 3))
    assert current_planning_week_start(user) == date(2026, 5, 4)

    monkeypatch.setattr("app.services.plans.current_local_date", lambda timezone_name: date(2026, 5, 4))
    assert current_planning_week_start(user) == date(2026, 5, 4)


def test_meal_crud_and_tag_suggestions(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client

    created = create_meal(client, csrf_token, "Taco Soup", ["soup", "tacos"], "simple")
    assert created["title"] == "Taco Soup"
    assert {tag["name"] for tag in created["tags"]} == {"soup", "tacos"}

    listed = client.get("/api/meals")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/meals/{created['id']}",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "recurrence_tier": "staple",
            "seasonal_recurrence_overrides": [
                {"season": "winter", "recurrence_tier": "staple"},
                {"season": "summer", "recurrence_tier": "none"},
            ],
            "tags": ["cozy", "quick"],
        },
    )
    assert updated.status_code == 200
    updated_payload = updated.json()
    assert updated_payload["recurrence_tier"] == "staple"
    assert updated_payload["seasonal_recurrence_overrides"] == [
        {"season": "winter", "recurrence_tier": "staple"},
        {"season": "summer", "recurrence_tier": "none"},
    ]
    assert {tag["name"] for tag in updated_payload["tags"]} == {"cozy", "quick"}

    suggestions = client.get("/api/tags/suggestions")
    assert suggestions.status_code == 200
    suggestion_names = {item["name"] for item in suggestions.json()}
    assert {"cozy", "quick", "soup", "takeout-inspired"}.issubset(suggestion_names)

    exported = client.get("/api/meals/export.csv")
    assert exported.status_code == 200
    assert "Taco Soup" in exported.text
    assert "summer_recurrence" in exported.text

    deleted = client.delete(
        f"/api/meals/{created['id']}",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert deleted.status_code == 204

    archived = client.get("/api/meals")
    assert archived.status_code == 200
    assert archived.json() == []


def test_bulk_fast_add(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client

    response = client.post(
        "/api/meals/bulk-fast-add",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "meals": [
                {"title": "Chili", "tags": ["cozy"]},
                {"title": "Tacos", "tags": ["tacos"], "complexity": "simple"},
            ]
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert len(payload) == 2
    assert {meal["title"] for meal in payload} == {"Chili", "Tacos"}


def test_score_meal_uses_seasonal_recurrence_override() -> None:
    meal = Meal(title="Lentil Soup", notes="", complexity="simple", recurrence_tier="regular")
    meal.tag_links = []
    meal.seasonal_recurrence_overrides = [
        MealSeasonalRecurrenceOverride(season="winter", recurrence_tier="staple"),
    ]
    preferences = SimpleNamespace(
        allow_simple=True,
        allow_intermediate=True,
        allow_complex=True,
        planning_guidance_text="",
    )

    score, reason = score_meal(
        meal,
        date(2026, 12, 7),
        {"takeout": False, "prefer_tags": [], "must_tags": [], "avoid_complex": False},
        preferences,
        [],
        set(),
    )

    assert score == 3.0
    assert "winter seasonal recurrence" in reason


def test_score_meal_skips_none_effective_recurrence() -> None:
    meal = Meal(title="Lentil Soup", notes="", complexity="simple", recurrence_tier="regular")
    meal.tag_links = []
    meal.seasonal_recurrence_overrides = [
        MealSeasonalRecurrenceOverride(season="summer", recurrence_tier="none"),
    ]
    preferences = SimpleNamespace(
        allow_simple=True,
        allow_intermediate=True,
        allow_complex=True,
        planning_guidance_text="",
    )

    score, reason = score_meal(
        meal,
        date(2026, 7, 7),
        {"takeout": False, "prefer_tags": [], "must_tags": [], "avoid_complex": False},
        preferences,
        [],
        set(),
    )

    assert score == -10_000.0
    assert reason == "Skipped because it is disabled for summer."


def test_plan_generation_and_mutations(authenticated_client: tuple, monkeypatch: pytest.MonkeyPatch) -> None:
    client, csrf_token = authenticated_client
    monkeypatch.setattr("app.services.plans.current_planning_week_start", lambda user: date(2026, 5, 4))
    monkeypatch.setattr("app.api.routes.plans.current_planning_week_start", lambda user: date(2026, 5, 4))

    taco = create_meal(client, csrf_token, "Taco Soup", ["soup", "tacos"], "simple")
    roast = create_meal(client, csrf_token, "Roast Chicken", ["cozy"], "intermediate")
    pasta = create_meal(client, csrf_token, "Pasta Primavera", ["quick"], "simple")
    create_meal(client, csrf_token, "Bean Chili", ["cozy", "beans"], "simple")

    preferences = client.patch(
        "/api/me/preferences",
        headers={"X-CSRF-Token": csrf_token},
        json={"leftovers_per_week": 2},
    )
    assert preferences.status_code == 200

    rules = client.patch(
        "/api/me/schedule-rules",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "rules": [
                {"day_of_week": 1, "rule_type": "prefer_tag", "rule_payload": {"tag": "tacos"}, "priority": 1, "active": True},
                {"day_of_week": 3, "rule_type": "takeout", "rule_payload": {}, "priority": 1, "active": True},
            ]
        },
    )
    assert rules.status_code == 200

    generated = client.post(
        "/api/plans/generate",
        headers={"X-CSRF-Token": csrf_token},
        json={"week_start_date": "2026-05-04"},
    )
    assert generated.status_code == 200
    plan = generated.json()
    assert len(plan["slots"]) == 7
    assert any(slot["slot_type"] == "takeout" for slot in plan["slots"])
    leftovers = [slot for slot in plan["slots"] if slot["slot_type"] == "leftover"]
    assert len(leftovers) == 2
    for leftover in leftovers:
        assert leftover["meal_id"] is not None
        assert any(
            candidate["slot_order"] < leftover["slot_order"] and candidate["meal_id"] == leftover["meal_id"]
            for candidate in plan["slots"]
        )

    slot_ids = [slot["id"] for slot in plan["slots"]]
    set_slot = client.post(
        f"/api/plans/{plan['id']}/set-slot",
        headers={"X-CSRF-Token": csrf_token},
        json={"slot_id": slot_ids[0], "meal_id": taco["id"], "slot_type": "meal"},
    )
    assert set_slot.status_code == 200
    assert set_slot.json()["slots"][0]["title_snapshot"] == "Taco Soup"

    set_leftover = client.post(
        f"/api/plans/{plan['id']}/set-slot",
        headers={"X-CSRF-Token": csrf_token},
        json={"slot_id": slot_ids[-1], "meal_id": roast["id"], "slot_type": "leftover"},
    )
    assert set_leftover.status_code == 200
    latest_slot = next(slot for slot in set_leftover.json()["slots"] if slot["id"] == slot_ids[-1])
    assert latest_slot["slot_type"] == "leftover"
    assert latest_slot["title_snapshot"] == "Roast Chicken"

    moved = client.post(
        f"/api/plans/{plan['id']}/move-slot",
        headers={"X-CSRF-Token": csrf_token},
        json={"source_slot_id": slot_ids[0], "target_slot_id": slot_ids[1]},
    )
    assert moved.status_code == 200

    rerolled = client.post(
        f"/api/plans/{plan['id']}/reroll-slot",
        headers={"X-CSRF-Token": csrf_token},
        json={"slot_id": slot_ids[1]},
    )
    assert rerolled.status_code == 200

    outcome = client.post(
        f"/api/plans/{plan['id']}/slots/{slot_ids[1]}/outcome-status",
        headers={"X-CSRF-Token": csrf_token},
        json={"outcome_status": "cooked"},
    )
    assert outcome.status_code == 200
    matching_slot = next(slot for slot in outcome.json()["slots"] if slot["id"] == slot_ids[1])
    assert matching_slot["outcome_status"] == "cooked"

    undo = client.post(
        f"/api/plans/{plan['id']}/undo",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert undo.status_code == 200

    fetched = client.get(f"/api/plans/week/{plan['week_start_date']}")
    assert fetched.status_code == 200
    assert len(fetched.json()["slots"]) == 7

    current = client.get("/api/plans/current")
    assert current.status_code == 200
    assert current.json()["week_start_date"] == "2026-05-04"

    titles = {slot["title_snapshot"] for slot in fetched.json()["slots"]}
    assert {"Taco Soup", "Roast Chicken", "Pasta Primavera", "Takeout Night"}.intersection(titles)

    next_week_start = date(2026, 5, 11)
    generated_next = client.post(
        "/api/plans/generate",
        headers={"X-CSRF-Token": csrf_token},
        json={"week_start_date": str(next_week_start)},
    )
    assert generated_next.status_code == 200
    assert generated_next.json()["week_start_date"] == str(next_week_start)

    history = client.get("/api/plans")
    assert history.status_code == 200
    assert [item["week_start_date"] for item in history.json()] == [
        str(next_week_start),
        "2026-05-04",
    ]

    current = client.get("/api/plans/current")
    assert current.status_code == 200
    assert current.json()["week_start_date"] == "2026-05-04"
