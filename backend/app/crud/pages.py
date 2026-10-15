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
    return slug[:500] or "page"  # Limit to max length; never empty


def unique_slug(db: Session, space_id: str, base: str, exclude_page_id: Optional[str] = None) -> str:
    """Return `base` or `base-2`, `base-3`... so (space_id, slug) stays unique."""
    base = (base or "page")[:480]
    candidate, n = base, 1
    while True:
        query = db.query(Page.id).filter(Page.space_id == space_id, Page.slug == candidate)
        if exclude_page_id:
            query = query.filter(Page.id != exclude_page_id)
        if query.first() is None:
            return candidate
        n += 1
        candidate = f"{base}-{n}"


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
    draft_text: Optional[str] = None,
    commit: bool = True
) -> Page:
    """
    Create a new page. The slug is made unique within the space.
    With commit=False the page is only flushed so the caller can commit
    page and tree node in one transaction.
    """
    slug = unique_slug(db, space_id, slug or generate_slug(title))

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
    if commit:
        db.commit()
        db.refresh(page)
    else:
        db.flush()
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
            page.slug = unique_slug(db, page.space_id, generate_slug(title), exclude_page_id=page.id)

    if slug is not None:
        clash = db.query(Page.id).filter(
            Page.space_id == page.space_id, Page.slug == slug, Page.id != page.id
        ).first()
        if clash:
            raise ValueError(f"Slug '{slug}' is already used in this space")
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

    # A page's children live below it in the tree, so they go with it
    ids = [page_id] + get_descendant_page_ids(db, page_id)
    pages = db.query(Page).filter(Page.id.in_(ids)).all()

    if hard_delete:
        for p in pages:
            db.delete(p)  # tree node, versions, backlinks cascade
    else:
        for p in pages:
            p.is_archived = True
            p.updated_at = func.now()

    db.commit()
    return True


def get_descendant_page_ids(db: Session, page_id: str) -> List[str]:
    """Page ids of every page below `page_id` in the tree (children, grandchildren, ...)."""
    from app.models.db_models import TreeNode
    node = db.query(TreeNode).filter(TreeNode.page_id == page_id).first()
    result: List[str] = []
    frontier = [node.id] if node else []
    while frontier:
        children = db.query(TreeNode).filter(TreeNode.parent_id.in_(frontier)).all()
        result.extend(c.page_id for c in children if c.page_id)
        frontier = [c.id for c in children]
    return result


def search_pages(
    db: Session,
    query: str,
    space_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    space_ids: Optional[List[str]] = None
) -> tuple[List[tuple[Page, float]], int]:
    """
    Search pages by title (substring) and body (PostgreSQL full-text, prefix aware).

    space_ids restricts results to spaces the caller may read (None = no restriction).

    Returns:
        ([(page, rank), ...], total_count) - best matches first
    """
    from sqlalchemy import or_, literal, case

    query = query.strip()
    if not query:
        return [], 0

    # Prefix-aware tsquery: "quan wik" -> quan:* & wik:*
    terms = [''.join(c for c in t if c.isalnum()) for t in query.split()]
    terms = [t for t in terms if t]
    tsq = func.to_tsquery('simple', ' & '.join(f"{t}:*" for t in terms)) if terms else None
    tsv = func.to_tsvector('simple', func.coalesce(Page.draft_text, ''))
    like = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

    conditions = [Page.title.ilike(like, escape="\\")]
    if tsq is not None:
        conditions.append(tsv.op('@@')(tsq))

    search_query = db.query(Page).filter(or_(*conditions), Page.is_archived == False)  # noqa: E712

    if space_id:
        search_query = search_query.filter(Page.space_id == space_id)
    if space_ids is not None:
        search_query = search_query.filter(Page.space_id.in_(space_ids))

    total = search_query.count()

    body_rank = func.ts_rank(tsv, tsq) if tsq is not None else literal(0.0)
    title_rank = case((Page.title.ilike(like, escape="\\"), 1.0), else_=0.0)
    rank = (title_rank + body_rank).label("rank")

    rows = search_query.add_columns(rank).order_by(rank.desc(), Page.updated_at.desc()) \
        .offset(offset).limit(limit).all()

    return [(page, float(r)) for page, r in rows], total
