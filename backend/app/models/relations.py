"""Právny graf (sekcia 8) a citácie."""
import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPK

RELATION_TYPES = (
    "meni",
    "doplna",
    "zrusuje",
    "vykonava",
    "splnomocnuje",
    "odkazuje_na",
    "definuje_pojem_pre",
    "preberá_pravo_eu",
    "vykonava_pravo_eu",
    "suvisi_s",
    "bol_predmetom_sudneho_preskumania",
    "deroguje",
    "je_lex_specialis_voci",
    "je_lex_generalis_voci",
    "obsahuje_prechodnu_upravu_pre",
)


class LegalRelation(Base, UUIDPK, Timestamped):
    """Hrana právneho grafu medzi dvomi predpismi alebo ustanoveniami."""

    __tablename__ = "legal_relation"

    relation_type: Mapped[str] = mapped_column(String(50))
    source_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("legal_instrument.id")
    )
    source_provision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("provision.id"))
    target_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("legal_instrument.id")
    )
    target_provision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("provision.id"))
    target_eu_act_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("eu_act.id"))
    target_court_decision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("court_decision.id")
    )
    confidence: Mapped[str] = mapped_column(String(20), default="explicit")
    # explicit (priamo v texte) | derived (analyticky odvodené)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    evidence_text: Mapped[str | None] = mapped_column(Text)


class Citation(Base, UUIDPK, Timestamped):
    """Konkrétny výskyt odkazu na iný predpis/ustanovenie v texte, normalizovaný."""

    __tablename__ = "citation"

    source_provision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provision.id"))
    raw_text: Mapped[str] = mapped_column(Text)  # napr. "§31 ods. 2"
    normalized_reference: Mapped[str] = mapped_column(String(255))
    target_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("legal_instrument.id")
    )
    target_provision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("provision.id"))
    resolved: Mapped[bool] = mapped_column(default=False)
