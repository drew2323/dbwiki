"""seed_default_tenant_and_roles

Revision ID: 2f91a66458ae
Revises: 40af09bfa370
Create Date: 2025-11-11 11:33:30.165195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '2f91a66458ae'
down_revision: Union[str, None] = '40af09bfa370'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create default tenant
    default_tenant_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO tenants (id, name, subdomain, is_active)
        VALUES ('{default_tenant_id}', 'Default', NULL, true)
    """)

    # Create roles
    admin_role_id = str(uuid.uuid4())
    editor_role_id = str(uuid.uuid4())
    viewer_role_id = str(uuid.uuid4())

    op.execute(f"""
        INSERT INTO roles (id, name, permissions, tenant_id)
        VALUES
        ('{admin_role_id}', 'Admin', '{{"user_management": true, "content_edit": true, "content_delete": true, "settings": true}}', '{default_tenant_id}'),
        ('{editor_role_id}', 'Editor', '{{"content_edit": true, "content_delete": false}}', '{default_tenant_id}'),
        ('{viewer_role_id}', 'Viewer', '{{"content_view": true}}', '{default_tenant_id}')
    """)


def downgrade() -> None:
    # Remove seed data
    op.execute("DELETE FROM roles WHERE name IN ('Admin', 'Editor', 'Viewer')")
    op.execute("DELETE FROM tenants WHERE name = 'Default'")
