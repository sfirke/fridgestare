import httpx
import pytest

from app.clients.mailgun import MailgunAdapter, MailgunDeliveryError


def test_adapter_reports_unconfigured_without_credentials() -> None:
    result = MailgunAdapter("", "").send("a@b.test", "c@d.test", "subject", "<p>hi</p>")

    assert result.configured is False
    assert result.delivered is False


def test_adapter_raises_when_mailgun_rejects_the_message(monkeypatch) -> None:
    """A configured key that fails must not look like a successful send.

    This used to return False, which the caller could not tell apart from "no key
    configured", so a bad key silently downgraded to a mock delivery.
    """

    def fake_post(*_args, **_kwargs) -> httpx.Response:
        return httpx.Response(
            401, text="Forbidden", request=httpx.Request("POST", "https://api.mailgun.net")
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(MailgunDeliveryError, match="HTTP 401"):
        MailgunAdapter("key-123", "mg.example.test").send(
            "a@b.test", "c@d.test", "subject", "<p>hi</p>"
        )


def test_adapter_raises_when_mailgun_is_unreachable(monkeypatch) -> None:
    def fake_post(*_args, **_kwargs) -> httpx.Response:
        raise httpx.ConnectError("no route to host")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(MailgunDeliveryError, match="Could not reach Mailgun"):
        MailgunAdapter("key-123", "mg.example.test").send(
            "a@b.test", "c@d.test", "subject", "<p>hi</p>"
        )


def test_adapter_uses_the_configured_region_base_url(monkeypatch) -> None:
    """EU sending domains live on api.eu.mailgun.net; the US host answers them with 401."""
    captured: dict[str, str] = {}

    def fake_post(url: str, **_kwargs) -> httpx.Response:
        captured["url"] = url
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)

    adapter = MailgunAdapter("key-123", "mg.example.test", "https://api.eu.mailgun.net")
    result = adapter.send("a@b.test", "c@d.test", "subject", "<p>hi</p>")

    assert result.delivered is True
    assert captured["url"] == "https://api.eu.mailgun.net/v3/mg.example.test/messages"
