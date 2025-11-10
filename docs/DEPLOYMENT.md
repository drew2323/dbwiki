# Deployment Documentation

## Docker Configuration

### Backend Dockerfile
- Multi-stage build for optimized image size
- Stage 1: Install dependencies with build tools
- Stage 2: Production runtime with minimal dependencies
- Non-root user for security
- Health check endpoint: `/health`
- Runs on port 8000 with uvicorn

### Frontend Dockerfile
- Multi-stage build: Node.js build + Nginx serve
- Stage 1: Build Vue app with Vite
- Stage 2: Serve static files with Nginx
- Custom nginx.conf for Vue Router history mode
- Gzip compression enabled
- Static asset caching with immutable headers
- Runs on port 80

### Docker Compose
- **Services**:
  - `backend`: FastAPI application
  - `frontend`: Nginx serving Vue build
  - `nginx`: Reverse proxy for both services
- **Network**: Bridge network for inter-container communication
- **Health Checks**: All services include health check definitions
- **Volumes**: Nginx config and SSL certificates mounted
- **Ports**:
  - 80 (HTTP)
  - 443 (HTTPS, when SSL configured)
  - 8000 (Backend direct access)

### Nginx Reverse Proxy
- Routes `/api/*` to backend container
- Routes `/` to frontend container
- Rate limiting:
  - API: 10 requests/second
  - Auth: 5 requests/minute
- Security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
- Gzip compression
- Health check endpoint: `/health`
- SSL/TLS ready (commented out, requires certificates)

## CI/CD Pipeline

### GitHub Actions Workflow (`.github/workflows/deploy.yml`)

**Triggers:**
- **Tag Push**: `v*.*.*` (e.g., v1.0.0, v1.2.3) - Primary deployment method
- **Manual**: workflow_dispatch - Emergency/manual deployments

**Deployment Strategy:**
- Automatic deployment ONLY on version tag creation
- No auto-deploy on master branch pushes (prevents accidental production deploys)
- Version extraction and Docker image tagging
- Deployment history tracking in `.deployment-version` file
- **Automatic GitHub Release creation** with changelog and download links

**Steps**:
1. **Checkout Code**: Clone repository
2. **Setup SSH**: Configure SSH key from secrets
3. **Create Deployment Directory**: Prepare VPS directory (`~/v3trading`)
4. **Sync Files**: rsync code to VPS (excludes .git, node_modules, __pycache__, venv, .env)
5. **Create .env**: Generate backend `.env` from GitHub Secrets (auto-includes CORS_ORIGINS from FRONTEND_URL)
6. **Deploy**: Run `docker compose down && build --no-cache && up -d`
7. **Verify**: Check service status with `docker compose ps`
8. **Cleanup**: Remove SSH keys for security

**Required GitHub Secrets**:
- `VPS_HOST`: VPS IP address or hostname
- `VPS_USERNAME`: SSH username
- `VPS_SSH_KEY`: Private SSH key (full content)
- `GOOGLE_CLIENT_ID`: Production Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET`: Production Google OAuth Secret
- `JWT_SECRET_KEY`: Production JWT secret (min 32 characters)
- `FRONTEND_URL`: Production frontend URL (e.g., https://yourdomain.com)

**Environment Injection**:
The workflow creates the `.env` file on the VPS during deployment from GitHub Secrets, ensuring secrets are never committed to the repository. `CORS_ORIGINS` is automatically set to match `FRONTEND_URL` value.

## Production Configuration

### Backend Environment Variables
```env
GOOGLE_CLIENT_ID=production-client-id
GOOGLE_CLIENT_SECRET=production-secret
JWT_SECRET_KEY=production-jwt-secret-min-32-chars
JWT_ALGORITHM=HS256
FRONTEND_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### CORS Configuration
Updated `main.py` to read `CORS_ORIGINS` from environment:
```python
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5174").split(",")
```

This allows multiple origins for production (e.g., with/without www).

### VPS Requirements
- Ubuntu/Debian Linux (recommended)
- Docker Engine installed
- docker-compose installed
- SSH access configured with public key authentication
- Firewall configured (ports 80, 443 open)
- Domain name pointed to VPS (optional, for SSL)

## Setup Guide

### 1. Prepare VPS
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Add user to docker group (replace with your username)
sudo usermod -aG docker $USER

# Logout and login, or run:
newgrp docker

# Verify installation
docker ps
docker compose version

# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
```

### 2. Setup SSH Keys
```bash
# On your local machine (if you don't have SSH keys)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to VPS
ssh-copy-id user@your_vps_ip

