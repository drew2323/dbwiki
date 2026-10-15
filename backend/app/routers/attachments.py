"""
Attachment management API endpoints.

Upload flow used by the UI: POST /api/attachments/upload (multipart).
A presign flow (S3-style) is kept for future object storage: POST /presign,
then POST /{id}/upload.
Files are served through GET /api/attachments/{id}/file so the same access
rules as for pages apply (public spaces are readable without login).
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import hashlib
import os
from pathlib import Path

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.dependencies.access import require_space_read, require_space_write, user_can_write_space
from app.models.db_models import User, Attachment
from app.models.page import (
    AttachmentPresignRequest, AttachmentPresignResponse, AttachmentResponse
)
from app.crud import attachments as attachment_crud
from app.crud import spaces as space_crud
from app.crud import pages as page_crud

router = APIRouter(prefix="/api/attachments", tags=["attachments"])


# ============================================================================
# Configuration
# ============================================================================

# Local storage path (update for production with S3)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024
CHUNK = 1024 * 1024

# Types that are safe to render inline in the browser; everything else downloads
INLINE_MIME_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf",
}


def ensure_upload_dir() -> Path:
    """Ensure upload directory exists"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def _storage_path(url: str) -> Path:
    """Resolve the stored relative url ('/uploads/<path>') to a file inside UPLOAD_DIR."""
    rel = url[len("/uploads/"):] if url.startswith("/uploads/") else url
    full = (UPLOAD_DIR / rel).resolve()
    if UPLOAD_DIR.resolve() not in full.parents:
        raise HTTPException(status_code=400, detail="Invalid storage path")
    return full


def _clean_filename(name: Optional[str]) -> str:
    name = os.path.basename((name or "").replace("\\", "/")).strip()
    return name or "file"


async def _save_upload(file: UploadFile, dest: Path) -> tuple[str, int]:
    """Stream upload to `dest`, enforcing the size limit. Returns (sha256, size)."""
    sha = hashlib.sha256()
    size = 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(dest, "wb") as out:
            while True:
                chunk = await file.read(CHUNK)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)"
                    )
                sha.update(chunk)
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return sha.hexdigest(), size


def _attachment_or_404(db: Session, attachment_id: str) -> Attachment:
    attachment = attachment_crud.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment


# ============================================================================
# Upload endpoints
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
    Direct multipart upload. Identical files within a space share one stored
    copy (SHA256) but get their own attachment record.
    """
    require_space_write(db, space_id, user)

    if page_id:
        page = page_crud.get_page_by_id(db, page_id)
        if not page or page.space_id != space_id:
            raise HTTPException(status_code=404, detail="Page not found in this space")

    filename = _clean_filename(file.filename)
    upload_dir = ensure_upload_dir()
    rel = attachment_crud.generate_upload_path(space_id, filename)
    full_path = upload_dir / rel

    file_hash, size = await _save_upload(file, full_path)
    if size == 0:
        full_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty file")

    url = f"/uploads/{rel}"
    existing = db.query(Attachment).filter(
        Attachment.space_id == space_id, Attachment.sha256_hash == file_hash
    ).first()
    if existing and _storage_path(existing.url).exists():
        full_path.unlink(missing_ok=True)  # reuse the stored copy
        url = existing.url

    return attachment_crud.create_attachment(
        db=db,
        space_id=space_id,
        url=url,
        filename=filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        created_by=user.id,
        page_id=page_id,
        sha256_hash=file_hash
    )


@router.post("/presign", response_model=AttachmentPresignResponse)
async def request_presigned_upload(
    presign_data: AttachmentPresignRequest,
    space_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 1 of the presigned flow: create a pending attachment record and
    return the endpoint to upload the bytes to (an S3 URL in production).
    """
    require_space_write(db, space_id, user)
    filename = _clean_filename(presign_data.filename)
    rel = attachment_crud.generate_upload_path(space_id, filename)

    attachment = attachment_crud.create_attachment(
        db=db,
        space_id=space_id,
        url=f"/uploads/{rel}",
        filename=filename,
        mime_type=presign_data.mime_type,
        size_bytes=presign_data.size_bytes,
        created_by=user.id,
        page_id=None
    )
    return AttachmentPresignResponse(
        upload_url=f"/api/attachments/{attachment.id}/upload",
        attachment_id=attachment.id,
        fields=None
    )


