# GitHub Actions Secrets Required for Deployment

Add these secrets to your GitHub repository: **Settings → Secrets and variables → Actions → New repository secret**

## VPS Connection Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `VPS_HOST` | VPS server hostname or IP | `123.45.67.89` or `example.com` |
| `VPS_USERNAME` | SSH username for VPS | `ubuntu` or `root` |
| `VPS_SSH_KEY` | Private SSH key for authentication | (entire contents of `~/.ssh/id_rsa`) |

## Application Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `FRONTEND_URL` | Public URL of your application | `https://dbwiki.com` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `123456789-abc.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | `GOCSPX-abc123def456` |
| `JWT_SECRET_KEY` | JWT signing key (min 32 chars) | `your-super-secret-key-min-32-characters-long` |

## Database Secrets (NEW - Required for PostgreSQL)

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://dbwiki:STRONG_PASSWORD@postgres:5432/dbwiki` |
| `POSTGRES_USER` | PostgreSQL username | `dbwiki` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `STRONG_RANDOM_PASSWORD_HERE` |
| `POSTGRES_DB` | PostgreSQL database name | `dbwiki` |

## Important Notes:

### DATABASE_URL Format
For Docker deployment, use the internal service name `postgres` as the host:
```
postgresql+psycopg://[POSTGRES_USER]:[POSTGRES_PASSWORD]@postgres:5432/[POSTGRES_DB]
```

**Example:**
```
DATABASE_URL=postgresql+psycopg://dbwiki:mySecureP@ssw0rd@postgres:5432/dbwiki
POSTGRES_USER=dbwiki
POSTGRES_PASSWORD=mySecureP@ssw0rd
POSTGRES_DB=dbwiki
```

### Security Best Practices:
1. **PostgreSQL Password**: Use a strong random password (20+ characters)
2. **JWT Secret**: Generate with: `openssl rand -base64 48`
3. **SSH Key**: Never commit to git, only store in GitHub secrets
4. **Google OAuth**: Restrict to your domain in Google Cloud Console

### Generating Strong Passwords:
```bash
# PostgreSQL password
openssl rand -base64 32

# JWT secret key
openssl rand -base64 48
```

### SSH Key Setup:
```bash
# Generate new SSH key pair (if needed)
ssh-keygen -t ed25519 -C "github-actions-deploy"

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/id_ed25519.pub username@vps-host

# Copy private key content to GitHub secret VPS_SSH_KEY
cat ~/.ssh/id_ed25519
```

## What Changed in Deployment Pipeline:

### ✅ Automatic Database Migrations
- Backend Dockerfile now runs `alembic upgrade head` on startup
- Waits for PostgreSQL to be ready before starting
- Migrations run automatically on every deployment

### ✅ PostgreSQL Data Persistence
- Database data stored in Docker volume `postgres-data`
- Survives container restarts and updates
- Backup recommended before major migrations

### ✅ Environment Variables
- Backend container uses `.env` for app config
- Docker Compose uses root `.env` for PostgreSQL credentials
- Separation of concerns for security

## Deployment Flow:

1. Push tag: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions:
   - Copies code to VPS
   - Creates `.env` files from secrets
   - Runs `docker compose down`
   - Builds new images with `--no-cache`
   - Tags images with version
   - Runs `docker compose up -d`
3. Backend container startup:
   - Waits for PostgreSQL health check
   - Connects to database
   - Runs Alembic migrations
   - Starts FastAPI server
4. Services become healthy and ready

## Troubleshooting:

### Check deployment logs:
```bash
ssh user@vps-host
cd ~/v3trading
docker compose logs backend
docker compose logs postgres
```

### Manual migration run:
```bash
docker compose exec backend alembic upgrade head
```

### Database backup:
```bash
docker compose exec postgres pg_dump -U dbwiki dbwiki > backup.sql
```

### Database restore:
```bash
cat backup.sql | docker compose exec -T postgres psql -U dbwiki dbwiki
```
