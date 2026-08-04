"""Externé právne zdroje: judikatúra a právo EÚ."""
import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPK


class CourtDecision(Base, UUIDPK, Timestamped):
    __tablename__ = "court_decision"

    court: Mapped[str] = mapped_column(String(255))  # napr. "Ústavný súd SR"
    case_number: Mapped[str] = mapped_column(String(100))
    decision_date: Mapped[date | None] = mapped_column(default=None)
    summary: Mapped[str | None] = mapped_column(Text)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_document.id")
    )
    source_url: Mapped[str | None] = mapped_column(Text)


class EuAct(Base, UUIDPK, Timestamped):
    __tablename__ = "eu_act"

    celex_number: Mapped[str] = mapped_column(String(50), unique=True)
    eli_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text)
    act_type: Mapped[str] = mapped_column(String(50))  # nariadenie | smernica | rozhodnutie
    date_of_document: Mapped[date | None] = mapped_column(default=None)
    date_entry_into_force: Mapped[date | None] = mapped_column(default=None)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_document.id")
    )
