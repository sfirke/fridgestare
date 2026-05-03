import json

import httpx

from app.clients.base import ProviderAdapter


class OpenRouterAdapter(ProviderAdapter):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key.strip()
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def parse_chat_intent(self, system_prompt: str, user_prompt: str) -> dict | None:
        if not self.is_available():
            return None
        try:
            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
                timeout=20,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception:
            return None
