"""Pydantic vstupná schéma pre /api/v1/export/* (zrkadlí LegislativePackage)."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.export.package import LegislativePackage, SourceCitation
from app.validators.legislative import ValidationFinding


class ValidationFindingIn(BaseModel):
    check: str
    severity: str
    message: str
    location: str | None = None

    def to_dataclass(self) -> ValidationFinding:
        return ValidationFinding(
            check=self.check, severity=self.severity, message=self.message, location=self.location
        )


class SourceCitationIn(BaseModel):
    instrument_full_citation: str
    provision_label: str | None = None
    source_url: str | None = None
    note: str | None = None

    def to_dataclass(self) -> SourceCitation:
        return SourceCitation(**self.model_dump())


class LegislativePackageIn(BaseModel):
    title: str
    generated_at: date
    as_of_date: date
    as_of_was_default: bool = False
    executive_summary: str
    current_legal_state: str
    problem_map: str
    variants: str
    paragraph_wording: str | None = None
    amendment_points: str | None = None
    consolidated_text: str | None = None
    explanatory_memorandum: str = ""
    accompanying_documents: str = ""
    control_findings: list[ValidationFindingIn] = []
    open_questions: list[str] = []
    sources: list[SourceCitationIn] = []

    def to_dataclass(self) -> LegislativePackage:
        data = self.model_dump(exclude={"control_findings", "sources"})
        return LegislativePackage(
            **data,
            control_findings=[f.to_dataclass() for f in self.control_findings],
            sources=[s.to_dataclass() for s in self.sources],
        )
