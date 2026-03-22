# MaplePulse — Deployment Guide

## Infrastructure

| | |
|---|---|
| **Server** | Hetzner Cloud — `46.62.255.66` |
| **User** | `sri` |
| **SSH Key** | `~/.ssh/id_hetzner` |
| **App Directory** | `~/maplepulse/` (i.e. `/home/sri/maplepulse/`) |
| **Domain** | `maplepulse.sshub.dev` |
| **Reverse Proxy** | Nginx + Certbot (Let's Encrypt) |
| **DNS** | Cloudflare |

---

## Step 1 — Cloudflare DNS Setup

Before deploying, you need the DNS record pointing to your server.

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select the **sshub.dev** domain
3. Go to **DNS** → **Records**
4. Click **Add Record**:
   - **Type:** `A`
   - **Name:** `maplepulse`
   - **IPv4 address:** `46.62.255.66`
   - **Proxy status:** OFF (grey cloud icon) — Certbot handles SSL directly
   - **TTL:** Auto
5. Click **Save**

> **Note:** If you prefer Cloudflare's CDN/DDoS protection (orange cloud ON), go to
> **SSL/TLS** → **Overview** and set the mode to **Full (Strict)** so Cloudflare
> trusts the Let's Encrypt certificate that Certbot provisions on the server.

To verify DNS propagation:

```bash
nslookup maplepulse.sshub.dev
# Should return 46.62.255.66
```

---

## Step 2 — Set Up the .env File on the Server

The `.env` file lives on the server only — the deploy script does **not** sync it.
This keeps your API keys safe and prevents accidental overwrites.

SSH into the server and create the file:

```bash
ssh -i ~/.ssh/id_hetzner sri@46.62.255.66
nano ~/maplepulse/.env
```

Paste in the following (fill in your real keys):

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-your-real-key-here

# Langfuse observability
LANGFUSE_SECRET_KEY=sk-lf-your-real-key-here
LANGFUSE_PUBLIC_KEY=pk-lf-your-real-key-here
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

Save with `Ctrl+O`, exit with `Ctrl+X`.

---

## Step 3 — First Deploy Setup (one-time, requires sudo)

After your first `bash push.sh`, SSH into the server to set up Nginx and SSL:

```bash
ssh -i ~/.ssh/id_hetzner sri@46.62.255.66
sudo cp ~/maplepulse/nginx-maplepulse.conf /etc/nginx/sites-available/maplepulse
sudo ln -sf /etc/nginx/sites-available/maplepulse /etc/nginx/sites-enabled/maplepulse
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d maplepulse.sshub.dev
```

This only needs to be done once. After this, all future deploys are just `bash push.sh`.

---

## Step 4 — Push & Deploy

Every time you want to push changes to production, run from your local machine:

```bash
cd "d:/Python Applications/Canada Personas"
bash push.sh
```

### What push.sh does

1. **Packs** your project files into a tar archive (excludes `.git`, `node_modules`, `.env`, dev files)
2. **Uploads** the archive to the server via `scp`
3. **Extracts** files into `~/maplepulse/` on the server
4. **Builds** production Docker images (multi-stage Dockerfiles)
5. **Starts** the containers (backend on `:8100`, frontend on `:8101`, localhost-only)

### Expected output

```
▸ Packing project files ...
  Archive size: 4.3M
▸ Uploading to server ...
▸ Extracting on server ...
▸ Building & starting containers (this may take a few minutes) ...
  [+] Building backend ...
  [+] Building frontend ...
  [+] Running 2/2
   ✔ Container maplepulse-backend-1   Started
   ✔ Container maplepulse-frontend-1  Started

✓ Pushed & deployed → https://maplepulse.sshub.dev
```

### Subsequent deploys

Just run `bash push.sh` again. Docker caches unchanged layers, so rebuilds are fast.

---

## Architecture

```
Internet
  │
  ▼
Cloudflare DNS (maplepulse.sshub.dev → 46.62.255.66)
  │
  ▼
Nginx (ports 80/443, SSL termination via Certbot)
  ├── /api/*        → 127.0.0.1:8100  (FastAPI backend)
  ├── /health       → 127.0.0.1:8100
  ├── /docs         → 127.0.0.1:8100
  └── /*            → 127.0.0.1:8101  (Next.js frontend)

Docker Compose (docker-compose.prod.yml)
  ├── backend   python:3.12-slim  → port 8000 → exposed as 127.0.0.1:8100
  └── frontend  node:22-alpine    → port 3000 → exposed as 127.0.0.1:8101
```

---

## Project Files for Deployment

| File | What it does |
|------|-------------|
| `push.sh` | Deploy script — tar + scp + docker compose build + up |
| `docker-compose.prod.yml` | Production compose file (backend + frontend) |
| `backend/Dockerfile.prod` | Multi-stage Python build for production |
| `frontend/Dockerfile.prod` | Multi-stage Next.js standalone build for production |
| `nginx-maplepulse.conf` | Nginx reverse proxy config with SSE streaming support |
| `.env.example` | Template for required environment variables |
| `backend/.dockerignore` | Excludes dev files from backend Docker image |
| `frontend/.dockerignore` | Excludes dev files from frontend Docker image |

---

## Common Operations

All commands below assume you are SSH'd into the server:

```bash
ssh -i ~/.ssh/id_hetzner sri@46.62.255.66
cd ~/maplepulse
```

### View logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Backend only
docker compose -f docker-compose.prod.yml logs -f backend

# Frontend only
docker compose -f docker-compose.prod.yml logs -f frontend

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail 100 backend
```

### Check status

```bash
docker compose -f docker-compose.prod.yml ps
```

Or from your local machine:

```bash
ssh -i ~/.ssh/id_hetzner sri@46.62.255.66 \
  "cd ~/maplepulse && docker compose -f docker-compose.prod.yml ps"
```

### Restart services

```bash
docker compose -f docker-compose.prod.yml restart

# Restart just the backend
docker compose -f docker-compose.prod.yml restart backend
```

### Stop the app

```bash
docker compose -f docker-compose.prod.yml down
```

### Rebuild a single service

```bash
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d backend
```

### View Nginx logs

```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Renew SSL certificate

Certbot auto-renews via a systemd timer, but to test manually:

```bash
sudo certbot renew --dry-run
```

### Check disk usage

```bash
df -h
docker system df
```

### Clean up old Docker images

```bash
docker image prune -a
```

---

## Environment Variables Reference

### Required

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | API key for LLM calls via OpenRouter |
| `LANGFUSE_SECRET_KEY` | Langfuse observability (server-side) |
| `LANGFUSE_PUBLIC_KEY` | Langfuse observability (client-side) |
| `LANGFUSE_HOST` | Langfuse endpoint URL |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `PERSONA_DB_PATH` | `/app/db/personas.db` | SQLite database path inside container |
| `CACHE_TTL_HOURS` | `24` | How long panel cache entries last |
| `PANEL_USE_AGENT` | `false` | Enable agentic panel builder |
| `PANEL_AGENT_MODEL` | `openai/gpt-5.4-mini` | Model for panel subagents |
| `PANEL_ORCHESTRATOR_MODEL` | `openai/gpt-5.4-mini` | Model for panel orchestrator |

---

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker compose -f docker-compose.prod.yml logs backend

# Check if port is already in use
sudo lsof -i :8100
sudo lsof -i :8101
```

### Nginx returns 502 Bad Gateway

The backend or frontend container isn't running or hasn't finished starting:

```bash
docker compose -f docker-compose.prod.yml ps
# Make sure both services show "Up" status

# Check backend health
curl http://127.0.0.1:8100/health
```

### SSL certificate issues

```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Re-run certbot from scratch
sudo certbot --nginx -d maplepulse.sshub.dev
```

### "Permission denied" on deploy

The app directory should be owned by `sri`:

```bash
ls -la ~/maplepulse/
# If owned by root, fix with:
sudo chown -R sri:sri ~/maplepulse
```

### push.sh fails to connect

```bash
# Test SSH connection first
ssh -i ~/.ssh/id_hetzner sri@46.62.255.66 echo "connected"

# If key is not found, check the path
ls -la ~/.ssh/id_hetzner
```
