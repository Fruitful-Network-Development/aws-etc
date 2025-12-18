#!/bin/bash
# pull_app.sh
#
# Safely pull updates for the Flask application repository that backs the
# deployed platform. By default this script assumes the deployed clone lives at
# `/home/admin/srv/webapps` and that its primary remote (`origin`) points to:
#   https://github.com/Fruitful-Network-Development/flask-app.git
#
# These assumptions can be overridden via environment variables so the same
# script works across hosts.
#
set -euo pipefail

REPO_PATH="${REPO_PATH:-/home/admin/srv/webapps}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[pull_app] Git repository not found at $REPO_PATH" >&2
  exit 1
fi

cd "$REPO_PATH"

echo "[pull_app] Updating $REPO_PATH from $REMOTE/$BRANCH (flask-app)..."
git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

echo "[pull_app] Updated $BRANCH in $REPO_PATH from $REMOTE (flask-app)"
