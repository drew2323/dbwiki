# DBWiki

A self-hosted wiki / CMS in the spirit of Confluence: spaces, a hierarchical page tree, a rich text editor with
autosave, a draft → publish workflow with version history, attachments and full text search.
Python FastAPI backend, Vue 3 + TypeScript frontend, PostgreSQL.

## 🚀 Features

**Content**
- **Spaces** (public or private) with a drag & drop **page tree**, breadcrumbs, outline and backlinks
- **Tiptap editor**: headings, lists, tables, code, links, images; **autosave** every few seconds with
  ETag conflict detection (HTTP 409 when someone else changed the draft)
- **Draft / publish workflow**, version history, restore, and **version comparison** (line + word diff, authors)
- **Page operations**: create from **templates**, rename, duplicate, archive or permanently delete (with sub-pages)
- **Attachments**: upload / drag & drop, image thumbnails, insert into pages, per-space deduplication
- **Favorites** and a per-space **activity feed**

**Search**
- **Ctrl/Cmd+K palette**: title + content search (prefix aware, ranked), scope "this space / all spaces",
  favorites and recently opened pages

**Users and access**
- Email/password (bcrypt) and **Google OAuth**, multiple identities per user, JWT in httpOnly cookies
- Users belong to spaces with a role: `read`, `edit`, `admin` (plus a global superuser flag)
- Public spaces are readable without login (published content only); drafts and archived pages are editor-only
- Admin area (`/admin`) for users, roles and spaces

## 🛠 Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic, AuthLib, python-jose, bcrypt |
| Database | PostgreSQL 16 (full text search, JSONB drafts) |
| Frontend | Vue 3, TypeScript, Vite, Pinia, Vue Router, PrimeVue 4, Tailwind CSS, Tiptap 3 |
| Tests | pytest (API against real PostgreSQL), vitest (frontend units) |
| Deployment | Docker Compose (nginx + backend + frontend + postgres), GitHub Actions |

## 📁 Project structure

```
dbwiki/
├── backend/
│   ├── app/
│   │   ├── routers/        # auth, users, roles, spaces, pages, tree, attachments, ...
│   │   ├── crud/           # database logic
│   │   ├── dependencies/   # auth + space access checks (access.py)
│   │   ├── models/         # SQLAlchemy models + Pydantic schemas
│   │   └── utils/          # auth helpers, page templates
│   ├── alembic/versions/   # database migrations
│   ├── tests/              # pytest API tests
│   └── main.py
├── frontend/
│   └── src/
│       ├── views/cms/      # Space, SpaceHome, PageView
│       ├── components/cms/ # PageTree, TiptapEditor, SearchPalette, PageAttachments, VersionDiffDialog, ...
│       ├── components/admin/, layout/, stores/, services/, composables/, utils/
├── docs/                   # architecture, auth, deployment, development, status
├── nginx/                  # reverse proxy config
└── docker-compose.yml
```

> The frontend still contains the PrimeVue/Sakai demo pages (`/admin/uikit/*`, `/admin/demo/*`);
> the `trades` / `positions` backend routers are leftovers from the project the template came from.

## 🔧 Setup

### Prerequisites
- Python 3.11+ (3.13 works), Node.js 18+ (22 recommended), PostgreSQL 14+
- Optional: Google Cloud OAuth credentials for "Sign in with Google"

