from datetime import date, timedelta


def create_meal(client, csrf_token: str, title: str, tags: list[str], complexity: str = "intermediate"):
    response = client.post(
        "/api/meals",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "title": title,
            "tags": tags,
            "complexity": complexity,
        },
    )
    assert response.status_code == 201
    return response.json()


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
        json={"recurrence_tier": "staple", "tags": ["cozy", "quick"]},
    )
    assert updated.status_code == 200
    updated_payload = updated.json()
    assert updated_payload["recurrence_tier"] == "staple"
    assert {tag["name"] for tag in updated_payload["tags"]} == {"cozy", "quick"}

    suggestions = client.get("/api/tags/suggestions")
    assert suggestions.status_code == 200
    suggestion_names = {item["name"] for item in suggestions.json()}
    assert {"cozy", "quick", "soup", "takeout-inspired"}.issubset(suggestion_names)

    exported = client.get("/api/meals/export.csv")
    assert exported.status_code == 200
    assert "Taco Soup" in exported.text

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


def test_plan_generation_and_mutations(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client
    taco = create_meal(client, csrf_token, "Taco Soup", ["soup", "tacos"], "simple")
    roast = create_meal(client, csrf_token, "Roast Chicken", ["cozy"], "intermediate")
    pasta = create_meal(client, csrf_token, "Pasta Primavera", ["quick"], "simple")

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
        json={"week_start_date": str(date.today() - timedelta(days=date.today().weekday()))},
    )
    assert generated.status_code == 200
    plan = generated.json()
    assert len(plan["slots"]) == 7
    assert any(slot["slot_type"] == "takeout" for slot in plan["slots"])

    slot_ids = [slot["id"] for slot in plan["slots"]]
    set_slot = client.post(
        f"/api/plans/{plan['id']}/set-slot",
        headers={"X-CSRF-Token": csrf_token},
        json={"slot_id": slot_ids[0], "meal_id": taco["id"], "slot_type": "meal"},
    )
    assert set_slot.status_code == 200
    assert set_slot.json()["slots"][0]["title_snapshot"] == "Taco Soup"

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
    assert current.status_code == 404

    titles = {slot["title_snapshot"] for slot in fetched.json()["slots"]}
    assert {"Taco Soup", "Roast Chicken", "Pasta Primavera", "Takeout Night"}.intersection(titles)

    next_week_start = date.today() - timedelta(days=date.today().weekday()) + timedelta(days=7)
    generated_next = client.post(
        "/api/plans/generate",
        headers={"X-CSRF-Token": csrf_token},
        json={},
    )
    assert generated_next.status_code == 200
    assert generated_next.json()["week_start_date"] == str(next_week_start)

    current = client.get("/api/plans/current")
    assert current.status_code == 200
    assert current.json()["week_start_date"] == str(next_week_start)
