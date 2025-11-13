"""add_auth_identities_table

Revision ID: 44817ce6f7eb
Revises: 1bc2737acf05
Create Date: 2025-11-13 11:19:13.801185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44817ce6f7eb'
down_revision: Union[str, None] = '1bc2737acf05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create auth_identities table
    op.create_table(
        'auth_identities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('provider_subject', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('provider', 'provider_subject', name='uq_provider_subject')
    )

    # Create indexes
    op.create_index(op.f('ix_auth_identities_user_id'), 'auth_identities', ['user_id'], unique=False)
    op.create_index(op.f('ix_auth_identities_provider_subject'), 'auth_identities', ['provider_subject'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_auth_identities_provider_subject'), table_name='auth_identities')
    op.drop_index(op.f('ix_auth_identities_user_id'), table_name='auth_identities')

    # Drop table
    op.drop_table('auth_identities')
