"""empty message

Revision ID: b0bc2f58b0f8
Revises: 20535cb5538c
Create Date: 2026-07-15 16:04:11.704483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b0bc2f58b0f8'
down_revision: Union[str, Sequence[str], None] = '20535cb5538c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("ix_job_created_at", "job", ["created_at"])
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_job_created_at", table_name="job")
    pass
