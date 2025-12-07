#!/bin/bash
# pull_app.sh
#
# Safely pull updates for the Flask platform repository that lives in the
# deployed /srv tree. Defaults can be overridden with environment variables so
# the same script works across hosts.

set -euo pipefail

REPO_PATH="${REPO_PATH:-/srv/webapps/platform}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[pull_app] Git repository not found at $REPO_PATH" >&2
  exit 1
fi

cd "$REPO_PATH"

echo "[pull_app] Fetching $REMOTE/$BRANCH in $REPO_PATH"
git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

echo "[pull_app] Updated $BRANCH in $REPO_PATH"
