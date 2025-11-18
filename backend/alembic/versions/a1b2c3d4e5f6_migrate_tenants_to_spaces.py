"""migrate tenants to spaces

Revision ID: a1b2c3d4e5f6
Revises: 9fd9c9e08109
Create Date: 2025-11-18 10:00:00.000000

This migration transforms the multi-tenant architecture to a CMS spaces architecture:
1. Deletes all existing tenant data (clean slate)
2. Restructures tenants table → spaces table with new schema
3. Renames user_tenant_roles → user_space_roles
4. Updates all foreign keys and relationships
5. Removes default_tenant_id from users table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9fd9c9e08109'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Delete all data from dependent tables (cascade)
    op.execute('DELETE FROM user_tenant_roles')
    op.execute('DELETE FROM roles')

    # Step 2: Remove default_tenant_id from users table BEFORE deleting tenants
    # This is needed because users.default_tenant_id references tenants.id
    op.drop_constraint('users_tenant_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'default_tenant_id')

    # Step 3: Now safe to delete from tenants
    op.execute('DELETE FROM tenants')

    # Step 4: Drop foreign key constraints before restructuring
    # Drop constraints on user_tenant_roles that reference tenants
    op.drop_constraint('user_tenant_roles_tenant_id_fkey', 'user_tenant_roles', type_='foreignkey')
    # Drop constraints on roles that reference tenants
    op.drop_constraint('roles_tenant_id_fkey', 'roles', type_='foreignkey')

    # Step 5: Rename user_tenant_roles table to user_space_roles
    op.rename_table('user_tenant_roles', 'user_space_roles')

    # Step 6: Rename tenant_id column to space_id in user_space_roles
    op.alter_column('user_space_roles', 'tenant_id', new_column_name='space_id')

    # Step 7: Rename indexes and constraints in user_space_roles
    op.execute('ALTER INDEX ix_user_tenant_roles_user_id RENAME TO ix_user_space_roles_user_id')
    op.execute('ALTER INDEX ix_user_tenant_roles_tenant_id RENAME TO ix_user_space_roles_space_id')
    op.execute('ALTER TABLE user_space_roles RENAME CONSTRAINT uq_user_tenant TO uq_user_space')

    # Step 8: Rename tenant_id to space_id in roles table
    op.alter_column('roles', 'tenant_id', new_column_name='space_id')

    # Rename the table
    op.rename_table('tenants', 'spaces')

    # Remove old columns
    op.drop_column('spaces', 'subdomain')
    op.drop_column('spaces', 'is_active')

    # Add new columns
    op.add_column('spaces', sa.Column('key', sa.String(length=100), nullable=False))
    op.add_column('spaces', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('spaces', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='private'))
    op.add_column('spaces', sa.Column('home_page_id', sa.String(length=36), nullable=True))
    op.add_column('spaces', sa.Column('created_by', sa.String(length=36), nullable=False))

    # Add unique constraint on key
    op.create_unique_constraint('uq_spaces_key', 'spaces', ['key'])

    # Add foreign key for created_by
    op.create_foreign_key('spaces_created_by_fkey', 'spaces', 'users', ['created_by'], ['id'], ondelete='CASCADE')

    # Step 10: Recreate foreign keys with new table name
    op.create_foreign_key('user_space_roles_space_id_fkey', 'user_space_roles', 'spaces', ['space_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('roles_space_id_fkey', 'roles', 'spaces', ['space_id'], ['id'], ondelete='CASCADE')

    # Step 11: Drop user_sessions table if it exists (optional, as it's not heavily used)
    op.execute('DROP TABLE IF EXISTS user_sessions CASCADE')


def downgrade() -> None:
    # Recreate user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('current_tenant_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['current_tenant_id'], ['spaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])

    # Drop foreign keys
    op.drop_constraint('roles_space_id_fkey', 'roles', type_='foreignkey')
    op.drop_constraint('user_space_roles_space_id_fkey', 'user_space_roles', type_='foreignkey')
    op.drop_constraint('spaces_created_by_fkey', 'spaces', type_='foreignkey')

    # Drop unique constraint
    op.drop_constraint('uq_spaces_key', 'spaces', type_='unique')

    # Remove new columns
    op.drop_column('spaces', 'created_by')
    op.drop_column('spaces', 'home_page_id')
    op.drop_column('spaces', 'visibility')
    op.drop_column('spaces', 'description')
    op.drop_column('spaces', 'key')

    # Add back old columns
    op.add_column('spaces', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('spaces', sa.Column('subdomain', sa.String(length=100), nullable=True))
    op.create_unique_constraint('tenants_subdomain_key', 'spaces', ['subdomain'])

    # Rename spaces back to tenants
    op.rename_table('spaces', 'tenants')

    # Recreate foreign keys
    op.create_foreign_key('roles_tenant_id_fkey', 'roles', 'tenants', ['space_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_space_roles_tenant_id_fkey', 'user_space_roles', 'tenants', ['space_id'], ['id'], ondelete='CASCADE')

    # Rename space_id back to tenant_id in roles
    op.alter_column('roles', 'space_id', new_column_name='tenant_id')

    # Rename indexes and constraints
    op.execute('ALTER TABLE user_space_roles RENAME CONSTRAINT uq_user_space TO uq_user_tenant')
    op.execute('ALTER INDEX ix_user_space_roles_space_id RENAME TO ix_user_tenant_roles_tenant_id')
    op.execute('ALTER INDEX ix_user_space_roles_user_id RENAME TO ix_user_tenant_roles_user_id')

    # Rename space_id back to tenant_id
    op.alter_column('user_space_roles', 'space_id', new_column_name='tenant_id')

    # Rename table back
    op.rename_table('user_space_roles', 'user_tenant_roles')

    # Add back default_tenant_id to users
    op.add_column('users', sa.Column('default_tenant_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('users_tenant_id_fkey', 'users', 'tenants', ['default_tenant_id'], ['id'])
