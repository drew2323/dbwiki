"""
Page management API endpoints for CMS.
Handles page CRUD, draft autosave, publishing, and version management.
"""
from fastapi import APIRouter, HTTPException, Depends, Header, status
from sqlalchemy.orm import Session
from typing import List, Optional
import time

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_space_id
from app.models.db_models import User
from app.models.page import (
    PageCreate, PageUpdate, PageResponse, PageDetailResponse,
    DraftUpdate, DraftResponse, VersionPublish, VersionResponse,
    VersionListItem, VersionRestore, SearchQuery, SearchResponse,
    SearchResult
)
from app.crud import pages as page_crud
from app.crud import page_versions as version_crud
from app.crud import tree_nodes as tree_crud
from app.crud import backlinks as backlink_crud
from app.crud import spaces as space_crud

router = APIRouter(prefix="/api/pages", tags=["pages"])


# ============================================================================
# Page CRUD Endpoints
# ============================================================================

@router.post("/", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    page_data: PageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new page in a space.
    Automatically creates a tree node for the page.
    """
    # Verify space exists and user has access
    space = space_crud.get_space_by_id(db, page_data.space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Create page
    page = page_crud.create_page(
        db=db,
        space_id=page_data.space_id,
        title=page_data.title,
        created_by=user.id,
        slug=page_data.slug
    )

    # Create tree node
    tree_crud.create_node(
        db=db,
        space_id=page_data.space_id,
        page_id=page.id,
        parent_id=page_data.parent_id,
        position=page_data.position
    )

    return page


@router.get("/{page_id}", response_model=PageDetailResponse)
async def get_page(
    page_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get page by ID with draft content.
    """
    page = page_crud.get_page_by_id(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # TODO: Check if user has access to this space
    # For now, authenticated users can access any page

    return page


@router.get("/space/{space_id}/list", response_model=List[PageResponse])
async def list_pages_in_space(
    space_id: str,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    List all pages in a space.
    """
    # Verify space exists
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    pages = page_crud.get_pages_by_space(
        db=db,
        space_id=space_id,
        include_archived=include_archived,
        skip=skip,
        limit=limit
    )

    return pages


@router.get("/slug/{space_id}/{slug}", response_model=PageDetailResponse)
async def get_page_by_slug(
    space_id: str,
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get page by slug within a space.
    Used for pretty URLs.
    """
    page = page_crud.get_page_by_slug(db, space_id, slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page


@router.patch("/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: str,
    page_data: PageUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update page metadata (title, slug, archive status).
    Does not affect draft content - use draft endpoint for that.
    """
    page = page_crud.update_page_metadata(
        db=db,
        page_id=page_id,
        title=page_data.title,
        slug=page_data.slug,
        is_archived=page_data.is_archived
    )

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: str,
    hard_delete: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a page (soft delete by default, hard delete if specified).
    """
    success = page_crud.delete_page(db, page_id, hard_delete=hard_delete)
    if not success:
        raise HTTPException(status_code=404, detail="Page not found")


# ============================================================================
# Draft Management Endpoints
# ============================================================================

@router.get("/{page_id}/draft", response_model=DraftResponse)
async def get_draft(
    page_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get draft content with ETag for optimistic locking.
    """
    page = page_crud.get_page_by_id(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return {
        "draft_json": page.draft_json,
        "draft_text": page.draft_text,
        "draft_etag": page.draft_etag,
        "updated_at": page.updated_at
    }


@router.put("/{page_id}/draft", response_model=DraftResponse)
async def update_draft(
    page_id: str,
    draft_data: DraftUpdate,
    if_match: Optional[str] = Header(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autosave draft content with ETag-based optimistic concurrency control.

    Headers:
        If-Match: ETag value for conflict detection

    Returns:
        409 Conflict if ETag mismatch
    """
    # Use header If-Match or body if_match
    etag = if_match or draft_data.if_match

    page, success = page_crud.update_page_draft(
        db=db,
        page_id=page_id,
        draft_json=draft_data.draft_json,
        draft_text=draft_data.draft_text,
        if_match=etag
    )

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Draft was modified by another user. Please refresh and try again.",
            headers={"ETag": page.draft_etag}
        )

    return {
        "draft_json": page.draft_json,
        "draft_text": page.draft_text,
        "draft_etag": page.draft_etag,
        "updated_at": page.updated_at
    }


# ============================================================================
# Version Management Endpoints
# ============================================================================

@router.post("/{page_id}/publish", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def publish_page(
    page_id: str,
    publish_data: VersionPublish,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Publish the current draft as a new version.
    Also updates backlinks based on content.
    """
    page = page_crud.get_page_by_id(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if not page.draft_json:
        raise HTTPException(status_code=400, detail="No draft content to publish")

    # Publish draft to new version
    version = version_crud.publish_draft(
        db=db,
        page_id=page_id,
        author_id=user.id,
        notes=publish_data.notes
    )

    # Update backlinks based on published content
    backlink_crud.update_backlinks_for_page(
        db=db,
        src_page_id=page_id,
        space_id=page.space_id,
        content_json=page.draft_json
    )

    return version


@router.get("/{page_id}/versions", response_model=List[VersionListItem])
async def list_versions(
    page_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    List all versions for a page, newest first.
    """
    versions = version_crud.get_versions_by_page(db, page_id, skip, limit)
    return versions


@router.get("/{page_id}/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    page_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get a specific version by ID.
    """
    version = version_crud.get_version_by_id(db, version_id)
    if not version or version.page_id != page_id:
        raise HTTPException(status_code=404, detail="Version not found")

    return version


@router.post("/{page_id}/restore", response_model=DraftResponse)
async def restore_version(
    page_id: str,
    restore_data: VersionRestore,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restore a version's content to the current draft.
    Does not create a new version - just updates the draft.
    """
    page = version_crud.restore_version_to_draft(
        db=db,
        page_id=page_id,
        version_id=restore_data.version_id
    )

    if not page:
        raise HTTPException(status_code=404, detail="Page or version not found")

    return {
        "draft_json": page.draft_json,
        "draft_text": page.draft_text,
        "draft_etag": page.draft_etag,
        "updated_at": page.updated_at
    }


# ============================================================================
# Backlink Endpoints
# ============================================================================

@router.get("/{page_id}/backlinks")
async def get_backlinks(
    page_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get all pages that link to this page.
    """
    backlinks = backlink_crud.get_backlinks_to_page(db, page_id)

    # Enrich with source page info
    result = []
    for backlink in backlinks:
        src_page = page_crud.get_page_by_id(db, backlink.src_page_id)
        if src_page:
            result.append({
                "id": backlink.id,
                "src_page_id": backlink.src_page_id,
                "src_page_title": src_page.title,
                "src_page_slug": src_page.slug,
                "created_at": backlink.created_at
            })

    return result


# ============================================================================
# Search Endpoint
# ============================================================================

@router.post("/search", response_model=SearchResponse)
async def search_pages(
    search_data: SearchQuery,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Full-text search across pages.
    """
    start_time = time.time()

    pages, total = page_crud.search_pages(
        db=db,
        query=search_data.query,
        space_id=search_data.space_id,
        limit=search_data.limit,
        offset=search_data.offset
    )

    # Convert to search results
    results = []
    for page in pages:
        # Extract snippet (first 200 chars of draft_text)
        snippet = page.draft_text[:200] + "..." if page.draft_text and len(page.draft_text) > 200 else page.draft_text

        results.append(SearchResult(
            page_id=page.id,
            title=page.title,
            slug=page.slug,
            space_id=page.space_id,
            snippet=snippet,
            rank=0.0  # TODO: Calculate actual rank
        ))

    took_ms = (time.time() - start_time) * 1000

    return SearchResponse(
        results=results,
        total=total,
        query=search_data.query,
        took_ms=took_ms
    )
