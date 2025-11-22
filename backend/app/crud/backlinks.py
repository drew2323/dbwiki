"""
CRUD operations for backlinks
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.db_models import Backlink, Page
from typing import List, Dict, Any, Set
import uuid
import re


def get_backlinks_to_page(db: Session, page_id: str) -> List[Backlink]:
    """Get all backlinks pointing to a page"""
    return db.query(Backlink).filter(Backlink.dst_page_id == page_id).all()


def get_backlinks_from_page(db: Session, page_id: str) -> List[Backlink]:
    """Get all backlinks from a page"""
    return db.query(Backlink).filter(Backlink.src_page_id == page_id).all()


def extract_page_links(content_json: Dict[str, Any]) -> Set[str]:
    """
    Extract page IDs from Tiptap JSON content.
    Looks for link nodes with internal page references.

    Example link format in Tiptap:
    {
      "type": "link",
      "attrs": {
        "href": "/p/page-id-slug" or "page-id"
      }
    }
    """
    page_ids = set()

    def traverse(node):
        if isinstance(node, dict):
            # Check if this is a link node
            if node.get('type') == 'link':
                href = node.get('attrs', {}).get('href', '')
                # Extract page ID from href
                # Format: /p/{page-id}-{slug} or just {page-id}
                if href.startswith('/p/'):
                    page_id = href.split('/p/')[1].split('-')[0]
                    page_ids.add(page_id)
                elif re.match(r'^[a-f0-9-]{36}$', href):  # UUID pattern
                    page_ids.add(href)

            # Recurse through content
            if 'content' in node:
                for child in node['content']:
                    traverse(child)
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(content_json)
    return page_ids


def create_backlink(
    db: Session,
    src_page_id: str,
    dst_page_id: str,
    space_id: str
) -> Backlink:
    """Create a backlink"""
    backlink = Backlink(
        id=str(uuid.uuid4()),
        src_page_id=src_page_id,
        dst_page_id=dst_page_id,
        space_id=space_id
    )
    db.add(backlink)
    db.commit()
    db.refresh(backlink)
    return backlink


def update_backlinks_for_page(
    db: Session,
    src_page_id: str,
    space_id: str,
    content_json: Dict[str, Any]
) -> None:
    """
    Update backlinks for a page based on its content.
    Deletes old backlinks and creates new ones.
    """
    # Extract page IDs from content
    dst_page_ids = extract_page_links(content_json)

    # Delete existing backlinks from this page
    db.query(Backlink).filter(Backlink.src_page_id == src_page_id).delete()

    # Create new backlinks
    for dst_page_id in dst_page_ids:
        # Verify destination page exists
        dst_page = db.query(Page).filter(Page.id == dst_page_id).first()
        if dst_page:
            create_backlink(db, src_page_id, dst_page_id, space_id)

    db.commit()


def delete_backlinks_for_page(db: Session, page_id: str) -> None:
    """Delete all backlinks to and from a page"""
    db.query(Backlink).filter(
        (Backlink.src_page_id == page_id) | (Backlink.dst_page_id == page_id)
    ).delete()
    db.commit()


def get_backlink_count(db: Session, page_id: str) -> int:
    """Get count of backlinks to a page"""
    return db.query(Backlink).filter(Backlink.dst_page_id == page_id).count()


def get_popular_pages(db: Session, space_id: str, limit: int = 10) -> List[tuple]:
    """
    Get most linked-to pages in a space.

    Returns:
        List of (page_id, backlink_count) tuples
    """
    from sqlalchemy import func

    results = db.query(
        Backlink.dst_page_id,
        func.count(Backlink.id).label('count')
    ).filter(
        Backlink.space_id == space_id
    ).group_by(
        Backlink.dst_page_id
    ).order_by(
        func.count(Backlink.id).desc()
    ).limit(limit).all()

    return results
