#!/usr/bin/env bash
# MaplePulse — Deploy to Hetzner (sshub.dev)
# Usage: bash deploy.sh
# Runs from your local Windows machine (Git Bash or Claude Code terminal)
set -euo pipefail

SERVER="sri@46.62.255.66"
SSH_KEY="$HOME/.ssh/id_hetzner"
APP_DIR="/opt/maplepulse"
SSH_CMD="ssh -i $SSH_KEY $SERVER"

# ── Step 1: Create app directory on server ───────────────────────────
echo "▸ Preparing server directory ..."
$SSH_CMD "sudo mkdir -p $APP_DIR && sudo chown sri:sri $APP_DIR"

# ── Step 2: Pack project, excluding dev/secret files ─────────────────
echo "▸ Packing project files ..."
TAR_FILE=$(mktemp /tmp/maplepulse-XXXXXX.tar.gz)
tar czf "$TAR_FILE" \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data/experiments' \
  --exclude='.env' \
  --exclude='.env.local' \
  --exclude='Dockerfile' \
  --exclude='docker-compose.yml' \
  --exclude='Caddyfile' \
  --exclude='backend/db' \
  -C "$(pwd)" .

echo "  Archive size: $(du -h "$TAR_FILE" | cut -f1)"

# ── Step 3: Upload and extract ───────────────────────────────────────
echo "▸ Uploading to $SERVER:$APP_DIR ..."
scp -i "$SSH_KEY" "$TAR_FILE" "$SERVER:/tmp/maplepulse-upload.tar.gz"
rm -f "$TAR_FILE"

$SSH_CMD bash -s <<'REMOTE'
  set -euo pipefail
  cd /opt/maplepulse

  # Extract (preserve .env on server)
  tar xzf /tmp/maplepulse-upload.tar.gz
  rm -f /tmp/maplepulse-upload.tar.gz
  echo "  Files extracted to /opt/maplepulse"
REMOTE

# ── Step 4: Build and start containers ───────────────────────────────
echo "▸ Building & starting containers on server ..."
$SSH_CMD bash -s <<'REMOTE'
  set -euo pipefail
  cd /opt/maplepulse

  # Build and deploy
  docker compose -f docker-compose.prod.yml build --no-cache
  docker compose -f docker-compose.prod.yml up -d --remove-orphans

  # Install nginx config if not already present
  if [ ! -f /etc/nginx/sites-available/maplepulse ]; then
    sudo cp nginx-maplepulse.conf /etc/nginx/sites-available/maplepulse
    sudo ln -sf /etc/nginx/sites-available/maplepulse /etc/nginx/sites-enabled/maplepulse
    sudo nginx -t && sudo systemctl reload nginx
    echo "▸ Nginx config installed. Getting SSL cert..."
    sudo certbot --nginx -d maplepulse.sshub.dev --non-interactive --agree-tos --redirect
  else
    echo "▸ Nginx config already exists, skipping..."
  fi

  echo ""
  echo "✓ MaplePulse deployed!"
  docker compose -f docker-compose.prod.yml ps
REMOTE

echo ""
echo "✓ Deploy complete → https://maplepulse.sshub.dev"
