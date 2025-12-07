#!/bin/bash
# pull_fnd.sh
#
# Pull updates for the fruitfulnetworkdevelopment.com client repository.

set -euo pipefail

REPO_PATH="${REPO_PATH:-/srv/webapps/clients/fruitfulnetworkdevelopment.com}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[pull_fnd] Git repository not found at $REPO_PATH" >&2
  exit 1
fi

cd "$REPO_PATH"

echo "[pull_fnd] Fetching $REMOTE/$BRANCH in $REPO_PATH"
git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

echo "[pull_fnd] Updated $BRANCH in $REPO_PATH"
