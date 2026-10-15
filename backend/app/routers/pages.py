"""
Page management API endpoints for CMS.
Handles page CRUD, draft autosave, publishing, and version management.
"""
from fastapi import APIRouter, HTTPException, Depends, Header, status
from sqlalchemy.orm import Session
from typing import List, Optional
import time

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.dependencies.access import (
    require_space_read, require_space_write, user_can_write_space, readable_space_ids
)
from app.models.db_models import User, Page, PageFavorite, Space
from app.models.page import (
    PageCreate, PageUpdate, PageResponse, PageDetailResponse, PageDuplicate,
    TemplateInfo, FavoritePage, DraftUpdate, DraftResponse, VersionPublish, VersionResponse,
    VersionListItem, VersionRestore, SearchQuery, SearchResponse,
    SearchResult
)
from app.utils import page_templates
from app.crud import pages as page_crud
from app.crud import page_versions as version_crud
from app.crud import tree_nodes as tree_crud
from app.crud import backlinks as backlink_crud
from app.crud import spaces as space_crud

router = APIRouter(prefix="/api/pages", tags=["pages"])


def _load_page(db: Session, page_id: str, user: Optional[User] = None) -> Page:
    """Load a page; archived pages exist only for people who can edit the space."""
    page = page_crud.get_page_by_id(db, page_id, include_archived=True)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    if page.is_archived:
        space = space_crud.get_space_by_id(db, page.space_id)
        if not (user and space and user_can_write_space(db, user, space)):
            raise HTTPException(status_code=404, detail="Page not found")
    return page


def _page_for_reader(db: Session, page: Page, user: Optional[User]) -> dict:
    """Page detail; drafts are only shown to people who can edit the space."""
    space = require_space_read(db, page.space_id, user)
    data = PageResponse.model_validate(page).model_dump()
    can_edit = user is not None and user_can_write_space(db, user, space)
    data["draft_json"] = page.draft_json if can_edit else None
    data["draft_text"] = page.draft_text if can_edit else None
    return data


@router.get("/templates", response_model=List[TemplateInfo])
async def list_templates():
    """Built-in page templates for the create-page dialog."""
    return page_templates.list_templates()


# ============================================================================
# Page CRUD Endpoints
# ============================================================================

