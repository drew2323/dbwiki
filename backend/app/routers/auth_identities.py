"""
Auth identities management router for managing user authentication providers.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.database import get_db
from app.crud import auth_identities as auth_identity_crud
from app.crud import users as user_crud

router = APIRouter(prefix="/api", tags=["auth_identities"])


class AuthIdentityResponse(BaseModel):
    id: str
    user_id: str
    provider: str
    provider_subject: str
    provider_metadata: Dict[str, Any]
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class CreateAuthIdentity(BaseModel):
    provider: str
    provider_subject: str
    metadata: Optional[Dict[str, Any]] = None


class UpdateAuthIdentity(BaseModel):
    metadata: Dict[str, Any]


@router.get("/users/{user_id}/identities", response_model=List[AuthIdentityResponse])
async def get_user_identities(user_id: str, db: Session = Depends(get_db)):
    """Get all auth identities for a specific user"""
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    identities = auth_identity_crud.get_identities_by_user_id(db, user_id)

    # Remove sensitive data from metadata (password_hash)
    result = []
    for identity in identities:
        identity_dict = {
            "id": identity.id,
            "user_id": identity.user_id,
            "provider": identity.provider,
            "provider_subject": identity.provider_subject,
            "provider_metadata": {
                k: v for k, v in identity.provider_metadata.items()
                if k != "password_hash"
            },
            "created_at": identity.created_at.isoformat() if identity.created_at else None,
            "updated_at": identity.updated_at.isoformat() if identity.updated_at else None
        }
        result.append(AuthIdentityResponse(**identity_dict))

    return result


@router.post("/users/{user_id}/identities", response_model=AuthIdentityResponse)
async def create_identity(
    user_id: str,
    identity_data: CreateAuthIdentity,
    db: Session = Depends(get_db)
):
    """Add a new auth identity to a user"""
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if this provider+subject combination already exists
    existing = auth_identity_crud.get_identity_by_provider_subject(
        db, identity_data.provider, identity_data.provider_subject
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Identity with provider '{identity_data.provider}' and subject '{identity_data.provider_subject}' already exists"
        )

    identity = auth_identity_crud.create_identity(
        db=db,
        user_id=user_id,
        provider=identity_data.provider,
        provider_subject=identity_data.provider_subject,
        metadata=identity_data.metadata or {}
    )

    # Remove password_hash from response
    metadata = {k: v for k, v in identity.provider_metadata.items() if k != "password_hash"}

    return AuthIdentityResponse(
        id=identity.id,
        user_id=identity.user_id,
        provider=identity.provider,
        provider_subject=identity.provider_subject,
        provider_metadata=metadata,
        created_at=identity.created_at.isoformat(),
        updated_at=identity.updated_at.isoformat() if identity.updated_at else None
    )


@router.put("/identities/{identity_id}", response_model=AuthIdentityResponse)
async def update_identity(
    identity_id: str,
    identity_data: UpdateAuthIdentity,
    db: Session = Depends(get_db)
):
    """Update an auth identity's metadata"""
    from app.models.db_models import AuthIdentity

    identity = db.query(AuthIdentity).filter(AuthIdentity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    identity = auth_identity_crud.update_identity_metadata(
        db, identity_id, identity_data.metadata
    )

    # Remove password_hash from response
    metadata = {k: v for k, v in identity.provider_metadata.items() if k != "password_hash"}

    return AuthIdentityResponse(
        id=identity.id,
        user_id=identity.user_id,
        provider=identity.provider,
        provider_subject=identity.provider_subject,
        provider_metadata=metadata,
        created_at=identity.created_at.isoformat(),
        updated_at=identity.updated_at.isoformat() if identity.updated_at else None
    )


@router.delete("/identities/{identity_id}")
async def delete_identity(identity_id: str, db: Session = Depends(get_db)):
    """Remove an auth identity from a user"""
    from app.models.db_models import AuthIdentity

    identity = db.query(AuthIdentity).filter(AuthIdentity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    # Check if this is the user's only identity
    user_identities = auth_identity_crud.get_identities_by_user_id(db, identity.user_id)
    if len(user_identities) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the user's only auth identity. User must have at least one way to authenticate."
        )

    success = auth_identity_crud.delete_identity(db, identity_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete identity")

    return {"message": "Identity deleted successfully"}


@router.get("/identities/providers")
async def get_available_providers():
    """Get list of available authentication providers"""
    return {
        "providers": [
            {
                "name": "password",
                "label": "Email/Password",
                "icon": "pi-key",
                "description": "Traditional email and password authentication"
            },
            {
                "name": "google",
                "label": "Google",
                "icon": "pi-google",
                "description": "Google OAuth authentication"
            },
            {
                "name": "github",
                "label": "GitHub",
                "icon": "pi-github",
                "description": "GitHub OAuth authentication (not yet implemented)"
            },
            {
                "name": "oidc",
                "label": "OpenID Connect",
                "icon": "pi-id-card",
                "description": "Generic OpenID Connect provider (not yet implemented)"
            }
        ]
    }
