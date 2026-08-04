"""Deterministický poskytovateľ pre testy a lokálny vývoj bez cloudového účtu
(ADR-0004). NIKDY nepoužívať na produkčné právne odpovede."""
from __future__ import annotations

import hashlib

from app.llm.base import GroundedClaim, LLMResponse


class FakeLLMProvider:
    def generate(
        self, system_prompt: str, user_prompt: str, context_documents: list[str]
    ) -> LLMResponse:
        prompt_hash = hashlib.sha256((system_prompt + user_prompt).encode("utf-8")).hexdigest()
        if not context_documents:
            claim = GroundedClaim(
                text="Nenašli sa žiadne relevantné zdroje pre tento dopyt.",
                claim_type="nevyriesena_otazka",
                citation_ids=[],
                supported=False,
            )
            return LLMResponse(
                text=claim.text, claims=[claim], model_name="fake-llm-v0", prompt_hash=prompt_hash
            )

        claims = [
            GroundedClaim(
                text=f"[FAKE-LLM - iba pre testy] Nájdený relevantný zdroj: {doc[:120]}",
                claim_type="overene_platne_pravo",
                citation_ids=[f"doc-{i}"],
                supported=True,
            )
            for i, doc in enumerate(context_documents)
        ]
        text = "\n".join(c.text for c in claims)
        return LLMResponse(text=text, claims=claims, model_name="fake-llm-v0", prompt_hash=prompt_hash)


class FakeEmbeddingProvider:
    """Deterministický 'embedding' (hash-based), iba pre testy - nenesie
    žiadny reálny sémantický význam."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors.append([b / 255.0 for b in digest[:16]])
        return vectors
