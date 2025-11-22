"""
Pydantic schemas for CMS page models.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ============================================================================
# Page Schemas
# ============================================================================

class PageBase(BaseModel):
    """Base schema for page with common fields"""
    title: str = Field(..., max_length=500, description="Page title")
    slug: Optional[str] = Field(None, max_length=500, description="URL-friendly slug")


class PageCreate(PageBase):
    """Schema for creating a new page"""
    space_id: str
    parent_id: Optional[str] = Field(None, description="Parent tree node ID for placement")
    position: Optional[int] = Field(None, description="Position in tree (auto-calculated if not provided)")


class PageUpdate(BaseModel):
    """Schema for updating page metadata"""
    title: Optional[str] = Field(None, max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    is_archived: Optional[bool] = None


class DraftUpdate(BaseModel):
    """Schema for autosaving draft content"""
    draft_json: Optional[Dict[str, Any]] = Field(None, description="Tiptap JSON content")
    draft_text: Optional[str] = Field(None, description="Plain text for search indexing")
    if_match: Optional[str] = Field(None, description="ETag for optimistic concurrency control")


class DraftResponse(BaseModel):
    """Response with draft content and ETag"""
    draft_json: Optional[Dict[str, Any]] = None
    draft_text: Optional[str] = None
    draft_etag: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    """Full page response with metadata"""
    id: str
    space_id: str
    title: str
    slug: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    draft_etag: Optional[str] = None

    class Config:
        from_attributes = True


class PageDetailResponse(PageResponse):
    """Page with draft content included"""
    draft_json: Optional[Dict[str, Any]] = None
    draft_text: Optional[str] = None


class PageTreeResponse(BaseModel):
    """Page in tree structure with tree node info"""
    id: str
    title: str
    slug: str
    tree_node_id: str
    parent_id: Optional[str] = None
    position: int
    has_children: bool = False

    class Config:
        from_attributes = True


# ============================================================================
# Page Version Schemas
# ============================================================================

class VersionPublish(BaseModel):
    """Schema for publishing a page version"""
    notes: Optional[str] = Field(None, description="Version notes/changelog")


class VersionResponse(BaseModel):
    """Published version response"""
    id: str
    page_id: str
    version_number: int
    title: str
    content_json: Dict[str, Any]
    content_text: str
    author_id: str
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class VersionListItem(BaseModel):
    """Lightweight version for listing"""
    id: str
    version_number: int
    title: str
    author_id: str
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class VersionRestore(BaseModel):
    """Schema for restoring draft from a version"""
    version_id: str


# ============================================================================
# Tree Node Schemas
# ============================================================================

class TreeNodeCreate(BaseModel):
    """Create a tree node (usually handled internally)"""
    space_id: str
    page_id: Optional[str] = None
    parent_id: Optional[str] = None
    position: int = Field(..., description="Position in sibling list")


class TreeNodeMove(BaseModel):
    """Move a tree node to new parent/position"""
    parent_id: Optional[str] = Field(None, description="New parent node ID (null for root)")
    position: int = Field(..., description="New position among siblings")


class TreeNodeReorder(BaseModel):
    """Batch reorder nodes"""
    updates: List[Dict[str, Any]] = Field(
        ...,
        description="List of {id, position} updates",
        example=[{"id": "node1", "position": 1024}, {"id": "node2", "position": 2048}]
    )


class TreeNodeResponse(BaseModel):
    """Tree node with page info"""
    id: str
    space_id: str
    page_id: Optional[str] = None
    parent_id: Optional[str] = None
    position: int

    # Populated page info
    page_title: Optional[str] = None
    page_slug: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Backlink Schemas
# ============================================================================

class BacklinkResponse(BaseModel):
    """Response for a backlink"""
    id: str
    src_page_id: str
    dst_page_id: str
    space_id: str
    created_at: datetime

    # Populated source page info
    src_page_title: Optional[str] = None
    src_page_slug: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Attachment Schemas
# ============================================================================

class AttachmentCreate(BaseModel):
    """Create attachment record after upload"""
    page_id: Optional[str] = Field(None, description="Page this attachment belongs to")
    url: str = Field(..., max_length=2048)
    filename: str = Field(..., max_length=500)
    mime_type: str = Field(..., max_length=255)
    size_bytes: int = Field(..., gt=0)
    sha256_hash: Optional[str] = Field(None, max_length=64)


class AttachmentPresignRequest(BaseModel):
    """Request presigned URL for upload"""
    filename: str = Field(..., max_length=500)
    mime_type: str = Field(..., max_length=255)
    size_bytes: int = Field(..., gt=0, le=100*1024*1024, description="Max 100MB")


class AttachmentPresignResponse(BaseModel):
    """Presigned upload URL response"""
    upload_url: str
    attachment_id: str
    fields: Optional[Dict[str, str]] = None  # For multipart form uploads


class AttachmentResponse(BaseModel):
    """Attachment response"""
    id: str
    space_id: str
    page_id: Optional[str] = None
    url: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256_hash: Optional[str] = None
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Search Schemas
# ============================================================================

class SearchQuery(BaseModel):
    """Full-text search query"""
    query: str = Field(..., min_length=1, max_length=500)
    space_id: Optional[str] = Field(None, description="Limit to specific space")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class SearchResult(BaseModel):
    """Search result item"""
    page_id: str
    title: str
    slug: str
    space_id: str
    snippet: Optional[str] = Field(None, description="Highlighted text snippet")
    rank: float = Field(0.0, description="Search relevance score")

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Search results response"""
    results: List[SearchResult]
    total: int
    query: str
    took_ms: Optional[float] = None
