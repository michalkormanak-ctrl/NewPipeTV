"""Režim LEGISLATÍVNY_PROJEKT (sekcia 11 zadania) - API vstupný bod.

DÔLEŽITÉ: beží nad `FakeLLMProvider` (docs/adr/0004), kým nie je k
dispozícii Vertex AI Gemini prístup. Výstup NIE JE právne použiteľný -
pozri disclaimer v odpovedi a docs/known-limitations.md."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.export.json_exporter import to_dict
from app.generator.legislative_project import run_legislative_project
from app.llm.fake import FakeLLMProvider
from app.models.security import AuditEvent
from app.schemas.generator import DraftingRequestIn

router = APIRouter(prefix="/api/v1/legislative-project", tags=["legislative-project"])


@router.post("")
def create_legislative_project(request_in: DraftingRequestIn, db: Session = Depends(get_db)) -> dict:
    package = run_legislative_project(
        request_in.to_dataclass(), db, FakeLLMProvider(), as_of=request_in.as_of
    )

    db.add(
        AuditEvent(
            action="draft_created",
            resource_type="legislative_project",
            resource_id=request_in.title[:255],
            model_used="fake-llm-v0",
            details=f"as_of={package.as_of_date.isoformat()} findings={len(package.control_findings)}",
        )
    )
    db.commit()

    return to_dict(package)
