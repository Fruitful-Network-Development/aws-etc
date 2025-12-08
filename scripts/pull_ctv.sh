#!/bin/bash
# pull_ctv.sh
#
# Pull updates for the cuyahogaterravita.com client repository that lives under
# /srv/webapps/clients by default.

set -euo pipefail

REPO_PATH="${REPO_PATH:-/srv/webapps/clients/cuyahogaterravita.com}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
LOG_DIR="$HOME/GH-etc/docs/audit"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[pull_ctv] Git repository not found at $REPO_PATH" >&2
  exit 1
fi

cd "$REPO_PATH"

# Prevent pulling over local changes
if ! git diff --quiet; then
  echo "[pull_ctv] ERROR: Local changes detected — refusing to pull." >&2
  exit 1
fi

echo "[pull_ctv] Before pull: $(git rev-parse HEAD)"
git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"
echo "[pull_ctv] After pull:  $(git rev-parse HEAD)"

# Log the update
mkdir -p "$LOG_DIR"
echo "$(date) - Updated $REPO_PATH on branch $BRANCH" >> "$LOG_DIR/ctv_updates.log"

echo "[pull_ctv] Updated $BRANCH in $REPO_PATH"
