from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import os

from app.models.user import User
from app.utils.mock_users import get_user_by_google_id, create_user, update_last_login
from app.utils.auth import create_access_token

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


@router.get("/google")
async def login_google(request: Request):
    """Initiate Google OAuth flow"""
    # Use BACKEND_URL for OAuth callback (works in both dev and production)
    redirect_uri = f"{BACKEND_URL}/api/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request, response: Response):
    """Handle Google OAuth callback"""
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

        # Get or create user
        user = get_user_by_google_id(google_id)
        if not user:
            user = create_user(
                email=email,
                name=name,
                google_id=google_id,
                picture=picture
            )
        else:
            # Update last login
            update_last_login(user.id)

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
        print(f"Auth error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/me", response_model=User)
async def get_current_user(request: Request):
    """Get current authenticated user"""
    from app.utils.auth import verify_token
    from app.utils.mock_users import get_user_by_id

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
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing the cookie"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
