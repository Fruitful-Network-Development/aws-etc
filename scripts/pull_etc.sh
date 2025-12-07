#!/bin/bash
# pull_etc.sh
#
# Pull updates for the GH-etc sandbox repository that mirrors /etc content.

set -euo pipefail

REPO_PATH="${REPO_PATH:-$(cd "$(dirname "$0")/.." && pwd)}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[pull_etc] Git repository not found at $REPO_PATH" >&2
  exit 1
fi

cd "$REPO_PATH"

echo "[pull_etc] Fetching $REMOTE/$BRANCH in $REPO_PATH"
git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

echo "[pull_etc] Updated $BRANCH in $REPO_PATH"
