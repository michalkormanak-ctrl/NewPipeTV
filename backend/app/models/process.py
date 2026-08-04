"""Legislatívny proces (eLegislatíva) a pripomienky (sekcia 12)."""
import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPK


class LegislativeProcess(Base, UUIDPK, Timestamped):
    __tablename__ = "legislative_process"

    process_identifier: Mapped[str] = mapped_column(String(100), unique=True)
    departmental_number: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    submitter: Mapped[str | None] = mapped_column(String(255))
    gestor: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="unverified")
    date_started: Mapped[date | None] = mapped_column(default=None)
    date_closed: Mapped[date | None] = mapped_column(default=None)
    related_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("legal_instrument.id")
    )


class ProcessDocument(Base, UUIDPK, Timestamped):
    __tablename__ = "process_document"

    process_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legislative_process.id"))
    document_type: Mapped[str] = mapped_column(String(100))
    # predbezna_informacia | material | dovodova_sprava | dolozka | uznesenie | znenie
    title: Mapped[str] = mapped_column(Text)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_document.id")
    )


class Comment(Base, UUIDPK, Timestamped):
    __tablename__ = "comment"

    process_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legislative_process.id"))
    author: Mapped[str] = mapped_column(String(255))
    target_provision_label: Mapped[str | None] = mapped_column(String(255))
    comment_type: Mapped[str] = mapped_column(String(20))  # zasadna | obycajna | hromadna
    is_fundamental: Mapped[bool] = mapped_column(default=False)
    text: Mapped[str] = mapped_column(Text)
    proposed_wording: Mapped[str | None] = mapped_column(Text)
    justification: Mapped[str | None] = mapped_column(Text)
    thematic_category: Mapped[str | None] = mapped_column(String(255))
    legal_argument: Mapped[str | None] = mapped_column(Text)


class CommentEvaluation(Base, UUIDPK, Timestamped):
    __tablename__ = "comment_evaluation"

    comment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comment.id"), unique=True)
    result: Mapped[str] = mapped_column(String(30))
    # akceptovana | ciastocne_akceptovana | neakceptovana
    resolution_method: Mapped[str | None] = mapped_column(Text)
    final_wording: Mapped[str | None] = mapped_column(Text)
    dispute_resolution_outcome: Mapped[str | None] = mapped_column(Text)
