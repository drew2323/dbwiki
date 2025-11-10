# Development Guide

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- Google OAuth credentials (for authentication)
- Git

### Initial Setup

#### 1. Clone Repository
```bash
git clone <repository-url>
cd v3trading
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install
```

#### 4. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized origins and redirect URIs:
   - Origins: `http://localhost:5174`, `http://localhost:8000`
   - Redirect: `http://localhost:8000/api/auth/callback`
6. Copy Client ID and Secret to backend `.env`

## Running the Application

### Development Mode

#### Backend
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm run dev
```

### Access Points
- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc

## Development Workflow

### Code Organization

#### Frontend
- **Components**: Reusable Vue components in `src/components/`
- **Views**: Page-level components in `src/views/`
- **Layout**: Application layout in `src/layout/`
- **Services**: API calls in `src/services/`
- **Stores**: Pinia stores in `src/stores/`
- **Types**: TypeScript types in `src/types/`
- **Router**: Routes in `src/router/index.js`

#### Backend
- **Routers**: Route handlers in `app/routers/`
- **Models**: Pydantic models in `app/models/`
- **Utils**: Utilities in `app/utils/`
- **Dependencies**: Dependency injection in `app/dependencies/`

### Adding New Features

#### Frontend Component
```bash
# Create component
touch frontend/src/components/MyComponent.vue

# Use in view or other component
import MyComponent from '@/components/MyComponent.vue';
```

#### Backend Endpoint
```python
# Add router in app/routers/
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}

# Register in main.py
from app.routers import my_router
app.include_router(my_router.router, prefix="/api/my", tags=["my"])
```

### State Management

#### Creating a Store
```typescript
// src/stores/myStore.ts
import { defineStore } from 'pinia';

export const useMyStore = defineStore('my', {
  state: () => ({
    data: null,
    loading: false,
    error: null
  }),

  getters: {
    hasData: (state) => state.data !== null
  },

  actions: {
    async fetchData() {
      this.loading = true;
      try {
        // API call
        this.data = await api.get('/my-endpoint');
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
});
```

## Testing

### Frontend
```bash
cd frontend
npm run build  # Test build process
```

### Backend
```bash
cd backend
python -m pytest  # When tests are added
```

## Code Style

### Frontend
- Use Vue 3 Composition API (not Options API)
- Follow TypeScript best practices
- Use PrimeVue components when available
- Follow existing component patterns
- Use Pinia for state management

### Backend
- Follow PEP 8 style guide
- Use type hints
- Use Pydantic models for validation
- Follow FastAPI best practices
- Document endpoints with docstrings

## Environment Configuration

### Development Ports
- Frontend: 5173 or 5174 (configurable in `vite.config.ts`)
- Backend: 8000

### Environment Variables

#### Backend (.env)
```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
FRONTEND_URL=http://localhost:5174
CORS_ORIGINS=http://localhost:5174
```

#### Frontend
- Uses Vite proxy configuration (no .env needed for development)
- Proxy in `vite.config.ts` routes `/api` to `http://localhost:8000`

## Development Tips

### Hot Reload
- Frontend: Vite provides instant hot reload
- Backend: `--reload` flag enables auto-restart on file changes

### Debugging

#### Frontend
- Use Vue DevTools browser extension
- Console logging: `console.log()`
- Vue component debugging in DevTools

#### Backend
- FastAPI automatic docs at `/docs` and `/redoc`
- Python debugger: `import pdb; pdb.set_trace()`
- Console logging: `print()` or use logging module

### Mock Data
- Trading data in `backend/app/utils/mock_data.py`
- User data in `backend/app/utils/mock_users.py`
- Modify to test different scenarios

### Database (Future)
Current implementation uses in-memory storage. To add database:
1. Choose database (PostgreSQL, MongoDB)
2. Add database driver to `requirements.txt`
3. Create database models/schemas
4. Replace mock storage with database queries
5. Add migrations system

## Git Workflow

### Branches
- `master`: Main branch (production-ready)
- Feature branches: `feature/feature-name`
- Bug fixes: `fix/bug-description`

### Commits
```bash
# Good commit messages
git commit -m "Add user profile endpoint"
git commit -m "Fix authentication cookie issue"
git commit -m "Update dashboard widget layout"
```

### Deployment
See [DEPLOYMENT.md](./DEPLOYMENT.md) and [RELEASES.md](./RELEASES.md)

## Troubleshooting

### Backend won't start
- Check if port 8000 is in use: `lsof -ti:8000`
- Verify `.env` file exists with correct credentials
- Check Python dependencies: `pip install -r requirements.txt`

### Frontend won't connect to backend
- Verify backend is running on port 8000
- Check proxy configuration in `vite.config.ts`
- Verify CORS settings in `backend/main.py`

### Module not found errors
- Frontend: Run `npm install`
- Backend: Run `pip install -r requirements.txt`

### Port already in use
```bash
# Find process using port
lsof -ti:8000  # or 5174

# Kill process
kill -9 <PID>
```

## Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [PrimeVue Documentation](https://primevue.org/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
