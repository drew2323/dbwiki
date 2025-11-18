"""merge heads

Revision ID: 966836cd73b4
Revises: a1b2c3d4e5f6, b4b145ee527e
Create Date: 2025-11-18 12:17:55.470626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '966836cd73b4'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'b4b145ee527e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
