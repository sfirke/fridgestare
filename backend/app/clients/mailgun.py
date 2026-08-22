import httpx

from app.clients.base import ProviderAdapter


class MailgunAdapter(ProviderAdapter):
    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key.strip()
        self.domain = domain.strip()

    def is_available(self) -> bool:
        return bool(self.api_key and self.domain)

    def send(self, sender: str, recipient: str, subject: str, html: str) -> bool:
        if not self.is_available():
            return False
        try:
            response = httpx.post(
                f"https://api.mailgun.net/v3/{self.domain}/messages",
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
            return True
        except Exception:
            return False
