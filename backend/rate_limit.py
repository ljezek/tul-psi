from __future__ import annotations

import os
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status

# In-memory per-replica storage: key → deque of timestamps within the current window.
# Safe for asyncio (single-threaded event loop). With multiple ACA replicas each replica
# maintains its own counter, so the effective limit per client is max_calls × replica_count.
# For this app (dev has minReplicas=0, prod has minReplicas=1) that means a single replica
# in practice for prod — acceptable for the auth endpoints being protected here.
_windows: dict[str, deque[datetime]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # ProxyHeadersMiddleware (configured in main.py) resolves request.client.host
    # to the real client IP from the trusted ACA ingress X-Forwarded-For header.
    return request.client.host if request.client else "unknown"


def rate_limit(max_calls: int, period_seconds: int = 60) -> Depends:
    """Return a FastAPI ``Depends`` that throttles requests by client IP.

    Setting ``DISABLE_RATE_LIMIT=true`` bypasses all checks — used in test
    environments so the in-memory counters do not interfere with test suites.

    A ``Depends``-based implementation was chosen instead of the popular slowapi
    library because slowapi's decorator approach wraps endpoint functions in a way
    that breaks FastAPI's parameter inspection with Pydantic v2, causing request
    bodies to be silently dropped (422 errors). This approach avoids that issue
    with no extra dependencies.
    """

    def _check(request: Request) -> None:
        if os.getenv("DISABLE_RATE_LIMIT", "").lower() == "true":
            return
        key = f"{_client_ip(request)}:{max_calls}/{period_seconds}"
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=period_seconds)
        window = _windows[key]
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests — please wait before trying again.",
            )
        window.append(now)

    return Depends(_check)
