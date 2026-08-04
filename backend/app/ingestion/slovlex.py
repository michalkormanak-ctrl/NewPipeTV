"""Ingestor pre Slov-Lex/eZbierka.

Dôležité (ADR-0003, docs/00-source-map.md): nenašli sme zdokumentované
oficiálne REST/XML API pre Slov-Lex, preto tento ingestor pracuje nad HTML
stránkou dokumentu. Presná CSS/HTML štruktúra `slov-lex.sk` NEBOLA v tomto
vývojovom sedení overená proti živému webu (sieťový prístup bol zablokovaný
egress politikou prostredia - pozri docs/risks.md R2). Selektory nižšie sú
zámerne tolerantné (viacero fallbackov) a musia byť potvrdené/doladené proti
reálnym stránkam pred produkčným nasadením.

Ingestor je testovaný nad `backend/tests/fixtures/slovlex_sample.html`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from app.ingestion.base import FetchedDocument
from app.ingestion.rate_limiter import RateLimitedSession


@dataclass(frozen=True)
class IngestedInstrumentDocument:
    """Výsledok jedného stiahnutia - pripravený na uloženie do
    `source_document` a ďalšie spracovanie parserom."""

    source_url: str
    title: str
    full_citation: str | None
    plain_text: str
    sha256: str
    mime_type: str
    size_bytes: int
    retrieved_at: datetime


# Viacero fallback selektorov - HTML štruktúra Slov-Lex nebola v tomto
# sedení overená naživo, preto sa skúša niekoľko bežných variantov.
_TITLE_SELECTORS = ["h1.document-title", "h1", "title"]
_CITATION_SELECTORS = [".document-citation", ".predpis-cislo", "meta[name='citation']"]
_CONTENT_SELECTORS = ["div.document-content", "div#content", "article", "body"]


def _first_text(soup: BeautifulSoup, selectors: list[str]) -> str | None:
    for selector in selectors:
        element = soup.select_one(selector)
        if element is not None:
            text = element.get("content") if element.name == "meta" else element.get_text(strip=True)
            if text:
                return text
    return None


def parse_slovlex_html(document: FetchedDocument) -> IngestedInstrumentDocument:
    soup = BeautifulSoup(document.content, "html.parser")

    title = _first_text(soup, _TITLE_SELECTORS) or "(neznámy názov - vyžaduje manuálnu kontrolu)"
    citation = _first_text(soup, _CITATION_SELECTORS)

    content_element = None
    for selector in _CONTENT_SELECTORS:
        content_element = soup.select_one(selector)
        if content_element is not None:
            break
    plain_text = content_element.get_text("\n", strip=True) if content_element else ""

    return IngestedInstrumentDocument(
        source_url=document.source_url,
        title=title,
        full_citation=citation,
        plain_text=plain_text,
        sha256=document.sha256,
        mime_type=document.mime_type,
        size_bytes=document.size_bytes,
        retrieved_at=datetime.now(timezone.utc),
    )


def ingest_document(url: str, session: RateLimitedSession, verify_robots: bool = True) -> IngestedInstrumentDocument:
    fetched = session.fetch(url, verify_robots=verify_robots)
    return parse_slovlex_html(fetched)
