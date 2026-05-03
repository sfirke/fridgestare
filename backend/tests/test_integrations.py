from datetime import date


def setup_plan(client, csrf_token: str):
    client.post(
        "/api/meals/bulk-fast-add",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "meals": [
                {"title": "Tomato Soup", "tags": ["soup"], "complexity": "simple"},
                {"title": "Tuesday Tacos", "tags": ["tacos"], "complexity": "simple"},
                {"title": "Roast Fish", "tags": ["cozy"], "complexity": "intermediate"},
                {"title": "Braised Short Ribs", "tags": ["cozy"], "complexity": "complex"},
            ]
        },
    )
    generated = client.post("/api/plans/generate", headers={"X-CSRF-Token": csrf_token}, json={})
    assert generated.status_code == 200
    return generated.json()


def test_discovery_suggest_and_accept(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client
    plan = setup_plan(client, csrf_token)
    slot_id = plan["slots"][0]["id"]

    suggestions = client.post(
        "/api/discovery/suggest",
        headers={"X-CSRF-Token": csrf_token},
        json={"slot_id": slot_id, "query": "easy vegetarian soup"},
    )
    assert suggestions.status_code == 200
    candidates = suggestions.json()
    assert len(candidates) >= 1

    accepted = client.post(
        f"/api/discovery/{candidates[0]['id']}/accept",
        headers={"X-CSRF-Token": csrf_token},
        json={"plan_id": plan["id"], "slot_id": slot_id, "apply_to_plan": True},
    )
    assert accepted.status_code == 200
    payload = accepted.json()
    assert payload["meal"]["agent_sourced"] is True


def test_chat_endpoint_edits_plan(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client
    plan = setup_plan(client, csrf_token)

    response = client.post(
        f"/api/plans/{plan['id']}/chat",
        headers={"X-CSRF-Token": csrf_token},
        json={"message": "put a soup on Tuesday"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "Tuesday" in payload["explanation"] or "Put" in payload["explanation"]


def test_chat_endpoint_handles_complexity_request(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client
    plan = setup_plan(client, csrf_token)

    response = client.post(
        f"/api/plans/{plan['id']}/chat",
        headers={"X-CSRF-Token": csrf_token},
        json={"message": "give me a complex meal on Friday"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "Friday" in payload["explanation"]
    assert "complex" in payload["explanation"].lower()

    friday_slot = next(slot for slot in payload["plan"]["slots"] if date.fromisoformat(slot["slot_date"]).weekday() == 4)
    assert friday_slot["title_snapshot"] == "Braised Short Ribs"


def test_email_preview_and_send(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client
    plan = setup_plan(client, csrf_token)

    preview = client.get(f"/api/plans/{plan['id']}/email-preview")
    assert preview.status_code == 200
    assert "Fridgestare weekly plan" in preview.json()["html"]

    sent = client.post(
        f"/api/plans/{plan['id']}/send-email",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert sent.status_code == 200
    assert sent.json()["status"] == "queued"