"""migrate_existing_auth_data

Revision ID: 9fd9c9e08109
Revises: 44817ce6f7eb
Create Date: 2025-11-13 11:19:32.323763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import uuid


# revision identifiers, used by Alembic.
revision: str = '9fd9c9e08109'
down_revision: Union[str, None] = '44817ce6f7eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migrate existing authentication data from users table to auth_identities table.
    - Users with password_hash → create 'password' identity (provider_subject = email)
    - Users with google_id → create 'google' identity (provider_subject = google_id)
    """
    connection = op.get_bind()

    # Get all users with existing auth data
    users = connection.execute(
        sa.text("SELECT id, email, password_hash, google_id FROM users")
    ).fetchall()

    for user in users:
        user_id, email, password_hash, google_id = user

        # Migrate password authentication
        if password_hash:
            identity_id = str(uuid.uuid4())
            import json
            metadata_json = json.dumps({"password_hash": password_hash})
            connection.execute(
                sa.text("""
                    INSERT INTO auth_identities (id, user_id, provider, provider_subject, metadata, created_at)
                    VALUES (:id, :user_id, 'password', :provider_subject, CAST(:metadata_json AS jsonb), NOW())
                """),
                {
                    "id": identity_id,
                    "user_id": user_id,
                    "provider_subject": email,
                    "metadata_json": metadata_json
                }
            )

        # Migrate Google OAuth authentication
        if google_id:
            identity_id = str(uuid.uuid4())
            connection.execute(
                sa.text("""
                    INSERT INTO auth_identities (id, user_id, provider, provider_subject, metadata, created_at)
                    VALUES (:id, :user_id, 'google', :provider_subject, '{}', NOW())
                """),
                {
                    "id": identity_id,
                    "user_id": user_id,
                    "provider_subject": google_id
                }
            )


def downgrade() -> None:
    """
    Restore authentication data from auth_identities back to users table.
    """
    connection = op.get_bind()

    # Get all auth identities
    identities = connection.execute(
        sa.text("SELECT user_id, provider, provider_subject, metadata FROM auth_identities")
    ).fetchall()

    for identity in identities:
        user_id, provider, provider_subject, metadata = identity

        if provider == 'password':
            # Extract password_hash from metadata
            password_hash = metadata.get('password_hash') if metadata else None
            if password_hash:
                connection.execute(
                    sa.text("UPDATE users SET password_hash = :password_hash WHERE id = :user_id"),
                    {"password_hash": password_hash, "user_id": user_id}
                )

        elif provider == 'google':
            connection.execute(
                sa.text("UPDATE users SET google_id = :google_id WHERE id = :user_id"),
                {"google_id": provider_subject, "user_id": user_id}
            )

    # Clear all auth_identities
    connection.execute(sa.text("DELETE FROM auth_identities"))
