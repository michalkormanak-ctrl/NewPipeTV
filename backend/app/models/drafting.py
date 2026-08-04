"""Režim LEGISLATÍVNY_PROJEKT (sekcia 11)."""
import uuid
from datetime import date

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPK


class DraftingProject(Base, UUIDPK, Timestamped):
    __tablename__ = "drafting_project"

    title: Mapped[str] = mapped_column(Text)
    user_instruction: Mapped[str] = mapped_column(Text)
    interpreted_goal: Mapped[str | None] = mapped_column(Text)
    working_assumptions: Mapped[list | None] = mapped_column(JSON)
    target_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("legal_instrument.id")
    )
    requested_effective_date: Mapped[date | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(String(30), default="interpreting")
    # interpreting | analyzing | drafting | reviewing | ready | blocked
    created_by: Mapped[str] = mapped_column(String(255))


class DraftVersion(Base, UUIDPK, Timestamped):
    __tablename__ = "draft_version"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drafting_project.id"))
    version_number: Mapped[int]
    step: Mapped[str] = mapped_column(String(50))
    # varianty | paragrafove_znenie | novelizacne_body | konsolidacia | sprievodne_dokumenty
    content: Mapped[str] = mapped_column(Text)
    content_format: Mapped[str] = mapped_column(String(20), default="markdown")
    is_recommended_variant: Mapped[bool] = mapped_column(default=False)
