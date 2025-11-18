# DBWiki Project - Overview

## Project Overview
DBWiki is a full-stack wiki cms with a Vue 3 frontend and FastAPI backend, featuring Google OAuth authentication
## Technology Stack

### Frontend
- **Framework**: Vue 3 with TypeScript
- **Build Tool**: Vite
- **UI Framework**: PrimeVue 4 with PrimeIcons
- **State Management**: Pinia (Composition API style)
- **Router**: Vue Router 4
- **HTTP Client**: Axios
- **Charts**: Chart.js, Lightweigth Charts - always use latest version
- **CSS**: Tailwind CSS + Sass
- **Port**: 5173 (development)

### Backend
- **Framework**: FastAPI
- **Language**: Python
- **Database**: PostgreSQL with SQLAlchemy 2.0, Alembic migrations
- **Authentication**: Email/password (bcrypt) + Google OAuth with JWT cookies
- **Spaces Architecture**: User-Space-Role junction table, space context via X-Space-Id header
- **Session Management**: Starlette SessionMiddleware
- **Port**: 8000

## Quick Start

### Development
```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure with your credentials
python -m uvicorn main:app --reload --port 8000

# Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

**Access**: http://localhost:5173

### Docker (Local Testing)
```bash
docker compose up -d
```

## Documentation

### Core Documentation
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Getting started, development workflow, coding standards
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Project structure, frontend/backend architecture
- **[AUTHENTICATION.md](docs/AUTHENTICATION.md)** - OAuth flow, security, user management
- **[API.md](docs/API.md)** - API endpoints, data models, examples
- **[UI_FRAMEWORK.md](docs/UI_FRAMEWORK.md)** - PrimeVue integration, layouts, components
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Docker, CI/CD, production setup
- **[RELEASES.md](docs/RELEASES.md)** - Release management, semantic versioning

## Key Features

### Reminders
- always use Primevue components, so it will work with switching the Theme internally
- search for available Primevue components
- if exra styling is needed, use Theme variables
- use Toast service if necessary
- keep frontend compact and information dense, yet professional looking
- dont verify that build works, i will do it myself

### ✅ Implemented
- **Authentication**: Email/password registration + Google OAuth, JWT httpOnly cookies, email verification, password reset
- **Spaces Architecture**: Users belong to multiple spaces with different roles per space, space switcher in UI
- **Database**: PostgreSQL with Alembic migrations, Space/Role/User/UserSpaceRole models
- **Authorization**: Role-based + permission-based per space context via `require_role_in_space()` and `require_permission_in_space()`
- **Frontend**: PrimeVue UI with dynamic theming, Pinia stores (authStore, spaceStore, layoutStore), axios interceptor for space context
- **API**: Complete CRUD for users, spaces, roles, space membership management
- Docker containerization, Nginx reverse proxy


## Project Structure

```
dbwiki/
├── backend/
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── crud/         # Database operations (users, spaces, roles, user_space_roles)
│   │   ├── models/       # Pydantic (user.py) + SQLAlchemy (db_models.py) models
│   │   ├── routers/      # API endpoints (auth.py, spaces.py, roles.py)
│   │   ├── utils/        # Password hashing, JWT auth
│   │   └── dependencies/ # Auth context (get_current_user, require_role_in_space)
│   ├── database.py       # SQLAlchemy engine + session
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── components/   # SpaceSwitcher.vue, admin components
│   │   ├── config/       # axios.ts (X-Space-Id interceptor)
│   │   ├── layout/       # AppTopbar, AppSettings
│   │   ├── services/     # authService, spaceService
│   │   ├── stores/       # authStore, spaceStore, layoutStore
│   │   ├── types/        # TypeScript interfaces
│   │   └── views/        # Login, Register, admin pages
│   └── vite.config.ts
│
├── docker-compose.yml    # PostgreSQL + app containers
└── .env                  # DATABASE_URL, JWT_SECRET_KEY, GOOGLE_CLIENT_ID/SECRET
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for complete structure details.

## Configuration

### Backend Environment Variables
```env
DATABASE_URL=postgresql+psycopg://user@localhost:5432/dbwiki
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
JWT_SECRET_KEY=<min-32-character-secret>
JWT_ALGORITHM=HS256
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
```

### Google OAuth Setup
1. Create project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Add authorized origins: `http://localhost:5174`, `http://localhost:8000`
5. Add redirect URI: `http://localhost:8000/api/auth/callback`

See [AUTHENTICATION.md](docs/AUTHENTICATION.md) for complete setup guide.

## Deployment

### Release-Based Deployment
```bash
# Create and push version tag to trigger deployment
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

GitHub Actions automatically:
- Builds Docker images
- Deploys to VPS
- Creates GitHub release
- Updates deployment version

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) and [RELEASES.md](docs/RELEASES.md) for details.

## Development Guidelines

### Code Standards
- **Frontend**: Vue 3 Composition API, TypeScript, PrimeVue patterns
- **Backend**: FastAPI best practices, Pydantic validation, type hints, SQLAlchemy 2.0 patterns
- **State**: Pinia stores (authStore, spaceStore, layoutStore) with localStorage persistence
- **Spaces**: Always use space context via `X-Space-Id` header, `require_role_in_space()` for auth
- **Styling**: Tailwind CSS + PrimeVue theming
- **Migrations**: Use Alembic for schema changes (`alembic revision -m "description"`)

### Git Workflow
- `master`: Production-ready code
- Feature branches: `feature/feature-name`
- Bug fixes: `fix/bug-description`
- Never commit `.env` files

### Key Principles
- Follow existing component/layout structure
- Use PrimeVue components when available
- Test Docker builds before deployment
- Update documentation when adding features
- Use TypeScript for new files

## Troubleshooting

### Common Issues

**Backend won't start**
- Check port 8000: `lsof -ti:8000`
- Verify `.env` file exists with DATABASE_URL
- Check dependencies: `pip install -r requirements.txt`
- Run migrations: `alembic upgrade head`

**Database issues**
- Ensure PostgreSQL running: `psql -U user -d dbwiki`
- Check migration status: `alembic current`
- View migration history: `alembic history`

**Authentication errors**
- Verify JWT_SECRET_KEY in `.env` (32+ chars)
- Check cookies in browser DevTools
- For spaces: Ensure X-Space-Id header sent

**Frontend won't connect**
- Verify backend on port 8000, frontend on 5173
- Check axios interceptor loaded in main.ts
- Verify CORS in `backend/main.py`

See [DEVELOPMENT.md](docs/DEVELOPMENT.md#troubleshooting) for more details.

## Resources

### Documentation
- [Vue 3](https://vuejs.org/)
- [PrimeVue](https://primevue.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pinia](https://pinia.vuejs.org/)

### Project Links
- API Docs (dev): http://localhost:8000/docs
- Frontend (dev): http://localhost:5174

---

**Last Updated**: November 18, 2025
**Primary Developer**: David P. Brazda (davidbrazda61@gmail.com)

**Quick Navigation**:
- 🚀 [Getting Started](docs/DEVELOPMENT.md)
- 🏗️ [Architecture](docs/ARCHITECTURE.md)
- 🔐 [Authentication](docs/AUTHENTICATION.md)
- 📡 [API Reference](docs/API.md)
- 🎨 [UI Framework](docs/UI_FRAMEWORK.md)
- 🚢 [Deployment](docs/DEPLOYMENT.md)
- 📦 [Releases](docs/RELEASES.md)
