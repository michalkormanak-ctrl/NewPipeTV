"""RBAC a audit (sekcia 16.2)."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPK, utcnow

WORKSPACE_TYPES = (
    "public_legislation",
    "internal_unclassified",
    "personal_project",
    "sensitive_restricted",
)


class User(Base, UUIDPK, Timestamped):
    __tablename__ = "app_user"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(255))
    roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditEvent(Base, UUIDPK, Timestamped):
    """Každý prístup, export a LLM volanie musí byť zapísané (sekcia 16.2, 10.1)."""

    __tablename__ = "audit_event"

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("app_user.id"))
    action: Mapped[str] = mapped_column(String(100))
    # query | export | draft_created | validation_run | login | permission_denied
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(255))
    workspace: Mapped[str] = mapped_column(String(50), default="public_legislation")
    model_used: Mapped[str | None] = mapped_column(String(100))
    prompt_hash: Mapped[str | None] = mapped_column(String(64))
    sources_used: Mapped[list | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    result: Mapped[str] = mapped_column(String(20), default="success")  # success | denied | error
    details: Mapped[str | None] = mapped_column(Text)
