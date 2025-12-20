#!/bin/bash
# pull_etc.sh
#
# Pull updates from the `Fruitful-Network-Development/aws-box` GitHub repository on `main`.
# This script is intended to be the standard way to keep the local aws-box clone updated.
#
# It assumes that the local clone at REPO_PATH is already configured
# with a remote (typically `origin`) pointing at:
#   https://github.com/Fruitful-Network-Development/aws-box.git
# Per-host overrides can be done via environment variables.
#
set -euo pipefail

REPO_PATH="${REPO_PATH:-$(cd "$(dirname "$0")/.." && pwd)}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[pull_etc] Git repository not found at $REPO_PATH" >&2
  exit 1
fi

cd "$REPO_PATH"

echo "[pull_etc] Updating $REPO_PATH from $REMOTE/$BRANCH (aws-box)..."
git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

echo "[pull_etc] Updated $BRANCH in $REPO_PATH from $REMOTE (aws-box)"
