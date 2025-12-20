#!/usr/bin/env bash
# deploy_nginx.sh
#
# Deploy nginx configuration from the aws-box repo clone into /etc/nginx.
# This is the ONLY supported way to update live nginx config.
#
# Properties:
# - Uses rsync to deploy whole nginx tree (no partial one-file drift)
# - Runs nginx -t before reload
# - Optionally removes default site (prevents catch-all serving wrong content)
#
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/home/admin/aws-box}"
SRC="${REPO_ROOT}/etc/nginx"
DEST="/etc/nginx"

log(){ echo "[deploy_nginx] $*"; }

if [ ! -d "$SRC" ]; then
  echo "[deploy_nginx] ERROR: source not found: $SRC" >&2
  exit 1
fi

log "Deploying nginx from $SRC -> $DEST"

# Deploy nginx tree
sudo rsync -a --delete \
  --exclude='*.bak' \
  --exclude='*.swp' \
  "$SRC/" "$DEST/"

# Ensure default site is not enabled (prevents wrong-site issues)
if [ -L /etc/nginx/sites-enabled/default ] || [ -f /etc/nginx/sites-enabled/default ]; then
  log "Removing /etc/nginx/sites-enabled/default"
  sudo rm -f /etc/nginx/sites-enabled/default
fi

log "Validating nginx config"
sudo nginx -t

log "Reloading nginx"
sudo systemctl reload nginx

log "Done."
