from __future__ import annotations

import asyncio
import json

import aiohttp

from .models import PrintResult


class PrintApiClient:
    def __init__(self, endpoint_url: str, token: str):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.token = token

    @property
    def print_url(self) -> str:
        if self.endpoint_url.endswith("/print"):
            return self.endpoint_url
        return f"{self.endpoint_url}/print"

    async def submit_html(self, html_document: str) -> PrintResult:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "text/html; charset=utf-8",
        }
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.print_url,
                    data=html_document.encode("utf-8"),
                    headers=headers,
                ) as response:
                    body = await response.text()
                    if response.status >= 400:
                        return PrintResult(
                            success=False,
                            stdout=body,
                            stderr="",
                            error=f"HTTP {response.status}: {body[:200]}",
                        )
                    try:
                        payload = json.loads(body) if body else {}
                    except json.JSONDecodeError:
                        payload = {}
                    job_id = payload.get("job_id")
                    return PrintResult(
                        success=True,
                        job_id=job_id,
                        stdout=body,
                        stderr="",
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:  # type: ignore[name-defined]
            return PrintResult(
                success=False,
                stdout="",
                stderr=str(exc),
                error="Failed to reach the configured print service.",
            )


async def validate_print_service(endpoint_url: str) -> tuple[bool, str]:
    if not endpoint_url:
        return False, "No print service URL configured."
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{endpoint_url.rstrip('/')}/healthz") as response:
                body = await response.text()
                if response.status == 200:
                    return True, body.strip() or "Print service is healthy."
                return False, f"HTTP {response.status}: {body[:200]}"
    except aiohttp.ClientError as exc:
        return False, str(exc)
