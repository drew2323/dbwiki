"""remove_legacy_auth_columns

Revision ID: b4b145ee527e
Revises: 9fd9c9e08109
Create Date: 2025-11-13 11:20:11.256729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4b145ee527e'
down_revision: Union[str, None] = '9fd9c9e08109'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_users_google_id', table_name='users')

    # Drop columns
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'google_id')


def downgrade() -> None:
    # Add columns back
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))

    # Re-create indexes
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)
