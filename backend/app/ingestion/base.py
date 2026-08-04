"""Abstraktné rozhranie získavania dát (bod 5.2-5.3). Oddelené od parsera a
od konkrétneho zdroja, aby zmena HTML štruktúry alebo prechod na oficiálne
API (ak sa niekedy sprístupní) nevyžadovali zásah do zvyšku systému."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FetchedDocument:
    source_url: str
    content: bytes
    mime_type: str
    status_code: int

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()

    @property
    def size_bytes(self) -> int:
        return len(self.content)


class Fetcher(Protocol):
    """Nízkoúrovňové HTTP získanie jedného zdroja. Implementácie musia
    rešpektovať rate limiting a robots.txt na vyššej úrovni (RateLimitedSession)."""

    def fetch(self, url: str) -> FetchedDocument: ...
