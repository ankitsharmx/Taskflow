"""smoke test table

Revision ID: dbb0845c5d22
Revises: 7bd70b2eeded
Create Date: 2026-09-15 14:04:34.683890

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'dbb0845c5d22'
down_revision: Union[str, None] = '7bd70b2eeded'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass