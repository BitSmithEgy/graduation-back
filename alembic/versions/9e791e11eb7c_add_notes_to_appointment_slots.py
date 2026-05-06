"""add notes to appointment_slots

Revision ID: 9e791e11eb7c
Revises: 
Create Date: 2026-05-01 19:38:18.080998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '9e791e11eb7c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('appointment_slots', sa.Column('notes', sa.String(255), nullable=True))

def downgrade() -> None:
    op.drop_column('appointment_slots', 'notes')