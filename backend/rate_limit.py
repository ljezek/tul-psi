from __future__ import annotations

import os
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status

# Module-level storage: key → list of request timestamps within the current window.
# Safe for asyncio (single-threaded event loop); not suitable for multi-process deployments
# without a shared backend (e.g. Redis), but perfectly adequate for this app.
_windows: dict[str, list[datetime]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    """Extract client IP, honouring the X-Forwarded-For header set by Azure's load-balancer."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(max_calls: int, period_seconds: int = 60) -> Depends:
    """Return a FastAPI ``Depends`` that throttles requests by client IP.

    Setting ``DISABLE_RATE_LIMIT=true`` bypasses all checks — used in test
    environments so the in-memory counters do not interfere with test suites.
    """

    def _check(request: Request) -> None:
        if os.getenv("DISABLE_RATE_LIMIT", "").lower() == "true":
            return
        key = f"{_client_ip(request)}:{max_calls}/{period_seconds}"
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=period_seconds)
        window = _windows[key]
        # Evict timestamps that have fallen outside the sliding window.
        while window and window[0] < cutoff:
            window.pop(0)
        if len(window) >= max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests — please wait before trying again.",
            )
        window.append(now)

    return Depends(_check)
