# GitHub Actions Workflows

## Workflows Overview

### 1. CI Pipeline (`ci.yml`)

**Triggers:**
- Push to `dev`, `main`, or `feature/*` branches
- Pull requests to `dev` or `main`

**Jobs:**
1. **build-and-test**: Build Docker images for all 4 services in parallel
2. **integration-test**: Start all services with docker-compose and test health
3. **lint**: Check docker-compose syntax and Dockerfiles
4. **build-summary**: Generate summary report

**Duration:** ~5-10 minutes

---

### 2. CD Pipeline (`cd.yml`)

**Triggers:**
- Push to `main` branch (auto deploy)
- Manual workflow dispatch

**Jobs:**
1. **deploy**: SSH to VPS, pull code, rebuild containers

**Requirements:**
- VPS setup with Docker installed
- GitHub Secrets configured (see below)

**Duration:** ~3-5 minutes

---

## Setup Instructions

### For CI (works immediately, no setup needed)

CI workflow works out of the box! Just push code and GitHub Actions will:
- ✅ Build all Docker images
- ✅ Test services start correctly
- ✅ Run linting

### For CD (requires VPS setup)

1. **Setup VPS:**
   ```bash
   # SSH to VPS
   ssh root@your-vps-ip

   # Install Docker
   curl -fsSL https://get.docker.com | sh

   # Clone repository
   cd /app
   git clone https://github.com/YOUR_USERNAME/uit-ai-assistant.git
   cd uit-ai-assistant

   # Create .env.prod files for all services
   cp apps/api-gateway/.env.dev apps/api-gateway/.env.prod
   cp apps/agent/.env.dev apps/agent/.env.prod
   cp apps/mcp-server/.env.dev apps/mcp-server/.env.prod
   # Edit with production values...
   ```

2. **Generate SSH key for GitHub Actions:**
   ```bash
   # On your local machine
   ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github-actions

   # Copy public key to VPS
   ssh-copy-id -i ~/.ssh/github-actions.pub user@your-vps-ip

   # Get private key content
   cat ~/.ssh/github-actions
   ```

3. **Add GitHub Secrets:**

   Go to: `https://github.com/YOUR_USERNAME/uit-ai-assistant/settings/secrets/actions`

   Add these secrets:
   - `VPS_HOST`: Your VPS IP address (e.g., `123.45.67.89`)
   - `VPS_USER`: SSH username (e.g., `root` or `ubuntu`)
   - `VPS_SSH_KEY`: Private key content from step 2
   - `VPS_PORT`: SSH port (default: `22`)

4. **Test deployment:**
   ```bash
   # Push to main branch
   git push origin main

   # Or trigger manually
   # Go to: Actions → CD Pipeline → Run workflow
   ```

---

## Monitoring

### View workflow runs:
- Go to: `https://github.com/YOUR_USERNAME/uit-ai-assistant/actions`
- Click on workflow name to see details

### Common issues:

**CI fails on build:**
- Check Dockerfile syntax
- Verify dependencies in pyproject.toml/package.json/go.mod

**CD fails on deploy:**
- Verify GitHub Secrets are correct
- Check VPS is accessible: `ssh user@vps-ip`
- Check Docker is installed on VPS: `docker --version`
- Check project path exists: `/app/uit-ai-assistant`

---

## Future Enhancements

- [ ] Add Docker Hub/GHCR image push
- [ ] Add automated testing (unit tests, e2e tests)
- [ ] Add deployment to staging environment
- [ ] Add rollback on deployment failure
- [ ] Add Slack/Discord notifications
- [ ] Add database migration step
- [ ] Add health check after deployment

---

## Workflow Status Badges

Add to main README.md:

```markdown
[![CI Pipeline](https://github.com/YOUR_USERNAME/uit-ai-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/uit-ai-assistant/actions/workflows/ci.yml)
[![CD Pipeline](https://github.com/YOUR_USERNAME/uit-ai-assistant/actions/workflows/cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/uit-ai-assistant/actions/workflows/cd.yml)
```
