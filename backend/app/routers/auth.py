from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqlalchemy.orm import Session
import os
import uuid
import secrets
from datetime import datetime, timedelta, timezone

from app.models.user import (
    User, UserResponse, UserCreate, UserLogin,
    PasswordResetRequest, PasswordReset, EmailVerification
)
from app.database import get_db
from app.crud import users as user_crud
from app.crud import spaces as space_crud
from app.crud import user_space_roles as user_space_role_crud
from app.crud import auth_identities as auth_identity_crud
from app.utils.auth import create_access_token
from app.utils.password import verify_password, get_password_hash

# OAuth configuration
config = Config(environ={
    "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
    "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
})

oauth = OAuth(config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# Email/Password Authentication
@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email and password"""
    # Check if user already exists
    if user_crud.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_crud.get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    # Check if password identity already exists for this email
    if auth_identity_crud.get_identity_by_provider_subject(db, "password", user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    password_hash = get_password_hash(user_data.password)

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)

    # Create user (without default space - users will be added to spaces separately)
    user = user_crud.create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        name=user_data.name,
        is_verified=False
    )

    # Create password auth identity
    auth_identity_crud.create_identity(
        db=db,
        user_id=user.id,
        provider="password",
        provider_subject=user_data.email,
        metadata={"password_hash": password_hash}
    )

    # Update verification token
    user_crud.update_user_verification_token(db, user.id, verification_token)

    # TODO: Send verification email
    # For now, we'll just log it
    print(f"Verification token for {user.email}: {verification_token}")

    # Refresh to get role relationship
    db.refresh(user)
    return user


@router.post("/login")
async def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login with email and password"""
    # Get password identity
    identity = auth_identity_crud.get_identity_by_provider_subject(db, "password", credentials.email)
    if not identity:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Get the user
    user = user_crud.get_user_by_id(db, identity.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password from provider_metadata
    password_hash = identity.provider_metadata.get("password_hash")
    if not password_hash or not verify_password(credentials.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Update last login
    user_crud.update_user_last_login(db, user.id)

    # Create JWT token
    access_token = create_access_token(data={"sub": user.id, "email": user.email})

    # Set httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7  # 7 days
    )

    return {"message": "Logged in successfully"}


# Google OAuth Authentication
@router.get("/google")
async def login_google(request: Request):
    """Initiate Google OAuth flow"""
    redirect_uri = f"{BACKEND_URL}/api/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    """Handle Google OAuth callback with automatic account linking"""
    try:
        # Get the token from Google
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        # Extract user data
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')

        # Try to find existing Google identity
        google_identity = auth_identity_crud.get_identity_by_provider_subject(db, "google", google_id)

        if google_identity:
            # User already has a Google identity
            user = user_crud.get_user_by_id(db, google_identity.user_id)
        else:
            # Check if user exists by email (account linking)
            user = user_crud.get_user_by_email(db, email)

            if user:
                # Link Google identity to existing user account
                auth_identity_crud.create_identity(
                    db=db,
                    user_id=user.id,
                    provider="google",
                    provider_subject=google_id,
                    metadata={"email": email, "name": name, "picture": picture}
                )
                print(f"Linked Google account to existing user: {email}")
            else:
                # Create new user with Google OAuth (without default space)
                username = email.split('@')[0] + "_" + secrets.token_hex(4)
                user = user_crud.create_user(
                    db=db,
                    email=email,
                    username=username,
                    name=name,
                    picture=picture,
                    is_verified=True  # OAuth users are auto-verified
                )

                # Create Google identity
                auth_identity_crud.create_identity(
                    db=db,
                    user_id=user.id,
                    provider="google",
                    provider_subject=google_id,
                    metadata={"email": email, "name": name, "picture": picture}
                )

        # Update last login
        user_crud.update_user_last_login(db, user.id)

        # Create JWT token
        access_token = create_access_token(data={"sub": user.id, "email": user.email})

        # Create response and set httpOnly cookie
        redirect_response = RedirectResponse(url=FRONTEND_URL)
        redirect_response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24 * 7  # 7 days
        )

        return redirect_response

    except Exception as e:
        import traceback
        print(f"Auth error: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user"""
    from app.utils.auth import verify_token

    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify token
    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get user
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return user


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing the cookie"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


# Email verification and password reset
@router.post("/verify-email")
async def verify_email(data: EmailVerification, db: Session = Depends(get_db)):
    """Verify user email with token"""
    user = user_crud.verify_user(db, data.token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    return {"message": "Email verified successfully"}


@router.post("/request-password-reset")
async def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset email"""
    user = user_crud.get_user_by_email(db, data.email)
    if user:
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        user_crud.update_reset_token(db, user.id, reset_token, expires)

        # TODO: Send password reset email
        print(f"Password reset token for {user.email}: {reset_token}")

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(data: PasswordReset, db: Session = Depends(get_db)):
    """Reset password with token"""
    password_hash = get_password_hash(data.new_password)
    user = user_crud.reset_password(db, data.token, password_hash)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"message": "Password reset successfully"}
