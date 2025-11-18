"""remove space_id from roles make global

Revision ID: c1d2e3f4g5h6
Revises: 966836cd73b4
Create Date: 2025-11-18 12:00:00.000000

This migration transforms roles from space-specific to global entities:
1. Removes space_id column from roles table
2. Makes role names globally unique
3. Seeds default global roles (superuser, admin, edit, read)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = '966836cd73b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Drop foreign key constraint on roles.space_id
    op.drop_constraint('roles_space_id_fkey', 'roles', type_='foreignkey')

    # Step 2: Drop the space_id column from roles table
    op.drop_column('roles', 'space_id')

    # Step 3: Create unique constraint on role name (globally unique)
    op.create_unique_constraint('uq_roles_name', 'roles', ['name'])

    # Step 4: Seed default global roles
    roles_table = sa.table('roles',
        sa.column('id', sa.String),
        sa.column('name', sa.String),
        sa.column('permissions', sa.JSON),
        sa.column('created_at', sa.DateTime)
    )

    # Default roles with their permissions
    default_roles = [
        {
            'id': str(uuid.uuid4()),
            'name': 'superuser',
            'permissions': {
                'system_admin': True,
                'all_spaces': True,
                'manage_users': True,
                'manage_roles': True,
                'manage_spaces': True
            },
            'created_at': datetime.utcnow()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'admin',
            'permissions': {
                'manage_users': True,
                'manage_content': True,
                'manage_settings': True,
                'edit_content': True,
                'delete_content': True,
                'view_content': True
            },
            'created_at': datetime.utcnow()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'edit',
            'permissions': {
                'create_content': True,
                'edit_content': True,
                'delete_own': True,
                'view_content': True
            },
            'created_at': datetime.utcnow()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'read',
            'permissions': {
                'view_content': True
            },
            'created_at': datetime.utcnow()
        }
    ]

    op.bulk_insert(roles_table, default_roles)


def downgrade() -> None:
    # Step 1: Delete seeded roles
    op.execute("DELETE FROM roles WHERE name IN ('superuser', 'admin', 'edit', 'read')")

    # Step 2: Drop unique constraint on name
    op.drop_constraint('uq_roles_name', 'roles', type_='unique')

    # Step 3: Add back space_id column
    op.add_column('roles', sa.Column('space_id', sa.String(length=36), nullable=True))

    # Step 4: Recreate foreign key constraint
    op.create_foreign_key('roles_space_id_fkey', 'roles', 'spaces', ['space_id'], ['id'], ondelete='CASCADE')

    # Note: After downgrade, space_id will be NULL for all roles
    # Manual intervention needed to assign roles to spaces
