"""add_multi_tenant_support

Revision ID: cad78ee196ed
Revises: 2f91a66458ae
Create Date: 2025-11-11 12:47:20.824040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cad78ee196ed'
down_revision: Union[str, None] = '2f91a66458ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create new junction table for multi-tenant support
    op.create_table(
        'user_tenant_roles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('role_id', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant')
    )
    op.create_index(op.f('ix_user_tenant_roles_user_id'), 'user_tenant_roles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_tenant_roles_tenant_id'), 'user_tenant_roles', ['tenant_id'], unique=False)

    # Step 2: Create user sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('current_tenant_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['current_tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)

    # Step 3: Rename tenant_id to default_tenant_id in users table
    op.alter_column('users', 'tenant_id', new_column_name='default_tenant_id')

    # Step 4: Migrate existing data - copy user/tenant/role relationships to junction table
    # This will be done in a data migration step
    op.execute("""
        INSERT INTO user_tenant_roles (id, user_id, tenant_id, role_id, is_active, created_at)
        SELECT
            gen_random_uuid()::text,
            id,
            default_tenant_id,
            role_id,
            true,
            created_at
        FROM users
        WHERE role_id IS NOT NULL
    """)

    # Step 5: Make role_id nullable in users table (it's now in junction table)
    op.alter_column('users', 'role_id',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    # Step 1: Restore role_id as required in users table
    # First, populate it from junction table (take first role found)
    op.execute("""
        UPDATE users u
        SET role_id = (
            SELECT utr.role_id
            FROM user_tenant_roles utr
            WHERE utr.user_id = u.id
            AND utr.tenant_id = u.default_tenant_id
            LIMIT 1
        )
        WHERE role_id IS NULL
    """)

    op.alter_column('users', 'role_id',
               existing_type=sa.VARCHAR(),
               nullable=False)

    # Step 2: Rename back to tenant_id
    op.alter_column('users', 'default_tenant_id', new_column_name='tenant_id')

    # Step 3: Drop new tables
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_table('user_sessions')

    op.drop_index(op.f('ix_user_tenant_roles_tenant_id'), table_name='user_tenant_roles')
    op.drop_index(op.f('ix_user_tenant_roles_user_id'), table_name='user_tenant_roles')
    op.drop_table('user_tenant_roles')
