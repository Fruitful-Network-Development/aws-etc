# This one copies nginx configs from your repo clone into the aws model tree. It never touches /etc.
#!/bin/bash
#
# Sync nginx config from GH-etc (repo) into the aws model directory.
# GH-etc:  ~/GH-etc/etc/nginx
# aws:     ~/aws/etc/nginx
#
set -euo pipefail

GH_NGINX="$HOME/GH-etc/etc/nginx"
AWS_NGINX="$HOME/aws/etc/nginx"

echo "[1/3] Ensuring aws nginx directory exists..."
mkdir -p "$AWS_NGINX/sites-available" "$AWS_NGINX/sites-enabled"

echo "[2/3] Copying base nginx config files..."
cp -v "$GH_NGINX/nginx.conf" "$AWS_NGINX/nginx.conf"
cp -v "$GH_NGINX/mime.types" "$AWS_NGINX/mime.types"

echo "[3/3] Copying site configs..."
cp -v "$GH_NGINX/sites-available/"*.conf "$AWS_NGINX/sites-available/"

echo "Sync complete: GH-etc → aws (nginx)."

# Make it executable:
    # chmod +x ~/GH-etc/scripts/01_sync_nginx_gh_to_aws.sh

# Usage (any time you change nginx configs in GH-etc):
    # bash ~/GH-etc/scripts/01_sync_nginx_gh_to_aws.sh
