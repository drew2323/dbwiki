"""
CMS spaces database models with junction table support.
This allows users to belong to multiple spaces with different roles in each.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Space(Base):
    """
    Top-level content container in the CMS.
    Each space can have multiple users with different roles.
    """
    __tablename__ = "spaces"

    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String(100), unique=True, nullable=False)  # URL-safe short code
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    visibility = Column(String(20), default='private', nullable=False)  # 'private' | 'public'
    home_page_id = Column(String(36), nullable=True)  # Set later by pages module
    created_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user_space_roles = relationship("UserSpaceRole", back_populates="space")
    creator = relationship("User", foreign_keys=[created_by])


class Role(Base):
    """
    Global roles that can be assigned to users in different spaces.
    Examples: superuser, admin, edit, read
    """
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)  # Globally unique
    permissions = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user_space_roles = relationship("UserSpaceRole", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)

    # Profile
    name = Column(String(255), nullable=True)
    picture = Column(String(500), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False, index=True)

    # Verification tokens
    verification_token = Column(String(255), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    space_roles = relationship("UserSpaceRole", back_populates="user", cascade="all, delete-orphan")
    auth_identities = relationship("AuthIdentity", back_populates="user", cascade="all, delete-orphan")


class UserSpaceRole(Base):
    """
    Junction table that allows users to have different roles in different spaces.

    Example:
        User John → Space A (role: Admin)
        User John → Space B (role: Viewer)
        User John → Space C (role: Editor)
    """
    __tablename__ = "user_space_roles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    space_id = Column(String, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    # Track if this association is active
    is_active = Column(Boolean, default=True, nullable=False)

    # When was this association created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Optional: Expiration date for temporary access
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="space_roles")
    space = relationship("Space", back_populates="user_space_roles")
    role = relationship("Role", back_populates="user_space_roles")

    # Ensure unique user-space combination
    __table_args__ = (
        UniqueConstraint('user_id', 'space_id', name='uq_user_space'),
    )


class AuthIdentity(Base):
    """
    Links users to authentication providers (password, Google, GitHub, OIDC, etc.).
    Supports multiple identities per user for SSO and passwordless authentication.

    Examples:
        User A → password provider (email/password login)
        User A → google provider (can also login with Google)
        User B → github provider (GitHub login only)
    """
    __tablename__ = "auth_identities"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Provider type: 'password', 'google', 'github', 'oidc', etc.
    provider = Column(Text, nullable=False)

    # Provider-specific user identifier (e.g., Google sub, GitHub user ID, email for password)
    provider_subject = Column(Text, nullable=False, index=True)

    # Provider-specific metadata (tokens, claims, profile data, password hash, etc.)
    provider_metadata = Column("metadata", JSON, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="auth_identities")

    # Ensure unique provider + subject combination
    __table_args__ = (
        UniqueConstraint('provider', 'provider_subject', name='uq_provider_subject'),
    )


