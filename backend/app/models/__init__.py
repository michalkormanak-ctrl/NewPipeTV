"""Registrácia všetkých modelov do SQLAlchemy metadát (pre Alembic autogenerate)."""
from app.models.base import Base
from app.models.drafting import DraftingProject, DraftVersion
from app.models.external import CourtDecision, EuAct
from app.models.ingestion import IngestionRun, SourceDocument, ValidationResult
from app.models.legal import (
    LegalExpression,
    LegalInstrument,
    LegalManifestation,
    LegalVersion,
)
from app.models.process import (
    Comment,
    CommentEvaluation,
    LegislativeProcess,
    ProcessDocument,
)
from app.models.provisions import Amendment, Provision, ProvisionVersion, TermDefinition
from app.models.relations import Citation, LegalRelation
from app.models.security import AuditEvent, User

__all__ = [
    "Base",
    "LegalInstrument",
    "LegalExpression",
    "LegalManifestation",
    "LegalVersion",
    "Provision",
    "ProvisionVersion",
    "Amendment",
    "TermDefinition",
    "LegalRelation",
    "Citation",
    "LegislativeProcess",
    "ProcessDocument",
    "Comment",
    "CommentEvaluation",
    "CourtDecision",
    "EuAct",
    "SourceDocument",
    "IngestionRun",
    "ValidationResult",
    "DraftingProject",
    "DraftVersion",
    "User",
    "AuditEvent",
]
