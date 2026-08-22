from dataclasses import dataclass, field
from time import monotonic

from fastapi import HTTPException, Request, status


@dataclass
class RateLimitBucket:
    window_seconds: int
    hits: list[float] = field(default_factory=list)

    def prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self.hits = [hit for hit in self.hits if hit > cutoff]

    def is_expired(self, now: float) -> bool:
        return not self.hits or self.hits[-1] <= now - self.window_seconds


REQUEST_LOG: dict[str, RateLimitBucket] = {}


def client_identifier(request: Request, identifier: str | None = None) -> str:
    """Bucket key for a request: an explicit identifier, else the peer address."""
    if identifier:
        return identifier
    return request.client.host if request.client else "anonymous"


def enforce_rate_limit(
    request: Request,
    bucket: str,
    limit: int,
    window_seconds: int,
    identifier: str | None = None,
) -> None:
    bucket_key = f"{bucket}:{client_identifier(request, identifier)}"
    now = monotonic()
    entry = REQUEST_LOG.get(bucket_key)
    if entry is None or entry.window_seconds != window_seconds:
        entry = RateLimitBucket(window_seconds=window_seconds)
        REQUEST_LOG[bucket_key] = entry

    entry.prune(now)
    if len(entry.hits) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again shortly.",
        )
    entry.hits.append(now)
    evict_expired_buckets(now)


def evict_expired_buckets(now: float) -> None:
    """Drop buckets whose hits have all aged out.

    Keys are attacker-controlled (login buckets by the submitted email), so without
    this sweep the in-process log grows without bound under a credential-stuffing run.
    """
    for key in [key for key, entry in REQUEST_LOG.items() if entry.is_expired(now)]:
        del REQUEST_LOG[key]