### Database
```bash
createdb dbwiki      # or use any PostgreSQL database you like
```

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env     # set DATABASE_URL, JWT_SECRET_KEY, (Google keys)
alembic upgrade head     # create / update the schema
python -m uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Google OAuth (optional)
1. Create OAuth 2.0 credentials in the [Google Cloud Console](https://console.cloud.google.com/)
2. Authorized JavaScript origins: `http://localhost:5173`, `http://localhost:8000`
3. Authorized redirect URI: `http://localhost:8000/api/auth/callback`
4. Put client id/secret into `backend/.env`

### Environment variables (`backend/.env`)
| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg://user:pw@localhost:5432/dbwiki` | local `dbwiki` DB |
| `JWT_SECRET_KEY` | signs login cookies and sessions (min. 32 chars) | - |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth | - |
| `BACKEND_URL`, `FRONTEND_URL` | used for OAuth redirects | `http://localhost:8000` / `:5173` |
| `CORS_ORIGINS` | comma separated allowed origins | `http://localhost:5173` |
| `UPLOAD_DIR` | where attachments are stored | `/tmp/uploads` (Docker: `/app/uploads` volume) |
| `MAX_UPLOAD_MB` | max attachment size | `25` |
| `SMTP_*` | email (verification / password reset) | - |

## 🌐 Access points

- **App**: http://localhost:5173
- **API**: http://localhost:8000, interactive docs at http://localhost:8000/docs

## 🎯 First steps

1. Register at `/auth/register` and log in.
2. Make yourself superuser (the first user has to be promoted in the database):
   `UPDATE users SET is_superuser = true WHERE email = 'you@example.com';`
3. Open `/admin/spaces`, create a space (tick *public* to list it on the landing page).
4. Open `/<space-key>`, create a page (pick a template), **Edit Mode** → write → **Publish**.
5. Press **Ctrl/Cmd+K** to search; star pages to find them quickly.

Keyboard shortcuts on a page: `Ctrl+E` edit, `Ctrl+S` save draft, `Ctrl+Shift+P` publish, `Ctrl+H` history.

## 📚 API overview

Full, interactive reference: `/docs`. Main groups:

| Prefix | What |
|---|---|
| `/api/auth/*` | register, login, logout, me, Google OAuth, password reset |
| `/api/users`, `/api/roles`, `/api/auth-identities` | administration |
| `/api/spaces` | spaces, `GET /by-key/{key}` (with `can_edit`), `GET /{id}/activity`, memberships, public discovery |
| `/api/pages` | create (optionally `template_id`), get, rename/archive (`PATCH`), delete, `POST /{id}/duplicate`, `GET /templates` |
| `/api/pages/{id}/draft` | read / autosave draft (ETag, `If-Match`) |
| `/api/pages/{id}/publish`, `/versions`, `/restore` | versions |
| `/api/pages/search`, `/api/pages/favorites/me`, `/api/pages/{id}/favorite` | search and favorites |
| `/api/tree/space/{id}`, `/api/tree/node/*` | page tree, move, reorder |
| `/api/attachments/upload`, `/{id}/file`, `/page/{id}/list` | uploads and downloads |

Read endpoints work without login for public spaces; write endpoints need the `edit` / `admin` role in the
space (or being its creator / a superuser).

## 🧪 Tests

```bash
# Backend: API + access control tests against a migrated PostgreSQL (DATABASE_URL)
cd backend && pip install -r requirements-dev.txt && pytest tests

# Frontend: unit tests (safe renderer, diff)
cd frontend && npm test
```

The backend tests create uniquely named data, so a development database can be reused - never run them
against production. GitHub Actions (`.github/workflows/tests.yml`) runs both suites plus a frontend build.

## 📖 Documentation

- [docs/QUICK_START_NEXT_SESSION.md](./docs/QUICK_START_NEXT_SESSION.md) - quick start and file map
- [docs/CMS_IMPLEMENTATION_STATUS.md](./docs/CMS_IMPLEMENTATION_STATUS.md) - what is implemented, bug history, optional ideas
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md), [docs/AUTHENTICATION.md](./docs/AUTHENTICATION.md),
  [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md), [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md),
  [docs/UI_FRAMEWORK.md](./docs/UI_FRAMEWORK.md), [docs/RELEASES.md](./docs/RELEASES.md)
- [CLAUDE.MD](./CLAUDE.MD) - project notes for AI assisted development

## 🚢 Deployment

### Docker Deployment

The project includes Docker support with multi-stage builds and GitHub Actions CI/CD.

#### Local Docker Build
```bash
# Build and run with docker-compose (migrations run automatically on backend start)
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

Attachments are stored in the `uploads-data` Docker volume (`UPLOAD_DIR=/app/uploads`); nginx allows
request bodies up to 30 MB on `/api/`. Back up this volume together with the database.

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
