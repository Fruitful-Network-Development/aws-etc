#!/bin/bash
# synch.sh
#
# Sync individual configuration files from the GH-etc repo clone into the
# live system `/etc` directory, one file at a time.
#
# Source tree (default):
#   GH_ROOT=/home/admin/GH-etc
# Dest tree (default):
#   ETC_ROOT=/etc
#
# Typical usage:
#   ./synch.sh one etc/nginx/nginx.conf
#   ./synch.sh nginx-core
#   ./synch.sh nginx-site fruitfulnetworkdevelopment.com
#
# Note: This script uses sudo to write to /etc. It syncs configuration
# templates from GH-etc to the live system paths.
#
set -euo pipefail

GH_ROOT="${GH_ROOT:-/home/admin/GH-etc}"
ETC_ROOT="${ETC_ROOT:-/etc}"

log() {
  echo "[synch] $*"
}

# Map a repo-relative path (e.g. `etc/nginx/nginx.conf`) to a target path
# under $ETC_ROOT. If the path starts with `etc/`, we strip that so that
# `etc/nginx/nginx.conf` becomes `$ETC_ROOT/nginx/nginx.conf`.
resolve_dest() {
  local rel_path="$1"
  local dest_rel

  case "$rel_path" in
    etc/*)
      dest_rel="${rel_path#etc/}"
      ;;
    *)
      dest_rel="$rel_path"
      ;;
  esac

  printf '%s\n'"$ETC_ROOT/$dest_rel"
}

sync_one() {
  if [ "$#" -ne 1 ]; then
    echo "Usage: $0 one RELATIVE_PATH_UNDER_GH_ETC" >&2
    exit 1
  fi

  local rel_path="$1"
  local src="$GH_ROOT/$rel_path"
  local dest
  dest="$(resolve_dest "$rel_path")"

  if [ ! -f "$src" ]; then
    echo "[synch] Source file not found: $src" >&2
    exit 1
  fi

  log "Copying $src -> $dest"
  # Use sudo for /etc operations (standard user cannot write to /etc)
  sudo mkdir -p "$(dirname "$dest")"
  sudo cp -v "$src" "$dest"
}

sync_nginx_core() {
  sync_one "etc/nginx/nginx.conf"
  sync_one "etc/nginx/mime.types"
}

sync_nginx_site() {
  if [ "$#" -ne 1 ]; then
    echo "Usage: $0 nginx-site SITENAME_OR_REL_PATH" >&2
    echo "  Example with sitename: fruitfulnetworkdevelopment.com" >&2
    echo "  Example with rel path: etc/nginx/sites-available/fruitfulnetworkdevelopment.com.conf" >&2
    exit 1
  fi

  local arg="$1"
  local rel_path

  case "$arg" in
    */*)
      # Looks like a path already; use as-is relative to GH_ROOT.
      rel_path="$arg"
      ;;
    *.conf)
      rel_path="etc/nginx/sites-available/$arg"
      ;;
    *)
      rel_path="etc/nginx/sites-available/$arg.conf"
      ;;
  esac

  sync_one "$rel_path"
}

print_help() {
  cat <<EOF
Usage: $0 <command> [args]

Commands:
  one REL_PATH          Sync a single file by relative path under GH-etc
                        (e.g. etc/nginx/nginx.conf).

  nginx-core            Sync core nginx config files (nginx.conf, mime.types).

  nginx-site NAME       Sync one nginx site config. NAME can be either:
                          - a bare sitename (e.g. fruitfulnetworkdevelopment.com), or
                          - a .conf filename, or
                          - a full relative path under GH-etc
                            (e.g. etc/nginx/sites-available/foo.conf).

Environment variables:
  GH_ROOT   Source repo root (default: /home/admin/GH-etc)
  ETC_ROOT  Destination tree (default: /etc)
EOF
}

main() {
  if [ "$#" -lt 1 ]; then
    print_help
    exit 1
  fi

  local cmd="$1"; shift || true

  case "$cmd" in
    one)
      sync_one "$@"
      ;;
    nginx-core)
      sync_nginx_core "$@"
      ;;
    nginx-site)
      sync_nginx_site "$@"
      ;;
    help|--help|-h)
      print_help
      ;;
    *)
      echo "Unknown command: $cmd" >&2
      print_help
      exit 1
      ;;
  esac
}

main "$@"
