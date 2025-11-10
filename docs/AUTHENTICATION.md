# Authentication Documentation

## Google OAuth Flow

### Backend Endpoints

#### Login Endpoint: `/api/auth/google`
- Redirects to Google OAuth consent screen
- Initiates OAuth flow

#### Callback Endpoint: `/api/auth/callback`
- Handles Google OAuth callback
- Creates or updates user in mock storage
- Generates JWT token
- Sets httpOnly cookie
- Redirects to frontend

#### Current User Endpoint: `/api/auth/me`
- Returns authenticated user info
- Requires valid JWT cookie

#### Logout Endpoint: `/api/auth/logout`
- Clears authentication cookie

## Security Features

- **JWT Tokens**: Stored in httpOnly cookies (XSS protection)
- **Token Expiration**: 7 days
- **CORS**: Configured for allowed origins (environment variable)
- **Session Middleware**: Starlette session for OAuth state management
- **Secure Cookies**:
  - Production: `secure=True` (HTTPS only)
  - Development: `secure=False` (HTTP allowed)

## Frontend Integration

### Auth Store (`stores/authStore.ts`)
- **State**:
  - `user`: Current user object (null when not authenticated)
  - `loading`: Loading state
  - `error`: Error message
- **Computed**:
  - `isAuthenticated`: Boolean based on user presence
- **Actions**:
  - `fetchUser()`: Get current user from backend
  - `login()`: Redirect to Google OAuth
  - `logout()`: Clear session and redirect to login

### Route Guards (`router/index.js`)
- Protected routes use `meta: { requiresAuth: true }`
- Navigation guard in `beforeEach`:
  1. Check if route requires authentication
  2. Fetch user if not already loaded
  3. Redirect to login if not authenticated
  4. Allow navigation if authenticated

### Authentication Pages
- **Login** (`/auth/login`): Standard login page
- **LoginAlt** (`/auth/login-alt`): Alternative login design
- **Register** (`/auth/register`): User registration
- **Access** (`/auth/access`): Access denied page
- **Error** (`/auth/error`): Error page

### User Flow
1. User visits application
2. If not authenticated, redirected to `/auth/login`
3. Clicks "Sign in with Google" → redirects to Google OAuth
4. Authenticates with Google account
5. Redirects back to frontend with httpOnly cookie containing JWT
6. Frontend fetches user info and displays dashboard
7. User profile appears in AppTopbar with dropdown menu
8. User can logout, which clears cookie and returns to login screen

## Configuration

### Backend Environment Variables (`.env`)
```env
GOOGLE_CLIENT_ID=client-id
GOOGLE_CLIENT_SECRET=secret-id
JWT_SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
JWT_ALGORITHM=HS256
FRONTEND_URL=http://localhost:5174
CORS_ORIGINS=http://localhost:5174
```

### Google Cloud Console OAuth Setup
**Authorized JavaScript origins**:
- `http://localhost:5174` (development)
- `http://localhost:8000`
- Production URLs (when deployed)

**Authorized redirect URIs**:
- `http://localhost:8000/api/auth/callback` (development)
- Production callback URL (when deployed)

## Data Storage

### User Storage
- Currently in-memory (mock) - resets on backend restart
- New users automatically created on first Google login
- User model includes: id, email, name, picture, google_id

### Future Enhancements
- Database persistence (PostgreSQL/MongoDB)
- Multi-factor authentication
- Email notifications
- Session management improvements

## API Response Example

### GET /api/auth/me
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "google_id": "113705771254809700048"
}
```

## Troubleshooting

### OAuth not working
- Verify Google Cloud Console credentials
- Check redirect URIs match exactly
- Clear browser cookies and try again
- Check backend logs for detailed error messages

### Picture not displaying
- Verify Google OAuth returns `picture` field
- Check browser console for image loading errors
- Ensure user has a Google profile picture set

### Cookie Issues
- Ensure `FRONTEND_URL` matches the actual frontend URL
- Check `CORS_ORIGINS` includes the frontend URL
- Verify browser allows cookies
- Check `secure` flag matches HTTP/HTTPS usage
