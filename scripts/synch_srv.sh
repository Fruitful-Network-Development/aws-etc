#!/bin/bash
# synch_srv.sh
#
# Sync the skeleton structure from GH-etc/srv/webapps/ to the live system
# /srv/webapps/ directory. This script safely updates source code while
# preserving runtime state (venv, .git, __pycache__).
#
# Source tree (default):
#   GH_ROOT=/home/admin/GH-etc/srv/webapps
# Dest tree (default):
#   SRV_ROOT=/srv/webapps
#
# Typical usage:
#   ./synch_srv.sh                    # Sync everything
#   ./synch_srv.sh --no-restart       # Sync without restarting services
#   ./synch_srv.sh platform           # Sync platform only
#   ./synch_srv.sh clients            # Sync clients only
#
set -euo pipefail

GH_ROOT="${GH_ROOT:-/home/admin/GH-etc}"
SRV_ROOT="${SRV_ROOT:-/srv/webapps}"
SRV_SRC="${GH_ROOT}/srv/webapps"

RESTART_SERVICES="${RESTART_SERVICES:-yes}"
SYNC_TARGET="${1:-all}"

log() {
  echo "[synch_srv] $*"
}

error() {
  echo "[synch_srv] ERROR: $*" >&2
  exit 1
}

# Verify source exists
if [ ! -d "$SRV_SRC" ]; then
  error "Source directory not found: $SRV_SRC"
fi

# Verify destination exists
if [ ! -d "$SRV_ROOT" ]; then
  log "Creating destination directory: $SRV_ROOT"
  sudo mkdir -p "$SRV_ROOT"
fi

# Rsync exclusions: preserve runtime state
RSYNC_EXCLUDES=(
  --exclude='.git'
  --exclude='venv'
  --exclude='__pycache__'
  --exclude='*.pyc'
  --exclude='*.pyo'
  --exclude='*.pyd'
  --exclude='.DS_Store'
  --exclude='*.log'
  --exclude='.env'
  --exclude='*.sqlite3'
  --exclude='instance'
  --exclude='uploads'
  --exclude='data'
)


# Sync platform directory
sync_platform() {
  if [ ! -d "$SRV_SRC/platform" ]; then
    log "Platform source not found, skipping..."
    return 0
  fi

  log "Syncing platform from $SRV_SRC/platform to $SRV_ROOT/platform"
  sudo rsync -av "${RSYNC_EXCLUDES[@]}" \
    "$SRV_SRC/platform/" "$SRV_ROOT/platform/"
  
  log "Platform sync complete"
}

# Sync clients directory
sync_clients() {
  if [ ! -d "$SRV_SRC/clients" ]; then
    log "Clients source not found, skipping..."
    return 0
  fi

  log "Syncing clients from $SRV_SRC/clients to $SRV_ROOT/clients"
  sudo rsync -av "${RSYNC_EXCLUDES[@]}" \
    "$SRV_SRC/clients/" "$SRV_ROOT/clients/"
  
  log "Clients sync complete"
}

# Restart services if needed
restart_services() {
  if [ "$RESTART_SERVICES" != "yes" ]; then
    log "Skipping service restart (RESTART_SERVICES=$RESTART_SERVICES)"
    return 0
  fi

  log "Restarting services..."

  # Restart platform service if it exists and is active
  if systemctl is-active --quiet platform.service 2>/dev/null; then
    log "Restarting platform.service..."
    sudo systemctl restart platform.service
    log "platform.service restarted"
  else
    log "platform.service not active, skipping restart"
  fi

  # Reload nginx if it's running
  if systemctl is-active --quiet nginx 2>/dev/null; then
    log "Reloading nginx..."
    sudo systemctl reload nginx
    log "nginx reloaded"
  else
    log "nginx not active, skipping reload"
  fi

  log "Service restart complete"
}

print_help() {
  cat <<EOF
Usage: $0 [TARGET] [OPTIONS]

Syncs skeleton structure from GH-etc/srv/webapps/ to /srv/webapps/

TARGET (optional):
  all       Sync everything (default)
  platform  Sync platform directory only
  clients   Sync clients directory only

OPTIONS:
  --no-restart  Skip service restart after sync

Environment variables:
  GH_ROOT         Source repo root (default: /home/admin/GH-etc)
  SRV_ROOT        Destination tree (default: /srv/webapps)
  RESTART_SERVICES  Restart services after sync (default: yes)

Examples:
  $0                          # Sync everything and restart services
  $0 --no-restart             # Sync without restarting
  $0 platform                 # Sync platform only
  $0 clients --no-restart     # Sync clients without restart

EOF
}

# Handle --help
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "help" ]; then
  print_help
  exit 0
fi

# Handle --no-restart flag
if [ "${1:-}" = "--no-restart" ]; then
  RESTART_SERVICES="no"
  SYNC_TARGET="${2:-all}"
elif [ "${2:-}" = "--no-restart" ]; then
  RESTART_SERVICES="no"
fi

# Main sync logic
log "Starting sync from $SRV_SRC to $SRV_ROOT"

case "$SYNC_TARGET" in
  all)
    sync_platform
    sync_clients
    ;;
  platform)
    sync_platform
    ;;
  clients)
    sync_clients
    ;;
  *)
    error "Unknown target: $SYNC_TARGET. Use 'all', 'platform', or 'clients'"
    ;;
esac

restart_services

log "Sync complete"
