from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.security import AuditEvent
from app.search.service import SearchResult, search

router = APIRouter(prefix="/api/v1/search", tags=["search"])


class SearchResponse(BaseModel):
    query: str
    as_of: date
    as_of_was_default: bool
    as_of_note: str | None
    results: list[SearchResult]


@router.get("", response_model=SearchResponse)
def search_endpoint(
    q: str, as_of: date | None = None, db: Session = Depends(get_db)
) -> SearchResponse:
    results, effective_as_of, used_default = search(db, q, as_of)
    note = (
        f"Dátum posudzovania nebol zadaný, použil sa aktuálny dátum {effective_as_of.isoformat()}."
        if used_default
        else None
    )

    # Audit každého dopytu (sekcia 16.2, bod 10.1).
    db.add(
        AuditEvent(
            action="query",
            resource_type="search",
            resource_id=q[:255],
            details=f"results={len(results)} as_of={effective_as_of.isoformat()}",
        )
    )
    db.commit()

    return SearchResponse(
        query=q,
        as_of=effective_as_of,
        as_of_was_default=used_default,
        as_of_note=note,
        results=results,
    )
