"""Úvodná schéma - všetky entity z docs/data-model.md.

Poznámka k implementácii: namiesto ručne prepísaných `op.create_table`
príkazov pre 22 entít (vysoké riziko preklepu/rozchádzania sa s ORM
modelmi) táto úvodná migrácia vytvára schému priamo z
`app.models.Base.metadata`, čo je jediný zdroj pravdy pre štruktúru tabuliek.
Budúce migrácie (od druhej) by už mali používať štandardné
`alembic revision --autogenerate` s explicitnými `op.*` príkazmi.

Revision ID: 0001
Revises:
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op

from app.models import Base

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
