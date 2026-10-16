"""add job priority

Revision ID: 69934eb1cb2a
Revises: 4b0949d68497
Create Date: 2026-10-04 02:52:36.529930

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "69934eb1cb2a"
down_revision: Union[str, None] = "4b0949d68497"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="NORMAL",
        ),
    )

    op.alter_column(
        "jobs",
        "priority",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("jobs", "priority")