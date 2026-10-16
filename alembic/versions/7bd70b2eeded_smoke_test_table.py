"""smoke test table

Revision ID: 7bd70b2eeded
Revises: 
Create Date: 2026-09-15 13:58:30.605896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7bd70b2eeded'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass