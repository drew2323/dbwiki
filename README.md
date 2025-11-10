# V3Trading

A full-stack trading application with Python FastAPI backend and Vue 3 TypeScript frontend, featuring Google OAuth authentication and mock trading API.

## 🚀 Features

- **Google OAuth Authentication** - Secure login with Google accounts
- **Trading API** - Mock trading endpoints for trades and positions
- **Real-time State Management** - Pinia stores with TypeScript
- **Protected Routes** - Authentication guards for secure pages
- **RESTful API** - FastAPI with automatic OpenAPI documentation
- **Type Safety** - Full TypeScript on frontend, Pydantic on backend

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation with Python type hints
- **AuthLib** - OAuth 2.0 client implementation
- **python-jose** - JWT token handling

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe development
- **Vite** - Next generation frontend tooling
- **Pinia** - State management with Composition API
- **Axios** - HTTP client with interceptors
- **Vue Router** - Client-side routing with guards

## 📁 Project Structure

```
v3trading/
├── backend/
│   ├── app/
│   │   ├── dependencies/    # Auth dependencies
│   │   ├── models/          # Pydantic models
│   │   ├── routers/         # API endpoints
│   │   └── utils/           # Utilities (auth, mock data)
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                 # Your secrets (not in git)
│
└── frontend/
    ├── src/
    │   ├── components/      # Vue components
    │   ├── composables/     # Composition functions
    │   ├── router/          # Vue Router with auth guards
    │   ├── services/        # API service layer
    │   ├── stores/          # Pinia stores
    │   ├── types/           # TypeScript types
    │   └── views/           # Page components
    ├── vite.config.ts
    ├── tsconfig.json
    └── package.json
```

## 🔧 Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- Google Cloud Console project with OAuth credentials

### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add authorized JavaScript origins:
   - `http://localhost:5174`
   - `http://localhost:8000`
4. Add authorized redirect URI:
   - `http://localhost:8000/api/auth/callback`
5. Copy Client ID and Client Secret

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your Google OAuth credentials

# Run server
python -m uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## 🌐 Access Points

- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc

## 📚 API Endpoints

### Authentication
- `GET /api/auth/google` - Initiate Google OAuth flow
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/me` - Get current user (protected)
- `POST /api/auth/logout` - Logout user

### Trading
- `GET /api/trades` - List trades (paginated)
- `GET /api/trades/{id}` - Get single trade
- `POST /api/trades` - Create new trade
- `PATCH /api/trades/{id}/cancel` - Cancel trade

### Positions
- `GET /api/positions` - List all positions
- `GET /api/positions/{symbol}` - Get position by symbol
- `POST /api/positions/{symbol}/close` - Close position

## 🔐 Environment Variables

### Backend (`.env`)
```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
FRONTEND_URL=http://localhost:5174
```

### Frontend (optional `.env`)
```env
VITE_API_BASE_URL=/api
```

## 🎯 Usage

1. Start both backend and frontend servers
2. Navigate to http://localhost:5174
3. Click "Sign in with Google"
4. Authorize the application
5. After login, access the "Test API Integration" page
6. View and interact with mock trades and positions

## 🧪 Development Notes

- **Mock Data**: All trading data is in-memory and resets on server restart
- **User Storage**: Users are stored in-memory (not persisted)
- **Authentication**: JWT tokens stored in httpOnly cookies (7-day expiration)
- **CORS**: Configured for localhost development
- **Auto-reload**: Both servers support hot-reloading during development

## 📖 Documentation

For detailed documentation including architecture decisions, API examples, and troubleshooting, see [CLAUDE.MD](./CLAUDE.MD).

## 🚢 Deployment

### Docker Deployment

The project includes Docker support with multi-stage builds and GitHub Actions CI/CD.

#### Local Docker Build
```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### GitHub Actions CI/CD

**Release-Based Deployment** - Deployments are triggered by creating version tags.

**Quick Deploy:**
```bash
# Create and push a version tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

**Deployment Triggers:**
- ✅ **Tag Push**: `v*.*.*` (e.g., v1.0.0, v1.2.3) - Automatic deployment
- ✅ **Manual**: GitHub Actions UI - Emergency deployments
- ❌ **Master Branch**: No auto-deploy (prevents accidental production updates)

**Required GitHub Secrets:**
- `VPS_HOST` - Your VPS IP or hostname
- `VPS_USERNAME` - SSH username for VPS
- `VPS_SSH_KEY` - Private SSH key for authentication
- `GOOGLE_CLIENT_ID` - Production Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET` - Production Google OAuth Client Secret
- `JWT_SECRET_KEY` - Production JWT secret (min 32 chars)
- `FRONTEND_URL` - Production frontend URL (e.g., https://yourdomain.com)

**What Happens on Deployment:**
1. Tag pushed → GitHub Actions triggered
2. Version extracted from tag (e.g., `v1.0.0`)
3. Code synced to VPS via SSH/rsync
4. `.env` file created from GitHub Secrets
5. Docker images built and tagged with version
6. Services restarted with `docker compose up -d`
7. Deployment verified with health checks

📖 **Complete Release Guide:** See [docs/RELEASES.md](./docs/RELEASES.md) for semantic versioning, rollback procedures, and best practices.

#### VPS Setup

**1. Install Docker:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**2. Install Docker Compose:**
```bash
sudo apt-get update
sudo apt-get install -y docker-compose-plugin
```

**3. Configure Docker Permissions:**
```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Logout and login again, or run:
newgrp docker

# Verify
docker ps
docker compose version
```

**4. Configure Firewall:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
```

**5. Setup SSH Key Authentication:**
- Generate SSH key pair on your local machine (if you don't have one)
- Add public key to VPS: `~/.ssh/authorized_keys`
- Add private key to GitHub Secrets as `VPS_SSH_KEY`

**6. Configure GitHub Secrets:**

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:
- `VPS_HOST` - Your VPS IP (e.g., `123.45.67.89` or domain)
- `VPS_USERNAME` - SSH username (e.g., `root` or `ubuntu`)
- `VPS_SSH_KEY` - Complete private SSH key content
- `GOOGLE_CLIENT_ID` - Production Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET` - Production Google OAuth Client Secret
- `JWT_SECRET_KEY` - Secure random string (min 32 characters)
- `FRONTEND_URL` - VPS URL (e.g., `http://123.45.67.89` or `https://yourdomain.com`)

**7. Update Google OAuth Settings:**

In Google Cloud Console, add to your OAuth credentials:
- Authorized JavaScript origins: `http://YOUR_VPS_IP` (or your domain)
- Authorized redirect URIs: `http://YOUR_VPS_IP/api/auth/callback`

**Important Notes:**
- `CORS_ORIGINS` is automatically set to match `FRONTEND_URL`
- Without a domain, use `http://YOUR_VPS_IP` for `FRONTEND_URL`
- When you add SSL/domain, update to `https://yourdomain.com`
- **Deployment is tag-based** - push to master does NOT trigger deployment
- First deployment: Create tag `v1.0.0` after setting up secrets

#### Adding HTTPS/SSL (When Ready)

**Quick Steps:**
1. Point your domain DNS to VPS IP
2. Install certbot on VPS: `sudo apt-get install certbot`
3. Obtain certificates: `sudo certbot certonly --standalone -d yourdomain.com`
4. Update `docker-compose.yml` to mount `/etc/letsencrypt:/etc/letsencrypt:ro`
5. Edit `nginx/nginx.conf` - uncomment HTTPS server block
6. Edit `backend/app/routers/auth.py` - change `secure=False` to `secure=True`
7. Update GitHub Secret `FRONTEND_URL` to `https://yourdomain.com`
8. Update Google OAuth URLs to HTTPS
9. Deploy and test

**Detailed instructions:** See CLAUDE.MD "SSL/TLS Configuration" section for complete step-by-step guide including certificate auto-renewal setup.

### Manual Production Build

#### Frontend
```bash
cd frontend
npm run build
```

#### Backend
Update environment variables for production:
- Set `secure=True` for cookies (requires HTTPS)
- Update `FRONTEND_URL` to production domain
- Set `CORS_ORIGINS` to production domain(s)
- Generate a secure `JWT_SECRET_KEY`

## 🤝 Contributing

This is a development project. For major changes, please document your updates in CLAUDE.MD.

## 📝 License

Private project - All rights reserved

## 👤 Author

David P. Brazda - davidbrazda61@gmail.com