# Copy private key content for GitHub Secrets
cat ~/.ssh/id_ed25519
```

### 3. Configure GitHub Secrets
- Go to GitHub repo → Settings → Secrets and variables → Actions
- Add all required secrets (see list above)
- For `FRONTEND_URL` without domain: `http://YOUR_VPS_IP`

### 4. Update Google OAuth
- Go to Google Cloud Console → Credentials
- Add authorized JavaScript origin: `http://YOUR_VPS_IP`
- Add authorized redirect URI: `http://YOUR_VPS_IP/api/auth/callback`

### 5. Create First Release
See [RELEASES.md](./RELEASES.md) for complete release management guide.

## SSL/TLS Configuration (HTTPS)

When you're ready to add a domain with HTTPS, follow these steps:

### 1. Point Domain to VPS
- Configure DNS A record: `yourdomain.com` → VPS IP
- Configure DNS A record: `www.yourdomain.com` → VPS IP (optional)
- Wait for DNS propagation (can take up to 48 hours)

### 2. Obtain SSL Certificates (Let's Encrypt)
SSH into your VPS and run:
```bash
# Install certbot
sudo apt-get update
sudo apt-get install -y certbot

# Stop nginx temporarily (port 80 needs to be free)
cd ~/v3trading
docker compose stop nginx

# Obtain certificates
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Start nginx again
docker compose start nginx
```

Certificates will be saved to: `/etc/letsencrypt/live/yourdomain.com/`

### 3. Update Docker Compose Volumes
Edit `docker-compose.yml` to mount certificates:
```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro  # Add this line
```

### 4. Update Nginx Configuration
Edit `nginx/nginx.conf` and uncomment/update the HTTPS server block.

### 5. Update Backend Cookie Settings
Edit `backend/app/routers/auth.py` to set `secure=True` for cookies.

### 6. Update GitHub Secrets
Set `FRONTEND_URL=https://yourdomain.com`

### 7. Update Google OAuth Settings
Update authorized origins and redirect URIs with HTTPS URLs.

### 8. Setup Auto-Renewal
```bash
# Test renewal process
sudo certbot renew --dry-run

# Add cron job for auto-renewal
sudo crontab -e

# Add this line (runs twice daily):
0 0,12 * * * certbot renew --quiet --deploy-hook "cd /home/YOUR_USERNAME/v3trading && docker compose restart nginx"
```

## Deployment Workflow

### Release-Based Deployment
See [RELEASES.md](./RELEASES.md) for complete guide.

### Common Deployment Commands on VPS
```bash
# Check deployment status
cd ~/v3trading
docker compose ps

# View logs
docker compose logs -f
docker compose logs backend
docker compose logs frontend
docker compose logs nginx

# Restart services
docker compose restart

# Stop all services
docker compose down

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Check resource usage
docker stats

# Clean up
docker system prune -a
```

## Local Docker Testing (Optional)

**Note:** Requires Docker Desktop installed on macOS/Windows or Docker Engine on Linux.

```bash
# From project root
cd /path/to/v3trading

# Create local .env file for testing
cp backend/.env.example backend/.env
# Edit backend/.env with your development credentials

# Build and run
docker compose up -d

# View logs
docker compose logs -f

# Check service status
docker compose ps

# Restart specific service
docker compose restart backend

# Stop all services
docker compose down

# Rebuild specific service
docker compose build --no-cache backend
docker compose up -d backend
```

If you don't have Docker installed locally, you can skip local testing and deploy directly to VPS via GitHub Actions.

## Troubleshooting

### `docker-compose: command not found`
- Modern Docker uses `docker compose` (space, not hyphen)
- Install: `sudo apt-get install docker-compose-plugin`

### Permission denied on Docker socket
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login, or run:
newgrp docker

# Verify
docker ps
```

### GitHub Actions deployment fails
- Check GitHub Secrets are set correctly
- Verify VPS SSH key is the complete private key (including headers)
- Ensure VPS has Docker and docker-compose installed
- Check VPS has ports 80/443 open: `sudo ufw status`
- View GitHub Actions logs for detailed error messages

### Container won't start
```bash
# On VPS, check logs
cd ~/v3trading
docker compose logs backend
docker compose logs frontend
docker compose logs nginx

# Check container status
docker compose ps

# Restart specific service
docker compose restart backend
```

### OAuth callback fails in production
- Update Google Cloud Console with production URLs
- Verify `FRONTEND_URL` in GitHub Secrets matches your VPS IP/domain
- Check redirect URI: `http://YOUR_VPS_IP/api/auth/callback`
- Ensure `CORS_ORIGINS` allows your frontend URL
