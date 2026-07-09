"""replace str for uuid on id

Revision ID: 92e9a7131630
Revises: 8cecf8b6d6f5
Create Date: 2026-07-09 17:09:44.727137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '92e9a7131630'
down_revision: Union[str, Sequence[str], None] = '8cecf8b6d6f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "job",
        "id",
        existing_type=sa.VARCHAR(),
        type_=sa.Uuid(),
        existing_nullable=False,
        postgresql_using="id::uuid",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "job",
        "id",
        existing_type=sa.Uuid(),
        type_=sa.VARCHAR(),
        existing_nullable=False,
        postgresql_using="id::varchar",
    )
