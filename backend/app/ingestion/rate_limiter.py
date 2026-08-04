"""Šetrný HTTP klient: rate limiting, exponenciálny odklad, kontrola robots.txt.

Používa sa nad každým ingestorom, ktorý číta verejné HTML/PDF stránky bez
oficiálneho API (bod 5.2, ADR-0003)."""
from __future__ import annotations

import time
import urllib.robotparser
from urllib.parse import urlparse

import httpx

from app.ingestion.base import FetchedDocument


class RobotsDisallowedError(RuntimeError):
    pass


class RateLimitedSession:
    def __init__(
        self,
        user_agent: str,
        min_interval_seconds: float = 2.0,
        max_retries: int = 3,
        client: httpx.Client | None = None,
    ) -> None:
        self._user_agent = user_agent
        self._min_interval = min_interval_seconds
        self._max_retries = max_retries
        self._client = client or httpx.Client(
            headers={"User-Agent": user_agent}, timeout=30.0, follow_redirects=True
        )
        self._last_request_at: float | None = None
        self._robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    def _wait_for_slot(self) -> None:
        if self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        remaining = self._min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _check_robots(self, url: str) -> None:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._robots_cache.get(origin)
        if parser is None:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(f"{origin}/robots.txt")
            try:
                response = self._client.get(f"{origin}/robots.txt")
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                else:
                    # robots.txt neprítomný alebo nedostupný -> fail-closed
                    # pre neznáme domény (bezpečnejšie než predpoklad povolenia).
                    raise RobotsDisallowedError(
                        f"robots.txt pre {origin} nie je dostupné (HTTP "
                        f"{response.status_code}); ingest sa zastavuje (fail-closed)."
                    )
            except httpx.HTTPError as exc:
                raise RobotsDisallowedError(
                    f"robots.txt pre {origin} sa nepodarilo overiť: {exc}"
                ) from exc
            self._robots_cache[origin] = parser

        if not parser.can_fetch(self._user_agent, url):
            raise RobotsDisallowedError(f"robots.txt zakazuje prístup na {url}")

    def fetch(self, url: str, verify_robots: bool = True) -> FetchedDocument:
        if verify_robots:
            self._check_robots(url)

        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            self._wait_for_slot()
            self._last_request_at = time.monotonic()
            try:
                response = self._client.get(url)
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        "server error", request=response.request, response=response
                    )
                return FetchedDocument(
                    source_url=url,
                    content=response.content,
                    mime_type=response.headers.get("content-type", "application/octet-stream"),
                    status_code=response.status_code,
                )
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(2**attempt)
        raise RuntimeError(f"Nepodarilo sa stiahnuť {url} po {self._max_retries} pokusoch") from last_exc
