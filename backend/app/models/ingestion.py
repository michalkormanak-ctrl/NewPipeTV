"""Evidencia originálov, ingest behov a nálezov validácie (bod 5.3, sekcia 17)."""
import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPK, utcnow


class SourceDocument(Base, UUIDPK, Timestamped):
    """Nemenná evidencia jedného stiahnutého originálu. Nikdy sa neprepisuje."""

    __tablename__ = "source_document"

    source_url: Mapped[str] = mapped_column(Text)
    source_identifier: Mapped[str | None] = mapped_column(String(255))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    document_type: Mapped[str] = mapped_column(String(50))
    promulgation_date: Mapped[date | None] = mapped_column(default=None)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    integrity_check_result: Mapped[str] = mapped_column(String(20), default="unverified")
    # ok | mismatch | unverified
    legal_status_note: Mapped[str] = mapped_column(
        String(50), default="informative"
    )  # informative | authoritative
    storage_path: Mapped[str] = mapped_column(Text)  # cesta v object storage (GCS/lokálne)
    ingestion_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ingestion_run.id"))


class IngestionRun(Base, UUIDPK, Timestamped):
    __tablename__ = "ingestion_run"

    source_name: Mapped[str] = mapped_column(String(100))  # slov-lex, eur-lex, nrsr
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running")
    # running | success | partial_failure | failed
    items_discovered: Mapped[int] = mapped_column(default=0)
    items_new: Mapped[int] = mapped_column(default=0)
    items_changed: Mapped[int] = mapped_column(default=0)
    items_failed: Mapped[int] = mapped_column(default=0)
    error_log: Mapped[str | None] = mapped_column(Text)


class ValidationResult(Base, UUIDPK, Timestamped):
    """Nález ľubovoľnej kontroly/validátora (legislatívnej, ústavnej, red-team, konsolidačnej)."""

    __tablename__ = "validation_result"

    check_type: Mapped[str] = mapped_column(String(50))
    # legislativny | ustavny | vecny | eu | udaje_bezpecnost | vykonatelnost | red_team | konsolidacia
    severity: Mapped[str] = mapped_column(String(20))  # kriticke | zavazne | stredne | lt | odporucanie
    subject_type: Mapped[str] = mapped_column(String(50))  # draft_version | amendment | instrument
    subject_id: Mapped[uuid.UUID]
    finding: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | fixed | accepted_risk
