from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.rate_limit import REQUEST_LOG, client_identifier, enforce_rate_limit


def make_request(host: str | None) -> SimpleNamespace:
    return SimpleNamespace(client=SimpleNamespace(host=host) if host else None)


def test_explicit_identifier_wins_even_without_a_client_address() -> None:
    request = make_request(None)

    assert client_identifier(request, "sam@example.com") == "sam@example.com"
    assert client_identifier(request) == "anonymous"
    assert client_identifier(make_request("10.0.0.1")) == "10.0.0.1"


def test_separate_identifiers_do_not_share_a_budget() -> None:
    request = make_request(None)

    for _ in range(3):
        enforce_rate_limit(request, bucket="login", limit=3, window_seconds=60, identifier="a@x")

    with pytest.raises(HTTPException) as exceeded:
        enforce_rate_limit(request, bucket="login", limit=3, window_seconds=60, identifier="a@x")
    assert exceeded.value.status_code == 429

    # A different account must still be able to log in.
    enforce_rate_limit(request, bucket="login", limit=3, window_seconds=60, identifier="b@x")


def test_expired_buckets_are_evicted() -> None:
    request = make_request(None)

    enforce_rate_limit(request, bucket="login", limit=3, window_seconds=0, identifier="stale@x")
    enforce_rate_limit(request, bucket="login", limit=3, window_seconds=0, identifier="fresh@x")

    assert REQUEST_LOG == {}
