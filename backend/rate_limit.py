from __future__ import annotations

import os
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status

# In-memory per-replica storage: key → deque of timestamps within the current window.
# Safe for asyncio (single-threaded event loop). With multiple ACA replicas each replica
# maintains its own counter, so the effective limit per client is max_calls × replica_count.
# For this app (dev has minReplicas=1, prod has minReplicas=1) that means a single replica
# in practice — acceptable for the auth endpoints being protected here.
_windows: dict[str, deque[datetime]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # Use the direct connection IP only; X-Forwarded-For is trivially spoofable by clients
    # and is NOT trusted here since Azure Container Apps sets it from untrusted input.
    return request.client.host if request.client else "unknown"


def rate_limit(max_calls: int, period_seconds: int = 60) -> Depends:
    """Return a FastAPI ``Depends`` that throttles requests by client IP.

    Setting ``DISABLE_RATE_LIMIT=true`` bypasses all checks — used in test
    environments so the in-memory counters do not interfere with test suites.

    slowapi (the usual choice) was evaluated but is incompatible with Pydantic v2:
    its decorator approach wraps the endpoint function in a way that breaks FastAPI's
    parameter inspection, causing request bodies to be silently dropped (422 errors).
    This ``Depends``-based implementation avoids that issue with no extra dependencies.
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
