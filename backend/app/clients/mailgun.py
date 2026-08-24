import logging
from dataclasses import dataclass

import httpx

from app.clients.base import ProviderAdapter

logger = logging.getLogger("app.clients.mailgun")


class MailgunDeliveryError(RuntimeError):
    """Mailgun is configured but the send did not go through."""


@dataclass(frozen=True)
class MailgunResult:
    delivered: bool
    configured: bool


class MailgunAdapter(ProviderAdapter):
    def __init__(self, api_key: str, domain: str, base_url: str = "https://api.mailgun.net"):
        self.api_key = api_key.strip()
        self.domain = domain.strip()
        self.base_url = base_url.strip().rstrip("/")

    def is_available(self) -> bool:
        return bool(self.api_key and self.domain)

    def send(self, sender: str, recipient: str, subject: str, html: str) -> MailgunResult:
        """Send one message.

        Returns an unconfigured result when there are no credentials, so local
        development still works. A configured send that fails raises instead of
        reporting success: a swallowed failure looked identical to a mock delivery,
        which meant a broken API key showed up as a plan silently marked "sent".
        """
        if not self.is_available():
            return MailgunResult(delivered=False, configured=False)
        try:
            response = httpx.post(
                f"{self.base_url}/v3/{self.domain}/messages",
                auth=("api", self.api_key),
                data={
                    "from": sender,
                    "to": [recipient],
                    "subject": subject,
                    "html": html,
                },
                timeout=20,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Mailgun explains rejected senders and unverified domains in the body.
            detail = exc.response.text[:500]
            logger.error(
                "Mailgun rejected the message with HTTP %s: %s", exc.response.status_code, detail
            )
            raise MailgunDeliveryError(
                f"Mailgun returned HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Could not reach Mailgun: %s", exc)
            raise MailgunDeliveryError(f"Could not reach Mailgun: {exc}") from exc
        return MailgunResult(delivered=True, configured=True)
