import json
import logging

import httpx

from app.clients.base import ProviderAdapter

logger = logging.getLogger("app.clients.openrouter")


class OpenRouterAdapter(ProviderAdapter):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key.strip()
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _post_chat_completion(self, payload: dict) -> httpx.Response:
        return httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )

    @staticmethod
    def _json_object_unsupported(response: httpx.Response) -> bool:
        if response.status_code != 405:
            return False
        try:
            raw_message = response.json()["error"]["metadata"].get("raw", "")
        except (KeyError, TypeError, ValueError):
            return False
        return "json_object response format is not supported" in raw_message

    def parse_chat_intent(self, system_prompt: str, user_prompt: str) -> dict | None:
        if not self.is_available():
            logger.info("Skipping OpenRouter chat intent parse because no API key is configured.")
            return None
        try:
            logger.info("Submitting OpenRouter chat intent parse request with model=%s.", self.model)
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
            response = self._post_chat_completion(payload)
            if self._json_object_unsupported(response):
                logger.warning(
                    "OpenRouter model=%s rejected json_object response_format; retrying chat intent parse without structured output.",
                    self.model,
                )
                payload.pop("response_format", None)
                response = self._post_chat_completion(payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if isinstance(parsed, list):
                if len(parsed) == 1 and isinstance(parsed[0], dict):
                    logger.warning("OpenRouter chat intent parse returned a one-item list; using the first object.")
                    parsed = parsed[0]
                else:
                    logger.warning("OpenRouter chat intent parse returned %s; expected an object.", type(parsed).__name__)
                    return None
            if not isinstance(parsed, dict):
                logger.warning("OpenRouter chat intent parse returned %s; expected an object.", type(parsed).__name__)
                return None
            logger.info("OpenRouter chat intent parse succeeded.")
            return parsed
        except Exception:
            logger.exception("OpenRouter chat intent parse failed.")
            return None
