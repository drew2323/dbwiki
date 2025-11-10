# V3Trading Project - Overview

## Project Overview
V3Trading is a full-stack trading application with a Vue 3 frontend and FastAPI backend, featuring Google OAuth authentication and a mock trading API.

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
- **Authentication**: OAuth2 (Google) with JWT
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
- Google OAuth authentication with JWT
- PrimeVue UI framework with dynamic theming
- Responsive dashboard with widgets and charts
- Mock trading API (trades, positions, CRUD operations)
- Docker containerization
- GitHub Actions CI/CD pipeline
- Nginx reverse proxy with rate limiting

### 🚧 In Progress / Planned
- Database persistence (currently in-memory)
- Real trading API integration
- WebSocket for real-time updates
- Router TypeScript migration
- Production UI kit cleanup

## Project Structure

```
v3trading/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── routers/      # API endpoints
│   │   ├── models/       # Pydantic models
│   │   ├── utils/        # Utilities, mock data
│   │   └── dependencies/ # Auth dependencies
│   └── main.py
│
├── frontend/         # Vue 3 application
│   ├── src/
│   │   ├── layout/       # App layout components
│   │   ├── components/   # Reusable components
│   │   ├── views/        # Page components
│   │   ├── stores/       # Pinia state management
│   │   ├── services/     # API service layer
│   │   ├── router/       # Vue Router config
│   │   └── types/        # TypeScript types
│   └── vite.config.ts
│
├── docs/             # Detailed documentation
├── nginx/            # Nginx configuration
└── docker-compose.yml
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for complete structure details.

## Configuration

### Backend Environment Variables
```env
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
JWT_SECRET_KEY=<min-32-character-secret>
JWT_ALGORITHM=HS256
FRONTEND_URL=http://localhost:5174
CORS_ORIGINS=http://localhost:5174
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
- **Backend**: FastAPI best practices, Pydantic validation, type hints
- **State**: Pinia stores for state management (layoutStore, authStore, tradingStore)
- **Styling**: Tailwind CSS + PrimeVue theming
- **Preferences**: Managed by layoutStore with automatic localStorage persistence

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
- Verify `.env` file exists
- Check dependencies: `pip install -r requirements.txt`

**Frontend won't connect**
- Verify backend running on port 8000
- Check proxy in `vite.config.ts`
- Verify CORS in `backend/main.py`

**OAuth not working**
- Verify credentials in `.env`
- Check redirect URIs match exactly
- Clear browser cookies

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

**Last Updated**: October 8, 2025
**Primary Developer**: David P. Brazda (davidbrazda61@gmail.com)

**Quick Navigation**:
- 🚀 [Getting Started](docs/DEVELOPMENT.md)
- 🏗️ [Architecture](docs/ARCHITECTURE.md)
- 🔐 [Authentication](docs/AUTHENTICATION.md)
- 📡 [API Reference](docs/API.md)
- 🎨 [UI Framework](docs/UI_FRAMEWORK.md)
- 🚢 [Deployment](docs/DEPLOYMENT.md)
- 📦 [Releases](docs/RELEASES.md)
