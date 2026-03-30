from __future__ import annotations

from fastapi import Request


def detect_client_type(request: Request) -> str:
    explicit = request.headers.get("x-client-type", "").strip().lower()
    if explicit in {"mobile", "web", "api"}:
        return explicit

    user_agent = request.headers.get("user-agent", "").lower()
    if "iphone" in user_agent:
        return "ios"
    if "android" in user_agent or "mobile" in user_agent:
        return "android"
    if "mozilla" in user_agent or "chrome" in user_agent or "safari" in user_agent or "edge" in user_agent:
        return "web"
    if "postman" in user_agent or "curl" in user_agent or "httpx" in user_agent:
        return "api"
    return "unknown"
