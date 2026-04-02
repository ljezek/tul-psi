from __future__ import annotations

import asyncio
import httpx


async def main() -> None:
    base = "http://localhost:8001"
    async with httpx.AsyncClient(timeout=5.0) as client:
        reqs = [
            client.get(f"{base}/projects", headers={"X-Client-Type": "android"}),
            client.get(f"{base}/projects?subject=PSI", headers={"X-Client-Type": "web"}),
            client.get(f"{base}/projects?academic_year=2024/25", headers={"X-Client-Type": "ios"}),
            client.get(f"{base}/health", headers={"X-Client-Type": "api"}),
        ]
        responses = await asyncio.gather(*reqs, return_exceptions=True)

    for idx, response in enumerate(responses, start=1):
        if isinstance(response, Exception):
            print(f"Request {idx} failed: {response}")
        else:
            print(f"Request {idx}: {response.status_code} -> {response.url.path}")


if __name__ == "__main__":
    asyncio.run(main())
