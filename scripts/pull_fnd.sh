#!/bin/bash
# pull_fnd.sh
#
# Pull updates for the fruitfulnetworkdevelopment.com client repository.

set -euo pipefail

REPO_PATH="${REPO_PATH:-/srv/webapps/clients/fruitfulnetworkdevelopment.com}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
LOG_DIR="$HOME/GH-etc/docs/audit"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[pull_fnd] Git repository not found at $REPO_PATH" >&2
  exit 1
fi

cd "$REPO_PATH"

# Prevent pulling over local changes
if ! git diff --quiet; then
  echo "[pull_fnd] ERROR: Local changes detected — refusing to pull." >&2
  exit 1
fi

echo "[pull_fnd] Before pull: $(git rev-parse HEAD)"
git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"
echo "[pull_fnd] After pull:  $(git rev-parse HEAD)"

# Log the update
mkdir -p "$LOG_DIR"
echo "$(date) - Updated $REPO_PATH on branch $BRANCH" >> "$LOG_DIR/fnd_updates.log"

echo "[pull_fnd] Updated $BRANCH in $REPO_PATH"
