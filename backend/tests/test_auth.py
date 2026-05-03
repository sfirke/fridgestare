def test_login_and_me(authenticated_client: tuple) -> None:
    client, _ = authenticated_client
    me_response = client.get("/api/auth/me")

    assert me_response.status_code == 200
    payload = me_response.json()["me"]
    assert payload["user"]["email"] == "sam@example.com"
    assert payload["preferences"]["takeout_frequency_per_week"] == 1.0


def test_logout_requires_csrf(authenticated_client: tuple) -> None:
    client, csrf_token = authenticated_client

    missing_csrf = client.post("/api/auth/logout")
    assert missing_csrf.status_code == 403

    logged_out = client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logged_out.status_code == 200
