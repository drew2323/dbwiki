"""
CRUD operations for attachments
"""
from sqlalchemy.orm import Session
from app.models.db_models import Attachment
from typing import Optional, List
import uuid
import os


def get_attachment_by_id(db: Session, attachment_id: str) -> Optional[Attachment]:
    """Get attachment by ID"""
    return db.query(Attachment).filter(Attachment.id == attachment_id).first()


def get_attachments_by_page(db: Session, page_id: str) -> List[Attachment]:
    """Get all attachments for a page"""
    return db.query(Attachment).filter(Attachment.page_id == page_id).all()


def get_attachments_by_space(
    db: Session,
    space_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[Attachment]:
    """Get all attachments in a space"""
    return db.query(Attachment).filter(
        Attachment.space_id == space_id
    ).offset(skip).limit(limit).all()


def get_orphaned_attachments(db: Session, space_id: str) -> List[Attachment]:
    """Get attachments not linked to any page"""
    return db.query(Attachment).filter(
        Attachment.space_id == space_id,
        Attachment.page_id == None
    ).all()


def find_by_hash(db: Session, sha256_hash: str) -> Optional[Attachment]:
    """Find attachment by SHA256 hash (for deduplication)"""
    return db.query(Attachment).filter(Attachment.sha256_hash == sha256_hash).first()


def create_attachment(
    db: Session,
    space_id: str,
    url: str,
    filename: str,
    mime_type: str,
    size_bytes: int,
    created_by: str,
    page_id: Optional[str] = None,
    sha256_hash: Optional[str] = None
) -> Attachment:
    """Create a new attachment record"""
    attachment = Attachment(
        id=str(uuid.uuid4()),
        space_id=space_id,
        page_id=page_id,
        url=url,
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        sha256_hash=sha256_hash,
        created_by=created_by
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def update_attachment_page(
    db: Session,
    attachment_id: str,
    page_id: Optional[str]
) -> Optional[Attachment]:
    """Link or unlink attachment from a page"""
    attachment = get_attachment_by_id(db, attachment_id)
    if not attachment:
        return None

    attachment.page_id = page_id
    db.commit()
    db.refresh(attachment)
    return attachment


def delete_attachment(db: Session, attachment_id: str) -> bool:
    """Delete an attachment record (does not delete file from storage)"""
    attachment = get_attachment_by_id(db, attachment_id)
    if not attachment:
        return False

    db.delete(attachment)
    db.commit()
    return True


def generate_upload_path(space_id: str, filename: str) -> str:
    """
    Generate a unique upload path for an attachment.
    Format: {space_id}/attachments/{uuid}_{filename}
    """
    unique_id = str(uuid.uuid4())[:8]
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ['.', '-', '_'])
    return f"{space_id}/attachments/{unique_id}_{safe_filename}"


def get_storage_stats(db: Session, space_id: str) -> dict:
    """Get storage statistics for a space"""
    from sqlalchemy import func

    result = db.query(
        func.count(Attachment.id).label('count'),
        func.sum(Attachment.size_bytes).label('total_bytes')
    ).filter(
        Attachment.space_id == space_id
    ).first()

    return {
        'count': result.count or 0,
        'total_bytes': result.total_bytes or 0,
        'total_mb': round((result.total_bytes or 0) / (1024 * 1024), 2)
    }
