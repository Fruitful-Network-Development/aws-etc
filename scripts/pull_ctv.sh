#!/bin/bash
# pull_ctv.sh
#
# Pull updates for the cuyahogaterravita.com client repository that lives under
# /srv/webapps/clients by default.

set -euo pipefail

REPO_PATH="${REPO_PATH:-/srv/webapps/clients/cuyahogaterravita.com}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[pull_ctv] Git repository not found at $REPO_PATH" >&2
  exit 1
fi

cd "$REPO_PATH"

echo "[pull_ctv] Fetching $REMOTE/$BRANCH in $REPO_PATH"
git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

echo "[pull_ctv] Updated $BRANCH in $REPO_PATH"
