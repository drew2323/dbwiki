"""
CRUD operations for pages
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.db_models import Page
from typing import Optional, List, Dict, Any
import uuid
import hashlib
import json


def generate_slug(title: str) -> str:
    """Generate URL-safe slug from title"""
    slug = title.lower()
    # Replace spaces and special chars with hyphens
    slug = ''.join(c if c.isalnum() or c in [' ', '-'] else '' for c in slug)
    slug = '-'.join(slug.split())
    return slug[:500]  # Limit to max length


def generate_etag(content: Dict[str, Any]) -> str:
    """Generate ETag from content for optimistic concurrency control"""
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()


def get_page_by_id(db: Session, page_id: str, include_archived: bool = False) -> Optional[Page]:
    """Get page by ID"""
    query = db.query(Page).filter(Page.id == page_id)
    if not include_archived:
        query = query.filter(Page.is_archived == False)
    return query.first()


def get_page_by_slug(db: Session, space_id: str, slug: str, include_archived: bool = False) -> Optional[Page]:
    """Get page by slug within a space"""
    query = db.query(Page).filter(
        Page.space_id == space_id,
        Page.slug == slug
    )
    if not include_archived:
        query = query.filter(Page.is_archived == False)
    return query.first()


def get_pages_by_space(
    db: Session,
    space_id: str,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[Page]:
    """Get all pages in a space"""
    query = db.query(Page).filter(Page.space_id == space_id)
    if not include_archived:
        query = query.filter(Page.is_archived == False)
    return query.offset(skip).limit(limit).all()


def create_page(
    db: Session,
    space_id: str,
    title: str,
    created_by: str,
    slug: Optional[str] = None,
    draft_json: Optional[Dict[str, Any]] = None,
    draft_text: Optional[str] = None
) -> Page:
    """Create a new page"""
    if not slug:
        slug = generate_slug(title)

    # Generate ETag if draft content provided
    draft_etag = None
    if draft_json:
        draft_etag = generate_etag(draft_json)

    page = Page(
        id=str(uuid.uuid4()),
        space_id=space_id,
        title=title,
        slug=slug,
        created_by=created_by,
        draft_json=draft_json,
        draft_text=draft_text,
        draft_etag=draft_etag
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def update_page_metadata(
    db: Session,
    page_id: str,
    title: Optional[str] = None,
    slug: Optional[str] = None,
    is_archived: Optional[bool] = None
) -> Optional[Page]:
    """Update page metadata (not draft content)"""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        return None

    if title is not None:
        page.title = title
        # Auto-update slug if title changed and slug not explicitly provided
        if slug is None:
            page.slug = generate_slug(title)

    if slug is not None:
        page.slug = slug

    if is_archived is not None:
        page.is_archived = is_archived

    page.updated_at = func.now()
    db.commit()
    db.refresh(page)
    return page


def update_page_draft(
    db: Session,
    page_id: str,
    draft_json: Optional[Dict[str, Any]] = None,
    draft_text: Optional[str] = None,
    if_match: Optional[str] = None
) -> tuple[Optional[Page], bool]:
    """
    Update page draft content with ETag-based optimistic locking.

    Returns:
        (page, success) tuple where success=False indicates ETag mismatch
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        return None, False

    # Check ETag if provided
    if if_match and page.draft_etag != if_match:
        return page, False  # ETag mismatch - conflict

    # Update draft content
    if draft_json is not None:
        page.draft_json = draft_json
        page.draft_etag = generate_etag(draft_json)

    if draft_text is not None:
        page.draft_text = draft_text

    page.updated_at = func.now()
    db.commit()
    db.refresh(page)
    return page, True


def delete_page(db: Session, page_id: str, hard_delete: bool = False) -> bool:
    """Delete a page (soft or hard delete)"""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        return False

    if hard_delete:
        db.delete(page)
    else:
        page.is_archived = True
        page.updated_at = func.now()

    db.commit()
    return True


def search_pages(
    db: Session,
    query: str,
    space_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[List[Page], int]:
    """
    Full-text search on pages using PostgreSQL.

    Returns:
        (pages, total_count) tuple
    """
    # Base query with full-text search
    search_query = db.query(Page).filter(
        func.to_tsvector('english', Page.draft_text).op('@@')(
            func.plainto_tsquery('english', query)
        ),
        Page.is_archived == False
    )

    # Filter by space if provided
    if space_id:
        search_query = search_query.filter(Page.space_id == space_id)

    # Get total count
    total = search_query.count()

    # Get paginated results with ranking
    results = search_query.order_by(
        func.ts_rank(
            func.to_tsvector('english', Page.draft_text),
            func.plainto_tsquery('english', query)
        ).desc()
    ).offset(offset).limit(limit).all()

    return results, total
