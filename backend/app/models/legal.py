"""Entity work-expression-manifestation (ADR-0002) pre predpisy ako celok."""
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamped, UUIDPK


class LegalInstrument(Base, UUIDPK, Timestamped):
    """Predpis ako právna entita naprieč časom (work). Pozri bod 6.2 zadania."""

    __tablename__ = "legal_instrument"

    number: Mapped[str] = mapped_column(String(50))
    year: Mapped[int]
    full_citation: Mapped[str] = mapped_column(String(255))
    short_citation: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    instrument_type: Mapped[str] = mapped_column(String(50))  # zakon, novela, vyhlaska, ...
    legal_force: Mapped[str] = mapped_column(String(50))  # ustavny zakon, zakon, vyhlaska, ...
    issuing_authority: Mapped[str] = mapped_column(String(255))
    date_approved: Mapped[date | None] = mapped_column(Date)
    date_promulgated: Mapped[date | None] = mapped_column(Date)
    date_valid_from: Mapped[date | None] = mapped_column(Date)
    date_effective_from: Mapped[date | None] = mapped_column(Date)
    date_effective_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="unverified")
    # ucinny | zruseny | este_neucinny | neoverene
    legal_area: Mapped[str | None] = mapped_column(String(255))
    gestor: Mapped[str | None] = mapped_column(String(255))
    eli_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    source: Mapped[str] = mapped_column(String(50))  # slov-lex, eur-lex, ...
    language: Mapped[str] = mapped_column(String(10), default="sk")

    expressions: Mapped[list["LegalExpression"]] = relationship(
        back_populates="instrument", foreign_keys="LegalExpression.instrument_id"
    )
    provisions: Mapped[list["Provision"]] = relationship(back_populates="instrument")

    __table_args__ = ({"comment": "legal_instrument – work v zmysle ADR-0002"},)


class LegalExpression(Base, UUIDPK, Timestamped):
    """Jazyková/časová verzia predpisu (znenie účinné od–do)."""

    __tablename__ = "legal_expression"

    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legal_instrument.id"))
    language: Mapped[str] = mapped_column(String(10), default="sk")
    effective_from: Mapped[date]
    effective_to: Mapped[date | None] = mapped_column(Date)
    is_consolidated: Mapped[bool] = mapped_column(default=False)
    consolidation_disclaimer: Mapped[str | None] = mapped_column(Text)
    amended_by_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("legal_instrument.id")
    )

    instrument: Mapped["LegalInstrument"] = relationship(
        back_populates="expressions", foreign_keys=[instrument_id]
    )
    manifestations: Mapped[list["LegalManifestation"]] = relationship(
        back_populates="expression"
    )


class LegalManifestation(Base, UUIDPK, Timestamped):
    """Konkrétny nosič/formát jednej expression (PDF v Zbierke, HTML na Slov-Lex)."""

    __tablename__ = "legal_manifestation"

    expression_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legal_expression.id"))
    format: Mapped[str] = mapped_column(String(20))  # pdf, html, xml, docx
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_document.id")
    )
    url: Mapped[str | None] = mapped_column(Text)
    is_official: Mapped[bool] = mapped_column(default=True)

    expression: Mapped["LegalExpression"] = relationship(back_populates="manifestations")


class LegalVersion(Base, UUIDPK, Timestamped):
    """Explicitný interval platnosti/účinnosti pre point-in-time dotazy."""

    __tablename__ = "legal_version"

    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legal_instrument.id"))
    version_label: Mapped[str] = mapped_column(String(100))
    valid_from: Mapped[date]
    valid_to: Mapped[date | None] = mapped_column(Date)
    effective_from: Mapped[date]
    effective_to: Mapped[date | None] = mapped_column(Date)
    changed_by_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("legal_instrument.id")
    )
    notes: Mapped[str | None] = mapped_column(Text)
