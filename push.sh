#!/usr/bin/env bash
# MaplePulse — Push & deploy to production
# Run: bash push.sh
set -euo pipefail

SERVER="sri@46.62.255.66"
SSH_KEY="$HOME/.ssh/id_hetzner"
APP_DIR="/home/sri/maplepulse"
SSH_CMD="ssh -i $SSH_KEY $SERVER"

# ── Pack only the needed project files ───────────────────────────────
echo "▸ Packing project files ..."
TAR_FILE=$(mktemp /tmp/maplepulse-XXXXXX.tar.gz)
tar czf "$TAR_FILE" \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='backend/db' \
  -C "$(pwd)" \
  backend/Dockerfile.prod \
  backend/main.py \
  backend/panel_engine.py \
  backend/canada_demographics_2021.py \
  backend/requirements.txt \
  backend/.dockerignore \
  frontend/Dockerfile.prod \
  frontend/package.json \
  frontend/next.config.ts \
  frontend/tsconfig.json \
  frontend/postcss.config.mjs \
  frontend/.dockerignore \
  frontend/src \
  frontend/public \
  docker-compose.prod.yml \
  nginx-maplepulse.conf \
  data/personas_5000.json \
  data/personas_5000.meta.json \
  data/personas_5000_enriched.json \
  data/occupation_noc_mapping.json \
  data/raw \
  canada_demographics_2021.py \
  .env.example

echo "  Archive size: $(du -h "$TAR_FILE" | cut -f1)"

# ── Upload and extract ───────────────────────────────────────────────
echo "▸ Uploading to server ..."
scp -i "$SSH_KEY" "$TAR_FILE" "$SERVER:/tmp/maplepulse-upload.tar.gz"
rm -f "$TAR_FILE"

echo "▸ Extracting on server ..."
$SSH_CMD "mkdir -p $APP_DIR && cd $APP_DIR && tar xzf /tmp/maplepulse-upload.tar.gz && rm -f /tmp/maplepulse-upload.tar.gz"

# ── Build and start containers ───────────────────────────────────────
echo "▸ Building & starting containers (this may take a few minutes) ..."
$SSH_CMD "cd $APP_DIR && docker compose -f docker-compose.prod.yml build --no-cache && docker compose -f docker-compose.prod.yml up -d --remove-orphans && docker compose -f docker-compose.prod.yml ps"

echo ""
echo "✓ Pushed & deployed → https://maplepulse.sshub.dev"
echo ""
echo "NOTE: First deploy only — SSH in and run:"
echo "  sudo cp $APP_DIR/nginx-maplepulse.conf /etc/nginx/sites-available/maplepulse"
echo "  sudo ln -sf /etc/nginx/sites-available/maplepulse /etc/nginx/sites-enabled/maplepulse"
echo "  sudo nginx -t && sudo systemctl reload nginx"
echo "  sudo certbot --nginx -d maplepulse.sshub.dev"