@router.get("/favorites/me", response_model=List[FavoritePage])
async def list_my_favorites(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """The current user's starred pages (only those they can still read), newest first."""
    rows = db.query(Page, Space).join(PageFavorite, PageFavorite.page_id == Page.id) \
        .join(Space, Space.id == Page.space_id) \
        .filter(PageFavorite.user_id == user.id, Page.is_archived == False) \
        .order_by(PageFavorite.created_at.desc()).all()  # noqa: E712

    result = []
    for page, space in rows:
        try:
            require_space_read(db, space.id, user)
        except HTTPException:
            continue  # lost access since starring
        result.append(FavoritePage(
            page_id=page.id, title=page.title, slug=page.slug,
            space_id=space.id, space_key=space.key, space_name=space.name
        ))
    return result


@router.put("/{page_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(
    page_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Star a page (idempotent)."""
    page = _load_page(db, page_id, user)
    require_space_read(db, page.space_id, user)
    exists = db.query(PageFavorite).filter(
        PageFavorite.user_id == user.id, PageFavorite.page_id == page_id).first()
    if not exists:
        db.add(PageFavorite(user_id=user.id, page_id=page_id))
        db.commit()


@router.delete("/{page_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    page_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unstar a page (idempotent)."""
    db.query(PageFavorite).filter(
        PageFavorite.user_id == user.id, PageFavorite.page_id == page_id
    ).delete()
    db.commit()


@router.post("", response_model=PageResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    page_data: PageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new page in a space, optionally prefilled from a template.
    Page and tree node are created in one transaction.
    """
    require_space_write(db, page_data.space_id, user)

    if page_data.parent_id:
        parent = tree_crud.get_node_by_id(db, page_data.parent_id)
        if not parent or parent.space_id != page_data.space_id:
            raise HTTPException(
                status_code=400,
                detail="parent_id must be the tree node ID of a page in the same space"
            )

    draft_json = None
    draft_text = None
    if page_data.template_id:
        if not page_templates.template_exists(page_data.template_id):
            raise HTTPException(status_code=400, detail="Unknown template")
        draft_json = page_templates.get_template_content(page_data.template_id)
        if draft_json:
            draft_text = page_templates.tiptap_plain_text(draft_json)

    try:
        page = page_crud.create_page(
            db=db,
            space_id=page_data.space_id,
            title=page_data.title,
            created_by=user.id,
            slug=page_data.slug,
            draft_json=draft_json,
            draft_text=draft_text,
            commit=False
        )
        tree_crud.create_node(
            db=db,
            space_id=page_data.space_id,
            page_id=page.id,
            parent_id=page_data.parent_id,
            position=page_data.position,
            commit=False
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(page)
    return page


@router.get("/{page_id}", response_model=PageDetailResponse)
async def get_page(
    page_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get page by ID. Draft content is only included for users who can edit the space.
    """
    page = _load_page(db, page_id, user)
    return _page_for_reader(db, page, user)


@router.get("/space/{space_id}/list", response_model=List[PageResponse])
async def list_pages_in_space(
    space_id: str,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    List all pages in a space.
    """
    space = require_space_read(db, space_id, user)
    if include_archived and not (user and user_can_write_space(db, user, space)):
        include_archived = False

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
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get page by slug within a space.
    Used for pretty URLs.
    """
    page = page_crud.get_page_by_slug(db, space_id, slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return _page_for_reader(db, page, user)


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
    existing = _load_page(db, page_id, user)
    require_space_write(db, existing.space_id, user)

    if page_data.title is not None and not page_data.title.strip():
        raise HTTPException(status_code=422, detail="Title must not be empty")

    try:
        page = page_crud.update_page_metadata(
            db=db,
            page_id=page_id,
            title=page_data.title.strip() if page_data.title is not None else None,
            slug=page_data.slug,
            is_archived=page_data.is_archived
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))

    return page


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: str,
    hard_delete: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a page together with all pages below it
    (soft delete = archive by default, hard delete if specified).
    """
    existing = _load_page(db, page_id, user)
    require_space_write(db, existing.space_id, user)
    page_crud.delete_page(db, page_id, hard_delete=hard_delete)


@router.post("/{page_id}/duplicate", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_page(
    page_id: str,
    data: PageDuplicate = PageDuplicate(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Duplicate a page (without its children) right after the original in the tree.
    The copy's draft is the original's draft, or its latest published content.
    """
    src = _load_page(db, page_id, user)
    require_space_write(db, src.space_id, user)

    draft_json = src.draft_json
    draft_text = src.draft_text
    if not draft_json:
        latest = version_crud.get_latest_version(db, page_id)
        if latest:
            draft_json, draft_text = latest.content_json, latest.content_text

    title = (data.title or f"{src.title} (copy)").strip()

    src_node = tree_crud.get_node_by_page(db, page_id)
    parent_id = src_node.parent_id if src_node else None
    position = None
    if src_node and parent_id:
        siblings = tree_crud.get_children(db, parent_id)
        later = [n for n in siblings if n.position > src_node.position]
        position = tree_crud.calculate_position(db, parent_id, later[0].id if later else None)

    try:
        page = page_crud.create_page(
            db=db, space_id=src.space_id, title=title, created_by=user.id,
            draft_json=draft_json, draft_text=draft_text, commit=False
        )
        tree_crud.create_node(
            db=db, space_id=src.space_id, page_id=page.id,
            parent_id=parent_id, position=position, commit=False
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(page)
    return page


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
    page = _load_page(db, page_id, user)
    require_space_write(db, page.space_id, user)

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
    require_space_write(db, _load_page(db, page_id, user).space_id, user)

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
    page = _load_page(db, page_id, user)
    require_space_write(db, page.space_id, user)

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
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    List all versions for a page, newest first.
    """
    require_space_read(db, _load_page(db, page_id, user).space_id, user)
    versions = version_crud.get_versions_by_page(db, page_id, skip, limit)
    return versions


@router.get("/{page_id}/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    page_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get a specific version by ID.
    """
    require_space_read(db, _load_page(db, page_id, user).space_id, user)
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
    require_space_write(db, _load_page(db, page_id, user).space_id, user)
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
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get all pages that link to this page.
    """
    require_space_read(db, _load_page(db, page_id, user).space_id, user)
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
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Search pages by title and content, limited to spaces the caller can read.
    Content snippets are only returned to people who can edit the page's space
    (the indexed text is the draft).
    """
    start_time = time.time()

    if search_data.space_id:
        require_space_read(db, search_data.space_id, user)
        allowed = None
    else:
        allowed = readable_space_ids(db, user)

    rows, total = page_crud.search_pages(
        db=db,
        query=search_data.query,
        space_id=search_data.space_id,
        limit=search_data.limit,
        offset=search_data.offset,
        space_ids=allowed
    )

    spaces = {}
    editable = {}
    results = []
    for page, rank in rows:
        if page.space_id not in spaces:
            spaces[page.space_id] = space_crud.get_space_by_id(db, page.space_id)
            editable[page.space_id] = bool(
                user and spaces[page.space_id] and user_can_write_space(db, user, spaces[page.space_id])
            )
        space = spaces[page.space_id]

        snippet = None
        if editable[page.space_id] and page.draft_text:
            snippet = page.draft_text[:200] + "..." if len(page.draft_text) > 200 else page.draft_text

        results.append(SearchResult(
            page_id=page.id,
            title=page.title,
            slug=page.slug,
            space_id=page.space_id,
            space_key=space.key if space else None,
            space_name=space.name if space else None,
            snippet=snippet,
            rank=rank
        ))

    took_ms = (time.time() - start_time) * 1000

    return SearchResponse(
        results=results,
        total=total,
        query=search_data.query,
        took_ms=took_ms
    )
