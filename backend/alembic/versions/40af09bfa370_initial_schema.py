"""initial_schema

Revision ID: 40af09bfa370
Revises: 
Create Date: 2025-11-11 11:33:09.015783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40af09bfa370'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenants table
    op.create_table('tenants',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('subdomain', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('subdomain')
    )

    # Create roles table
    op.create_table('roles',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('permissions', sa.JSON(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create users table
    op.create_table('users',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('google_id', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('picture', sa.String(length=500), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('verification_token', sa.String(length=255), nullable=True),
    sa.Column('reset_token', sa.String(length=255), nullable=True),
    sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('role_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username'),
    sa.UniqueConstraint('google_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('tenants')
