# Release Management Guide

## Overview

V3Trading uses **tag-based releases** with semantic versioning. Deployments are triggered only when you create and push version tags, giving you full control over when code goes to production.

**What happens when you push a tag:**
- ✅ Deploys to production VPS
- ✅ Tags Docker images with version number
- ✅ **Creates GitHub Release** with changelog and download links
- ✅ Records deployment version on server

## Quick Start

```bash
# 1. Ensure your code is ready and committed
git add .
git commit -m "Prepare release v1.0.0"
git push origin master

# 2. Create and push a version tag
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial production release"
git push origin v1.0.0

# 3. Watch deployment in GitHub Actions
# Go to: https://github.com/your-username/v3trading/actions

# 4. View the created release
# Go to: https://github.com/your-username/v3trading/releases
```

That's it! The deployment will automatically start and a GitHub Release will be created with your changelog.

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/) format: `vMAJOR.MINOR.PATCH`

### Version Format: `v1.2.3`

- **MAJOR** (1.x.x) - Breaking changes, incompatible API changes
- **MINOR** (x.2.x) - New features, backward-compatible
- **PATCH** (x.x.3) - Bug fixes, backward-compatible

### Examples

```bash
v1.0.0  # First production release
v1.0.1  # Bug fix release
v1.1.0  # New feature added
v2.0.0  # Major update with breaking changes
```

### When to Increment Each Number

**MAJOR (v2.0.0):**
- Removed or renamed API endpoints
- Changed authentication method
- Database schema breaking changes
- Any change that requires user action

**MINOR (v1.1.0):**
- Added new API endpoints
- Added new features
- New trading functionality
- Performance improvements

**PATCH (v1.0.1):**
- Bug fixes
- Security patches
- Documentation updates
- Minor UI fixes

## Creating a Release

### Step 1: Prepare Your Code

```bash
# Make sure all changes are committed
git status

# If you have uncommitted changes
git add .
git commit -m "Fix: Resolve issue with position calculations"
git push origin master
```

### Step 2: Create a Tag

**Annotated tag (recommended):**
```bash
git tag -a v1.0.0 -m "Release version 1.0.0

Changes:
- Implemented Google OAuth authentication
- Added mock trading API
- Created Docker deployment pipeline
"
```

**Lightweight tag (simpler):**
```bash
git tag v1.0.0
```

### Step 3: Push the Tag

```bash
git push origin v1.0.0
```

This will automatically trigger the deployment workflow!

### Step 4: Monitor Deployment

1. Go to GitHub → Actions tab
2. You'll see "Deploy to VPS" workflow running
3. Click on it to see real-time logs
4. Wait for all steps to complete (usually 2-5 minutes)

### Step 5: Verify Deployment

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Check deployed version
cd ~/v3trading
cat .deployment-version

# Check running containers
docker compose ps

# Check Docker image tags
docker images | grep v3trading
```

You should see images tagged with your version number!

## Manual Deployment (Emergency)

If you need to deploy without creating a tag:

1. Go to GitHub → Actions tab
2. Click "Deploy to VPS" workflow
3. Click "Run workflow" button
4. Select branch and click "Run workflow"

This creates a deployment tagged as `manual-YYYYMMDD-HHMMSS`.

## Rollback to Previous Version

If something goes wrong, rollback to a previous release:

```bash
# SSH into VPS
ssh user@your-vps-ip
cd ~/v3trading

# See available versions
git tag -l

# Checkout previous version
git fetch --tags
git checkout v1.0.0

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Verify
cat .deployment-version
```

## Viewing Release History

### List All Releases

```bash
# List all tags
git tag -l

# List tags with messages
git tag -l -n9
```

### View Specific Release

```bash
# Show tag details
git show v1.0.0

# Show commits in a release
git log v1.0.0..v1.1.0 --oneline
```

### On GitHub

Go to: `https://github.com/your-username/v3trading/releases`

**GitHub Releases are automatically created** when you push a tag. Each release includes:
- 📝 Auto-generated changelog from commits
- 🔗 Links to deployment and API documentation
- 📦 Downloadable source code archives (.zip, .tar.gz)
- 📊 Deployment timestamp and commit information
- 🏷️ Version tag reference

## Best Practices

### Before Creating a Release

- ✅ Run and test locally
- ✅ Ensure all tests pass (when you add tests)
- ✅ Update CLAUDE.MD with any new features
- ✅ Review recent commits for quality
- ✅ Ensure Google OAuth credentials are correct

### Tag Naming

- ✅ Use `v` prefix: `v1.0.0` (not `1.0.0`)
- ✅ Use semantic versioning: `vMAJOR.MINOR.PATCH`
- ✅ Always use 3 numbers: `v1.0.0` (not `v1.0` or `v1`)

### Tag Messages

**Good:**
```bash
git tag -a v1.2.0 -m "Release v1.2.0 - WebSocket Support

Features:
- Added real-time price updates via WebSocket
- Improved position tracking performance

Bug Fixes:
- Fixed OAuth redirect loop issue
- Resolved Docker build cache problem
"
```

**Bad:**
```bash
git tag v1.2.0  # No message
git tag -a v1.2.0 -m "updates"  # Too vague
```

### Release Frequency

**Development Phase:**
- Release often (daily/weekly)
- Use PATCH versions for quick fixes
- Don't worry about breaking changes

**Production Phase:**
- Release when ready (weekly/monthly)
- Be more careful with MAJOR versions
- Test thoroughly before releasing

## Common Scenarios

### Scenario: You Made a Mistake in a Tag

```bash
# Delete tag locally
git tag -d v1.0.0

# Delete tag remotely
git push origin :refs/tags/v1.0.0

# Create corrected tag
git tag -a v1.0.0 -m "Corrected release message"
git push origin v1.0.0
```

### Scenario: You Want to Tag an Older Commit

```bash
# Find the commit hash
git log --oneline

# Tag specific commit
git tag -a v1.0.0 abc123 -m "Release v1.0.0"
git push origin v1.0.0
```

### Scenario: Deploy to Production for First Time

```bash
# Your first tag should be v1.0.0
git tag -a v1.0.0 -m "Initial production release"
git push origin v1.0.0
```

### Scenario: Hotfix in Production

```bash
# Fix the bug
git commit -m "Hotfix: Critical security patch"
git push origin master

# Create patch release
git tag -a v1.0.1 -m "Hotfix: Security patch for authentication"
git push origin v1.0.1
```

## Troubleshooting

### Tag Push Doesn't Trigger Deployment

**Check:**
1. Tag format: Must be `v*.*.*` (e.g., `v1.0.0`)
2. GitHub Actions enabled in repository settings
3. Workflow file exists: `.github/workflows/deploy.yml`
4. GitHub Secrets configured correctly

### Wrong Version Deployed

```bash
# Check what tag you're on
git describe --tags

# Check what's on VPS
ssh user@vps 'cd ~/v3trading && git describe --tags'
```

### Need to See Deployment Logs

1. GitHub → Actions → Select failed workflow
2. Click on failed step to see detailed logs
3. Or SSH to VPS: `docker compose logs -f`

## Additional Resources

- [Semantic Versioning](https://semver.org/)
- [Git Tagging Documentation](https://git-scm.com/book/en/v2/Git-Basics-Tagging)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Questions?** Check CLAUDE.MD for detailed technical documentation.
