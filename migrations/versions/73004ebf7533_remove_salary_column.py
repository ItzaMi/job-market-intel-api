"""remove salary column

Revision ID: 73004ebf7533
Revises: b0bc2f58b0f8
Create Date: 2026-07-15 16:12:13.060162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '73004ebf7533'
down_revision: Union[str, Sequence[str], None] = 'b0bc2f58b0f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('job', 'salary')

def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('job', sa.Column('salary', sa.Integer(), nullable=False, server_default="0"))
    op.alter_column('job', 'salary', server_default=None)
