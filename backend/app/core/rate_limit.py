from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status

REQUEST_LOG: dict[str, deque[float]] = defaultdict(deque)


def enforce_rate_limit(
    request: Request,
    bucket: str,
    limit: int,
    window_seconds: int,
    identifier: str | None = None,
) -> None:
    key = identifier or request.client.host if request.client else "anonymous"
    bucket_key = f"{bucket}:{key}"
    now = monotonic()
    entries = REQUEST_LOG[bucket_key]
    while entries and now - entries[0] > window_seconds:
        entries.popleft()
    if len(entries) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again shortly.",
        )
    entries.append(now)
