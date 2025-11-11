"""remove_legacy_fields

Revision ID: 1bc2737acf05
Revises: cad78ee196ed
Create Date: 2025-11-11 14:30:00.000000

Removes:
1. user_sessions table (not currently used, sessions tracked client-side)
2. users.role_id column (deprecated, now using UserTenantRole junction table)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1bc2737acf05'
down_revision: Union[str, None] = 'cad78ee196ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove user_sessions table (not currently used)
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_table('user_sessions')

    # Remove role_id from users table (deprecated, now in UserTenantRole)
    op.drop_constraint('users_role_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'role_id')


def downgrade() -> None:
    # Restore role_id to users table
    op.add_column('users', sa.Column('role_id', sa.VARCHAR(), nullable=True))
    op.create_foreign_key('users_role_id_fkey', 'users', 'roles', ['role_id'], ['id'])

    # Populate role_id from UserTenantRole (take default tenant role)
    op.execute("""
        UPDATE users u
        SET role_id = (
            SELECT utr.role_id
            FROM user_tenant_roles utr
            WHERE utr.user_id = u.id
            AND utr.tenant_id = u.default_tenant_id
            LIMIT 1
        )
    """)

    # Recreate user_sessions table
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
