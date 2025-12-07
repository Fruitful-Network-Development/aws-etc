#!/bin/bash
# deploy_etc.sh
#
# Helper functions to sync the GH-etc sandbox repository into the deployed
# /etc tree and to publish audit outputs in docs back to the remote branch.
#
# Usage examples:
#   ./deploy_etc.sh deploy_nginx           # sync etc/nginx -> /etc/nginx
#   ./deploy_etc.sh deploy_systemd         # sync etc/systemd -> /etc/systemd
#   ./deploy_etc.sh deploy_file nginx/nginx.conf
#   ./deploy_etc.sh push_docs "chore: sync audit outputs"
#
# Environment overrides:
#   REPO_ROOT   : path to the GH-etc sandbox clone (default: repo root)
#   DEPLOY_ROOT : path to the live /etc tree (default: /etc)
#   DOCS_DIR    : docs directory to push (default: $REPO_ROOT/docs)
#   REMOTE      : git remote to push to (default: origin)
#   BRANCH      : git branch to push to (default: main)
#   DRY_RUN     : set to any value to print actions without applying changes

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DEPLOY_ROOT="${DEPLOY_ROOT:-/etc}"
DOCS_DIR="${DOCS_DIR:-$REPO_ROOT/docs}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
SUDO_BIN="${SUDO_BIN:-$(command -v sudo || true)}"

run_with_sudo() {
    if [ -n "$SUDO_BIN" ]; then
        "$SUDO_BIN" "$@"
    else
        "$@"
    fi
}

sync_dir() {
    local source_dir="$1" destination_dir="$2"
    local rsync_flags=("-av" "--delete")

    if [ -n "${DRY_RUN:-}" ]; then
        rsync_flags+=("--dry-run")
        echo "[deploy_etc] DRY_RUN enabled"
    fi

    if [ ! -d "$source_dir" ]; then
        echo "[deploy_etc] Source directory not found: $source_dir" >&2
        exit 1
    fi

    echo "[deploy_etc] Syncing $source_dir -> $destination_dir"
    run_with_sudo rsync "${rsync_flags[@]}" "$source_dir" "$destination_dir"
}

usage() {
    cat <<USAGE
Usage: $0 <command> [args]

Commands:
  deploy_nginx           Sync etc/nginx to $DEPLOY_ROOT/nginx
  deploy_systemd         Sync etc/systemd to $DEPLOY_ROOT/systemd
  deploy_file <path>     Sync a single file relative to etc/ (e.g., nginx/nginx.conf)
  push_docs [message]    Add, commit, and push docs/ changes to $REMOTE $BRANCH
USAGE
}

deploy_nginx() {
    sync_dir "$REPO_ROOT/etc/nginx/" "$DEPLOY_ROOT/nginx/"
}

deploy_systemd() {
    sync_dir "$REPO_ROOT/etc/systemd/" "$DEPLOY_ROOT/systemd/"
}

deploy_file() {
    local relative_path="$1"
    local source_file="$REPO_ROOT/etc/$relative_path"
    local destination_file="$DEPLOY_ROOT/$relative_path"

    if [ ! -f "$source_file" ]; then
        echo "[deploy_etc] File not found: $source_file" >&2
        exit 1
    fi

    echo "[deploy_etc] Copying $source_file -> $destination_file"
    if [ -n "${DRY_RUN:-}" ]; then
        echo "[deploy_etc] DRY_RUN: install -Dm644 \"$source_file\" \"$destination_file\""
    else
        run_with_sudo install -Dm644 "$source_file" "$destination_file"
    fi
}

push_docs() {
    local message="${1:-chore: sync docs audit outputs}"

    if [ ! -d "$DOCS_DIR" ]; then
        echo "[deploy_etc] Docs directory not found: $DOCS_DIR" >&2
        exit 1
    fi

    cd "$REPO_ROOT"
    git add "$DOCS_DIR"

    if git diff --cached --quiet; then
        echo "[deploy_etc] No docs changes to push"
        return 0
    fi

    git commit -m "$message"
    git push "$REMOTE" "$BRANCH"
}

main() {
    local command="${1:-}"
    shift || true

    case "$command" in
        deploy_nginx)
            deploy_nginx "$@"
            ;;
        deploy_systemd)
            deploy_systemd "$@"
            ;;
        deploy_file)
            if [ "$#" -lt 1 ]; then
                echo "[deploy_etc] deploy_file requires a path relative to etc/" >&2
                exit 1
            fi
            deploy_file "$@"
            ;;
        push_docs)
            push_docs "$@"
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"
