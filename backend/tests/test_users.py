def test_patch_preferences(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client

    response = client.patch(
        "/api/me/preferences",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "novel_meal_ratio": 0.4,
            "takeout_frequency_per_week": 2,
            "leftovers_per_week": 2,
            "planning_guidance_text": "Tuesday tacos.",
            "timezone": "America/Los_Angeles",
            "week_starts_on": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["novel_meal_ratio"] == 0.4
    assert payload["takeout_frequency_per_week"] == 2
    assert payload["leftovers_per_week"] == 2
    assert payload["planning_guidance_text"] == "Tuesday tacos."

    me_response = client.get("/api/me")
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["user"]["timezone"] == "America/Los_Angeles"
    assert me_payload["user"]["week_starts_on"] == 1


def test_replace_schedule_rules(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client

    response = client.patch(
        "/api/me/schedule-rules",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "rules": [
                {
                    "day_of_week": 1,
                    "rule_type": "prefer_tag",
                    "rule_payload": {"tag": "tacos"},
                    "priority": 10,
                    "active": True,
                },
                {
                    "day_of_week": 3,
                    "rule_type": "takeout",
                    "rule_payload": {"takeout": True},
                    "priority": 5,
                    "active": True,
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["rule_type"] == "prefer_tag"
    assert payload[1]["rule_type"] == "takeout"
