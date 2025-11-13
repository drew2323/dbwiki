from sqlalchemy.orm import Session
from app.models.db_models import User, Role, Tenant, UserTenantRole, AuthIdentity
from typing import Optional
from datetime import datetime, timezone
import uuid

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_provider_identity(db: Session, provider: str, provider_subject: str) -> Optional[User]:
    """Get user by their auth identity (e.g., google_id, email for password)"""
    identity = db.query(AuthIdentity).filter(
        AuthIdentity.provider == provider,
        AuthIdentity.provider_subject == provider_subject
    ).first()
    return identity.user if identity else None

def create_user(
    db: Session,
    email: str,
    username: str,
    default_tenant_id: str,
    role_id: str,
    name: Optional[str] = None,
    picture: Optional[str] = None,
    is_verified: bool = False
) -> User:
    """
    Create a new user with a default tenant.
    Also creates the UserTenantRole association automatically.
    Note: Auth identities should be created separately using auth_identities CRUD.
    """
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=email,
        username=username,
        name=name,
        picture=picture,
        default_tenant_id=default_tenant_id,
        is_verified=is_verified,
        is_active=True
    )
    db.add(user)

    # Create the UserTenantRole association
    user_tenant_role = UserTenantRole(
        id=str(uuid.uuid4()),
        user_id=user_id,
        tenant_id=default_tenant_id,
        role_id=role_id,
        is_active=True
    )
    db.add(user_tenant_role)

    db.commit()
    db.refresh(user)
    return user

def update_user_last_login(db: Session, user_id: str) -> None:
    db.query(User).filter(User.id == user_id).update({"last_login": datetime.now(timezone.utc)})
    db.commit()

def update_user_verification_token(db: Session, user_id: str, token: str) -> None:
    db.query(User).filter(User.id == user_id).update({"verification_token": token})
    db.commit()

def verify_user(db: Session, token: str) -> Optional[User]:
    user = db.query(User).filter(User.verification_token == token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.commit()
        db.refresh(user)
    return user

def update_reset_token(db: Session, user_id: str, token: str, expires: datetime) -> None:
    db.query(User).filter(User.id == user_id).update({
        "reset_token": token,
        "reset_token_expires": expires
    })
    db.commit()

def reset_password(db: Session, token: str, new_password_hash: str) -> Optional[User]:
    """Reset password for a user. Updates the password identity's metadata."""
    user = db.query(User).filter(
        User.reset_token == token,
        User.reset_token_expires > datetime.now(timezone.utc)
    ).first()
    if user:
        # Update the password identity
        password_identity = db.query(AuthIdentity).filter(
            AuthIdentity.user_id == user.id,
            AuthIdentity.provider == 'password'
        ).first()
        if password_identity:
            password_identity.provider_metadata = {"password_hash": new_password_hash}
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        db.refresh(user)
    return user

def get_users(db: Session, tenant_id: Optional[str] = None, skip: int = 0, limit: int = 100):
    query = db.query(User)
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    return query.offset(skip).limit(limit).all()

def deactivate_user(db: Session, user_id: str) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user

def activate_user(db: Session, user_id: str) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = True
        db.commit()
        db.refresh(user)
    return user
