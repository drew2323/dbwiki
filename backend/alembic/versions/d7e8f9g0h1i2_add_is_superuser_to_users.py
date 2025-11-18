"""add is_superuser to users

Revision ID: d7e8f9g0h1i2
Revises: c1d2e3f4g5h6
Create Date: 2025-11-18 14:00:00.000000

This migration adds the is_superuser boolean field to the users table.
Superusers have implicit access to all spaces and can manage all users.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7e8f9g0h1i2'
down_revision = 'c1d2e3f4g5h6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_superuser column to users table
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'))

    # Create index for faster superuser lookups
    op.create_index('ix_users_is_superuser', 'users', ['is_superuser'])

    # Set superuser flag for initial admin user
    op.execute(
        "UPDATE users SET is_superuser = true WHERE email = 'davidbrazda61@gmail.com'"
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_users_is_superuser', table_name='users')

    # Drop column
    op.drop_column('users', 'is_superuser')
