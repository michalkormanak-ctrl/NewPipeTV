"""Režim LEGISLATÍVNY_PROJEKT (sekcia 11 zadania) - API vstupný bod.

DÔLEŽITÉ: beží nad `FakeLLMProvider` (docs/adr/0004), kým nie je k
dispozícii Vertex AI Gemini prístup. Výstup NIE JE právne použiteľný -
pozri disclaimer v odpovedi a docs/known-limitations.md."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.export.json_exporter import to_dict
from app.generator.instruction_interpreter import run_legislative_project_from_text
from app.generator.legislative_project import run_legislative_project
from app.llm.fake import FakeLLMProvider
from app.models.security import AuditEvent
from app.schemas.generator import DraftingRequestIn, FreeTextInstructionIn

router = APIRouter(prefix="/api/v1/legislative-project", tags=["legislative-project"])


def _audit_draft_created(db: Session, resource_id: str, package) -> None:
    db.add(
        AuditEvent(
            action="draft_created",
            resource_type="legislative_project",
            resource_id=resource_id[:255],
            model_used="fake-llm-v0",
            details=f"as_of={package.as_of_date.isoformat()} findings={len(package.control_findings)}",
        )
    )
    db.commit()


@router.post("")
def create_legislative_project(request_in: DraftingRequestIn, db: Session = Depends(get_db)) -> dict:
    package = run_legislative_project(
        request_in.to_dataclass(), db, FakeLLMProvider(), as_of=request_in.as_of
    )
    _audit_draft_created(db, request_in.title, package)
    return to_dict(package)


@router.post("/from-text")
def create_legislative_project_from_text(
    request_in: FreeTextInstructionIn, db: Session = Depends(get_db)
) -> dict:
    """Prijme jednoduchý pokyn v prirodzenom jazyku (bod 2 zadania).
    Interpretácia je heuristická (regex, bez LLM) - ak sa nedá jednoznačne
    určiť predpis/ustanovenie, vráti balík s otvorenými otázkami namiesto
    pokusu pokračovať s vymysleným umiestnením zmeny (pravidlo 3.1)."""
    package = run_legislative_project_from_text(
        request_in.instruction,
        db,
        FakeLLMProvider(),
        as_of=request_in.as_of,
        title=request_in.title,
        amendment_instructions=[a.to_dataclass() for a in request_in.amendment_instructions],
    )
    _audit_draft_created(db, request_in.title or request_in.instruction, package)
    return to_dict(package)
