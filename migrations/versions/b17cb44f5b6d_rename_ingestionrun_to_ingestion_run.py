"""rename ingestionrun to ingestion_run

Revision ID: b17cb44f5b6d
Revises: f748381b4874
Create Date: 2026-07-13 17:12:59.107107

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b17cb44f5b6d'
down_revision: Union[str, Sequence[str], None] = 'f748381b4874'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("ingestionrun", "ingestion_run")


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table("ingestion_run", "ingestionrun")
