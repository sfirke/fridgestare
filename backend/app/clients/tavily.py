from urllib.parse import quote_plus

import httpx

from app.clients.base import ProviderAdapter


class TavilyAdapter(ProviderAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str) -> list[dict]:
        if not self.is_available():
            return []
        try:
            response = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": 5,
                    "search_depth": "basic",
                },
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []
        results = []
        for item in payload.get("results", []):
            results.append(
                {
                    "title": item.get("title", query.title()),
                    "summary": item.get("content", "")[:280],
                    "source_url": item.get("url", f"https://www.seriouseats.com/search?q={quote_plus(query)}"),
                }
            )
        return results
