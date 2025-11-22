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
    is_public = Column(Boolean, default=False, nullable=False, index=True)  # Public accessibility
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


class Page(Base):
    """
    Wiki page with draft content and version history.
    Each page belongs to a space and can appear once in the page tree.
    """
    __tablename__ = "pages"

    id = Column(String, primary_key=True, default=generate_uuid)
    space_id = Column(String, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)

    # Draft content (autosaved)
    draft_etag = Column(String(64), nullable=True)
    draft_json = Column(JSON, nullable=True)  # Tiptap JSON
    draft_text = Column(Text, nullable=True)  # Plain text for search

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    space = relationship("Space", backref="pages")
    creator = relationship("User", foreign_keys=[created_by])
    versions = relationship("PageVersion", back_populates="page", cascade="all, delete-orphan")
    tree_node = relationship("TreeNode", back_populates="page", uselist=False, cascade="all, delete-orphan")
    backlinks_out = relationship("Backlink", foreign_keys="[Backlink.src_page_id]", back_populates="src_page", cascade="all, delete-orphan")
    backlinks_in = relationship("Backlink", foreign_keys="[Backlink.dst_page_id]", back_populates="dst_page", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="page")

    __table_args__ = (
        UniqueConstraint('space_id', 'slug', name='uq_space_slug'),
    )


class PageVersion(Base):
    """
    Published version of a page.
    Created when a draft is published, preserving history.
    """
    __tablename__ = "page_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    page_id = Column(String, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    content_json = Column(JSON, nullable=False)
    content_text = Column(Text, nullable=False)
    author_id = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    notes = Column(Text, nullable=True)

    # Relationships
    page = relationship("Page", back_populates="versions")
    author = relationship("User")

    __table_args__ = (
        UniqueConstraint('page_id', 'version_number', name='uq_page_version'),
    )


class TreeNode(Base):
    """
    Hierarchical organization of pages within a space.
    Each page appears once in the tree per space.
    Uses gapped positioning (1024, 2048, ...) for efficient reordering.
    """
    __tablename__ = "tree_nodes"

    id = Column(String, primary_key=True, default=generate_uuid)
    space_id = Column(String, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String, ForeignKey("pages.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL for root sentinel
    parent_id = Column(String, ForeignKey("tree_nodes.id", ondelete="CASCADE"), nullable=True, index=True)
    position = Column(Integer, nullable=False, index=True)

    # Relationships
    space = relationship("Space", backref="tree_nodes")
    page = relationship("Page", back_populates="tree_node")
    parent = relationship("TreeNode", remote_side=[id], backref="children")

    __table_args__ = (
        UniqueConstraint('space_id', 'page_id', name='uq_space_page'),
    )


class Backlink(Base):
    """
    Tracks internal links between pages.
    Extracted from page content when publishing.
    """
    __tablename__ = "backlinks"

    id = Column(String, primary_key=True, default=generate_uuid)
    src_page_id = Column(String, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    dst_page_id = Column(String, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    space_id = Column(String, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    src_page = relationship("Page", foreign_keys=[src_page_id], back_populates="backlinks_out")
    dst_page = relationship("Page", foreign_keys=[dst_page_id], back_populates="backlinks_in")
    space = relationship("Space", backref="backlinks")

    __table_args__ = (
        UniqueConstraint('src_page_id', 'dst_page_id', name='uq_src_dst'),
    )


class Attachment(Base):
    """
    File attachments for pages (images, documents, etc.).
    Supports presigned URL uploads with deduplication via SHA256.
    """
    __tablename__ = "attachments"

    id = Column(String, primary_key=True, default=generate_uuid)
    space_id = Column(String, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True, index=True)
    url = Column(String(2048), nullable=False)
    filename = Column(String(500), nullable=False)
    mime_type = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=True, index=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    space = relationship("Space", backref="attachments")
    page = relationship("Page", back_populates="attachments")
    creator = relationship("User")