@router.post("/{attachment_id}/upload", response_model=AttachmentResponse)
async def upload_file(
    attachment_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 2 of the presigned flow: store the bytes at the path recorded in step 1."""
    attachment = _attachment_or_404(db, attachment_id)
    if attachment.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if attachment.sha256_hash:
        raise HTTPException(status_code=409, detail="Attachment already uploaded")

    ensure_upload_dir()
    file_hash, size = await _save_upload(file, _storage_path(attachment.url))
    attachment.sha256_hash = file_hash
    attachment.size_bytes = size
    db.commit()
    db.refresh(attachment)
    return attachment


# ============================================================================
# Reading
# ============================================================================

@router.get("/{attachment_id}/file")
async def download_file(
    attachment_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Serve the file. Safe image/PDF types render inline, everything else downloads."""
    attachment = _attachment_or_404(db, attachment_id)
    require_space_read(db, attachment.space_id, user)

    path = _storage_path(attachment.url)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File missing from storage")

    inline = attachment.mime_type in INLINE_MIME_TYPES
    return FileResponse(
        path,
        media_type=attachment.mime_type if inline else "application/octet-stream",
        filename=attachment.filename,
        content_disposition_type="inline" if inline else "attachment",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
            "Cache-Control": "private, max-age=3600",
        },
    )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get attachment metadata by ID"""
    attachment = _attachment_or_404(db, attachment_id)
    require_space_read(db, attachment.space_id, user)
    return attachment


@router.get("/page/{page_id}/list", response_model=List[AttachmentResponse])
async def list_page_attachments(
    page_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """List all attachments for a page"""
    page = page_crud.get_page_by_id(db, page_id, include_archived=True)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    require_space_read(db, page.space_id, user)
    return attachment_crud.get_attachments_by_page(db, page_id)


@router.get("/space/{space_id}/list", response_model=List[AttachmentResponse])
async def list_space_attachments(
    space_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """List all attachments in a space"""
    require_space_read(db, space_id, user)
    return attachment_crud.get_attachments_by_space(db, space_id, skip, limit)


@router.get("/space/{space_id}/orphaned", response_model=List[AttachmentResponse])
async def list_orphaned_attachments(
    space_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List attachments not linked to any page"""
    require_space_write(db, space_id, user)
    return attachment_crud.get_orphaned_attachments(db, space_id)


@router.get("/space/{space_id}/stats")
async def get_storage_stats(
    space_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get storage usage statistics for a space"""
    require_space_read(db, space_id, user)
    return attachment_crud.get_storage_stats(db, space_id)


# ============================================================================
# Management
# ============================================================================

@router.patch("/{attachment_id}/link", response_model=AttachmentResponse)
async def link_attachment_to_page(
    attachment_id: str,
    page_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Link or unlink (page_id omitted) an attachment to/from a page of the same space."""
    attachment = _attachment_or_404(db, attachment_id)
    require_space_write(db, attachment.space_id, user)
    if page_id:
        page = page_crud.get_page_by_id(db, page_id)
        if not page or page.space_id != attachment.space_id:
            raise HTTPException(status_code=404, detail="Page not found in this space")
    return attachment_crud.update_attachment_page(db, attachment_id, page_id)


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an attachment; the stored file goes too unless another record shares it."""
    attachment = _attachment_or_404(db, attachment_id)
    space = space_crud.get_space_by_id(db, attachment.space_id)
    if attachment.created_by != user.id and not (space and user_can_write_space(db, user, space) and
                                                (user.is_superuser or space.created_by == user.id
                                                 or _is_space_admin(db, user, space.id))):
        raise HTTPException(status_code=403, detail="Not authorized")

    url = attachment.url
    attachment_crud.delete_attachment(db, attachment_id)

    if not db.query(Attachment).filter(Attachment.url == url).first():
        try:
            _storage_path(url).unlink(missing_ok=True)
        except HTTPException:
            pass


def _is_space_admin(db: Session, user: User, space_id: str) -> bool:
    from app.crud import user_space_roles as usr_crud
    role = usr_crud.get_user_role_in_space(db, user.id, space_id)
    return bool(role and role.name.lower() in ("admin", "superuser"))
