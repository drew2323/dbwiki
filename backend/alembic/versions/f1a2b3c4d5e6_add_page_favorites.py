"""add page favorites

Revision ID: f1a2b3c4d5e6
Revises: e1f2g3h4i5j6
Create Date: 2025-11-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e1f2g3h4i5j6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'page_favorites',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('page_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'page_id'),
    )
    op.create_index('ix_page_favorites_page_id', 'page_favorites', ['page_id'])


def downgrade() -> None:
    op.drop_index('ix_page_favorites_page_id', table_name='page_favorites')
    op.drop_table('page_favorites')
