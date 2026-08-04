"""Vymeniteľné LLM/embedding rozhranie (ADR-0004, bod 4 zadania)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GroundedClaim:
    """Jedno tvrdenie vo výstupe LLM a jeho stav ukotvenia (sekcia 10.3)."""

    text: str
    claim_type: str
    # overene_platne_pravo | historicke_znenie | judikatura_alebo_doktrina |
    # pravny_nazor_systemu | navrh_riesenia | predpoklad | nevyriesena_otazka
    citation_ids: list[str]
    supported: bool


@dataclass(frozen=True)
class LLMResponse:
    text: str
    claims: list[GroundedClaim]
    model_name: str
    prompt_hash: str


class LLMProvider(Protocol):
    def generate(self, system_prompt: str, user_prompt: str, context_documents: list[str]) -> LLMResponse: ...


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
