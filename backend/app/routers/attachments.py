"""
Attachment management API endpoints.
Handles file uploads with presigned URLs (ready for S3 or local storage).
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import hashlib
from pathlib import Path

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.db_models import User
from app.models.page import (
    AttachmentCreate, AttachmentPresignRequest, AttachmentPresignResponse,
    AttachmentResponse
)
from app.crud import attachments as attachment_crud
from app.crud import spaces as space_crud
from app.crud import pages as page_crud

router = APIRouter(prefix="/api/attachments", tags=["attachments"])


# ============================================================================
# Configuration
# ============================================================================

# Local storage path (update for production with S3)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# ============================================================================
# Presigned Upload Endpoints (S3-style)
# ============================================================================

@router.post("/presign", response_model=AttachmentPresignResponse)
async def request_presigned_upload(
    presign_data: AttachmentPresignRequest,
    space_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request a presigned URL for file upload.
    In production, this would generate an S3 presigned URL.
    For now, returns a local upload endpoint.

    Flow:
    1. Client requests presigned URL with file metadata
    2. Server creates attachment record with pending status
    3. Client uploads directly to presigned URL
    4. Client confirms upload, server updates attachment
    """
    # Verify space exists
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Generate upload path
    upload_path = attachment_crud.generate_upload_path(space_id, presign_data.filename)
    full_path = UPLOAD_DIR / upload_path

    # Create directory if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Create pending attachment record
    attachment = attachment_crud.create_attachment(
        db=db,
        space_id=space_id,
        url=f"/uploads/{upload_path}",  # Will be updated after upload
        filename=presign_data.filename,
        mime_type=presign_data.mime_type,
        size_bytes=presign_data.size_bytes,
        created_by=user.id,
        page_id=None  # Will be linked later
    )

    # In production, generate S3 presigned URL here
    # For now, return local upload endpoint
    upload_url = f"/api/attachments/{attachment.id}/upload"

    return AttachmentPresignResponse(
        upload_url=upload_url,
        attachment_id=attachment.id,
        fields=None  # Would contain S3 form fields in production
    )


@router.post("/{attachment_id}/upload", response_model=AttachmentResponse)
async def upload_file(
    attachment_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload file to local storage (or S3 in production).
    This endpoint is used with the presigned upload flow.
    """
    # Get attachment record
    attachment = attachment_crud.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Verify user owns this attachment
    if attachment.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Save file to local storage
    upload_path = attachment_crud.generate_upload_path(
        attachment.space_id,
        attachment.filename
    )
    full_path = UPLOAD_DIR / upload_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(full_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Calculate hash
    file_hash = calculate_file_hash(full_path)

    # Check for duplicate
    existing = attachment_crud.find_by_hash(db, file_hash)
    if existing and existing.id != attachment_id:
        # Delete duplicate, return existing
        os.remove(full_path)
        attachment_crud.delete_attachment(db, attachment_id)
        return existing

    # Update attachment with hash and final URL
    attachment.sha256_hash = file_hash
    attachment.url = f"/uploads/{upload_path}"
    db.commit()
    db.refresh(attachment)

    return attachment


# ============================================================================
# Direct Upload Endpoint (simpler alternative)
# ============================================================================

@router.post("/upload", response_model=AttachmentResponse)
async def direct_upload(
    space_id: str,
    file: UploadFile = File(...),
    page_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Direct file upload (simpler flow, no presigning).
    Use this for small files or when presigning is not needed.
    """
    # Verify space exists
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Verify page exists if provided
    if page_id:
        page = page_crud.get_page_by_id(db, page_id)
        if not page or page.space_id != space_id:
            raise HTTPException(status_code=404, detail="Page not found in this space")

    # Generate upload path
    upload_path = attachment_crud.generate_upload_path(space_id, file.filename)
    full_path = UPLOAD_DIR / upload_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Save file
    content = await file.read()
    with open(full_path, "wb") as f:
        f.write(content)

    # Calculate hash and size
    file_hash = calculate_file_hash(full_path)
    file_size = len(content)

    # Check for duplicate
    existing = attachment_crud.find_by_hash(db, file_hash)
    if existing:
        # Delete duplicate file
        os.remove(full_path)
        # Update page_id if needed
        if page_id and not existing.page_id:
            existing.page_id = page_id
            db.commit()
            db.refresh(existing)
        return existing

    # Create attachment record
    attachment = attachment_crud.create_attachment(
        db=db,
        space_id=space_id,
        url=f"/uploads/{upload_path}",
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=file_size,
        created_by=user.id,
        page_id=page_id,
        sha256_hash=file_hash
    )

    return attachment


# ============================================================================
# Attachment Management Endpoints
# ============================================================================

@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get attachment by ID"""
    attachment = attachment_crud.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return attachment


@router.get("/page/{page_id}/list", response_model=List[AttachmentResponse])
async def list_page_attachments(
    page_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all attachments for a page"""
    attachments = attachment_crud.get_attachments_by_page(db, page_id)
    return attachments


@router.get("/space/{space_id}/list", response_model=List[AttachmentResponse])
async def list_space_attachments(
    space_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all attachments in a space"""
    attachments = attachment_crud.get_attachments_by_space(db, space_id, skip, limit)
    return attachments


@router.get("/space/{space_id}/orphaned", response_model=List[AttachmentResponse])
async def list_orphaned_attachments(
    space_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List attachments not linked to any page"""
    attachments = attachment_crud.get_orphaned_attachments(db, space_id)
    return attachments


@router.patch("/{attachment_id}/link", response_model=AttachmentResponse)
async def link_attachment_to_page(
    attachment_id: str,
    page_id: Optional[str],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link or unlink an attachment to/from a page.
    Set page_id to null to unlink.
    """
    attachment = attachment_crud.update_attachment_page(db, attachment_id, page_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return attachment


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an attachment.
    Note: This deletes the database record but not the file from storage.
    """
    attachment = attachment_crud.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Verify user owns this attachment (or is admin)
    if attachment.created_by != user.id and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    success = attachment_crud.delete_attachment(db, attachment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # TODO: Delete file from storage in background task


# ============================================================================
# Storage Statistics
# ============================================================================

@router.get("/space/{space_id}/stats")
async def get_storage_stats(
    space_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get storage usage statistics for a space"""
    stats = attachment_crud.get_storage_stats(db, space_id)
    return stats
