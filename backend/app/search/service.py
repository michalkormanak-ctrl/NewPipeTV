"""Presné a fulltextové vyhľadávanie nad primárnym registrom (sekcia 9).

V pilote beží fulltext ako jednoduchý `ILIKE` nad Postgresom/SQLite (aby
testy nevyžadovali bežiaci OpenSearch). Produkčná BM25/reranking vrstva je
`search/opensearch_client.py` (mimo automatizovaných testov - vyžaduje
bežiaci OpenSearch, viď docker-compose.yml)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.legal import LegalInstrument
from app.models.provisions import Provision, ProvisionVersion
from app.search.normalize import LegalReference, normalize_reference


@dataclass(frozen=True)
class SearchResult:
    instrument_full_citation: str
    provision_label: str
    text: str
    effective_from: date
    effective_to: date | None
    source_url: str | None
    consolidation_disclaimer: str | None


def _to_result(
    instrument: LegalInstrument, provision: Provision, version: ProvisionVersion
) -> SearchResult:
    return SearchResult(
        instrument_full_citation=instrument.full_citation,
        provision_label=provision.label,
        text=version.text,
        effective_from=version.effective_from,
        effective_to=version.effective_to,
        source_url=None,
        consolidation_disclaimer=None,
    )


def search_exact(session: Session, reference: LegalReference, as_of: date) -> list[SearchResult]:
    """Presné vyhľadanie podľa normalizovaného odkazu (bod 9.1 - má prednosť
    pred významovou podobnosťou)."""
    if not reference.unit or not reference.number:
        return []

    label = f"{reference.unit}{reference.number}"
    stmt = (
        select(Provision, ProvisionVersion, LegalInstrument)
        .join(ProvisionVersion, ProvisionVersion.provision_id == Provision.id)
        .join(LegalInstrument, LegalInstrument.id == Provision.instrument_id)
        .where(Provision.label == label)
        .where(ProvisionVersion.effective_from <= as_of)
        .where(
            (ProvisionVersion.effective_to.is_(None)) | (ProvisionVersion.effective_to >= as_of)
        )
    )

    if reference.instrument_number and reference.instrument_year:
        stmt = stmt.where(LegalInstrument.number == reference.instrument_number).where(
            LegalInstrument.year == int(reference.instrument_year)
        )

    rows = session.execute(stmt).all()
    return [_to_result(instrument, provision, version) for provision, version, instrument in rows]


def search_fulltext(session: Session, query: str, as_of: date, limit: int = 20) -> list[SearchResult]:
    """Jednoduché fulltextové vyhľadávanie (ILIKE) - nahradiť OpenSearch BM25
    v produkcii (viď docs/architecture.md sekcia 6, ADR pripravené)."""
    stmt = (
        select(Provision, ProvisionVersion, LegalInstrument)
        .join(ProvisionVersion, ProvisionVersion.provision_id == Provision.id)
        .join(LegalInstrument, LegalInstrument.id == Provision.instrument_id)
        .where(ProvisionVersion.text.ilike(f"%{query}%"))
        .where(ProvisionVersion.effective_from <= as_of)
        .where(
            (ProvisionVersion.effective_to.is_(None)) | (ProvisionVersion.effective_to >= as_of)
        )
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    return [_to_result(instrument, provision, version) for provision, version, instrument in rows]


def search(session: Session, raw_query: str, as_of: date | None = None) -> tuple[list[SearchResult], date, bool]:
    """Hybridný vstupný bod: skúsi presnú zhodu podľa normalizovaného odkazu,
    a ak nič nenájde (alebo dopyt nevyzerá ako odkaz), spadne na fulltext.
    Vracia aj `as_of` a príznak, či bol dátum implicitný (bod 3.3 - vždy
    explicitne uviesť, ku ktorému dátumu sa stav posudzuje)."""
    used_default_date = as_of is None
    effective_as_of = as_of or date.today()

    reference = normalize_reference(raw_query)
    exact_results = search_exact(session, reference, effective_as_of)
    if exact_results:
        return exact_results, effective_as_of, used_default_date

    return search_fulltext(session, raw_query, effective_as_of), effective_as_of, used_default_date
