"""Štrukturálne jednotky predpisu a novelizačné body."""
import uuid
from datetime import date

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamped, UUIDPK

# Poradie zodpovedá sekcii 6.3 zadania.
PROVISION_UNIT_TYPES = (
    "cast",
    "hlava",
    "diel",
    "oddiel",
    "paragraf",
    "odsek",
    "pismeno",
    "bod",
    "veta",
    "priloha",
    "polozka_prilohy",
    "nadpis",
    "poznamka_pod_ciarou",
)


class Provision(Base, UUIDPK, Timestamped):
    """Jedna štrukturálna jednotka predpisu (strom cez parent_id)."""

    __tablename__ = "provision"

    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legal_instrument.id"))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("provision.id"))
    unit_type: Mapped[str] = mapped_column(String(30))
    order_index: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(100))  # napr. "§ 31", "ods. 2", "písm. c)"
    hierarchical_path: Mapped[str] = mapped_column(Text)  # napr. "§31/ods2/pismc"
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_document.id")
    )
    source_locator: Mapped[str | None] = mapped_column(Text)  # napr. xpath/offset v zdroji

    instrument: Mapped["LegalInstrument"] = relationship(back_populates="provisions")  # noqa: F821
    parent: Mapped["Provision | None"] = relationship(remote_side="Provision.id")
    versions: Mapped[list["ProvisionVersion"]] = relationship(back_populates="provision")


class ProvisionVersion(Base, UUIDPK, Timestamped):
    """Znenie ustanovenia platné v danom časovom intervale."""

    __tablename__ = "provision_version"

    provision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provision.id"))
    text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64))  # sha256
    effective_from: Mapped[date]
    effective_to: Mapped[date | None] = mapped_column(default=None)
    amended_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("amendment.id"))
    is_repealed: Mapped[bool] = mapped_column(default=False)

    provision: Mapped["Provision"] = relationship(back_populates="versions")


class Amendment(Base, UUIDPK, Timestamped):
    """Novelizačný bod – inštrukcia na zmenu iného predpisu/ustanovenia."""

    __tablename__ = "amendment"

    amending_instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("legal_instrument.id")
    )
    target_instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legal_instrument.id"))
    target_provision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("provision.id"))
    point_number: Mapped[int] = mapped_column(Integer)
    operation: Mapped[str] = mapped_column(String(20))  # nahradit | vlozit | vypustit | doplnit
    instruction_text: Mapped[str] = mapped_column(Text)
    new_text: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date | None] = mapped_column(default=None)
    application_status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | applied | conflict
    application_note: Mapped[str | None] = mapped_column(Text)


class TermDefinition(Base, UUIDPK, Timestamped):
    """Definícia pojmu s rozsahom platnosti (kto ho definuje a pre čo platí)."""

    __tablename__ = "term_definition"

    term: Mapped[str] = mapped_column(String(255))
    defining_provision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provision.id"))
    definition_text: Mapped[str] = mapped_column(Text)
    scope_note: Mapped[str | None] = mapped_column(Text)  # napr. "iba pre účely tohto zákona"
    effective_from: Mapped[date | None] = mapped_column(default=None)
    effective_to: Mapped[date | None] = mapped_column(default=None)
