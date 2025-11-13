"""
CRUD operations for AuthIdentity model.
Handles authentication provider management for users.
"""
from sqlalchemy.orm import Session
from app.models.db_models import AuthIdentity
from typing import Optional, List
import uuid


def get_identity_by_provider_subject(
    db: Session,
    provider: str,
    provider_subject: str
) -> Optional[AuthIdentity]:
    """Get an auth identity by provider and provider_subject (e.g., Google sub, email)"""
    return db.query(AuthIdentity).filter(
        AuthIdentity.provider == provider,
        AuthIdentity.provider_subject == provider_subject
    ).first()


def get_identities_by_user_id(db: Session, user_id: str) -> List[AuthIdentity]:
    """Get all auth identities for a user"""
    return db.query(AuthIdentity).filter(AuthIdentity.user_id == user_id).all()


def get_identity_by_user_and_provider(
    db: Session,
    user_id: str,
    provider: str
) -> Optional[AuthIdentity]:
    """Get a specific identity for a user by provider type"""
    return db.query(AuthIdentity).filter(
        AuthIdentity.user_id == user_id,
        AuthIdentity.provider == provider
    ).first()


def create_identity(
    db: Session,
    user_id: str,
    provider: str,
    provider_subject: str,
    metadata: dict = None
) -> AuthIdentity:
    """
    Create a new auth identity for a user.

    Args:
        user_id: The user's ID
        provider: Provider type (e.g., 'password', 'google', 'github')
        provider_subject: Provider-specific identifier (email for password, sub for OAuth)
        metadata: Additional provider-specific data (password_hash, tokens, claims, etc.)
    """
    identity = AuthIdentity(
        id=str(uuid.uuid4()),
        user_id=user_id,
        provider=provider,
        provider_subject=provider_subject,
        provider_metadata=metadata or {}
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)
    return identity


def update_identity_metadata(
    db: Session,
    identity_id: str,
    metadata: dict
) -> Optional[AuthIdentity]:
    """Update the metadata for an auth identity (e.g., refresh tokens, update password_hash)"""
    identity = db.query(AuthIdentity).filter(AuthIdentity.id == identity_id).first()
    if identity:
        identity.provider_metadata = metadata
        db.commit()
        db.refresh(identity)
    return identity


def delete_identity(db: Session, identity_id: str) -> bool:
    """Delete an auth identity"""
    identity = db.query(AuthIdentity).filter(AuthIdentity.id == identity_id).first()
    if identity:
        db.delete(identity)
        db.commit()
        return True
    return False


def link_provider_to_user(
    db: Session,
    user_id: str,
    provider: str,
    provider_subject: str,
    metadata: dict = None
) -> Optional[AuthIdentity]:
    """
    Link a new authentication provider to an existing user.
    Returns None if the provider+subject combination already exists.
    """
    # Check if this provider identity already exists
    existing = get_identity_by_provider_subject(db, provider, provider_subject)
    if existing:
        return None

    return create_identity(db, user_id, provider, provider_subject, metadata)
