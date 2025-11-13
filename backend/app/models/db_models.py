"""
Multi-tenant database models with junction table support.
This allows users to belong to multiple tenants with different roles in each.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    roles = relationship("Role", back_populates="tenant")
    user_tenant_roles = relationship("UserTenantRole", back_populates="tenant")


class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    permissions = Column(JSON, default=dict, nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    user_tenant_roles = relationship("UserTenantRole", back_populates="role")


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

    # Verification tokens
    verification_token = Column(String(255), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    # Default/Home tenant (the tenant user was created in)
    default_tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    default_tenant = relationship("Tenant", foreign_keys=[default_tenant_id])
    tenant_roles = relationship("UserTenantRole", back_populates="user", cascade="all, delete-orphan")
    auth_identities = relationship("AuthIdentity", back_populates="user", cascade="all, delete-orphan")


class UserTenantRole(Base):
    """
    Junction table that allows users to have different roles in different tenants.

    Example:
        User John → Tenant A (role: Admin)
        User John → Tenant B (role: Viewer)
        User John → Tenant C (role: Editor)
    """
    __tablename__ = "user_tenant_roles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    # Track if this is the user's primary/active tenant
    is_active = Column(Boolean, default=True, nullable=False)

    # When was this association created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Optional: Expiration date for temporary access
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="tenant_roles")
    tenant = relationship("Tenant", back_populates="user_tenant_roles")
    role = relationship("Role", back_populates="user_tenant_roles")

    # Ensure unique user-tenant combination
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant'),
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


class UserSession(Base):
    """
    Track user's active tenant during their session.
    This allows users to switch between tenants they have access to.
    """
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    current_tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Session tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Device/browser info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
