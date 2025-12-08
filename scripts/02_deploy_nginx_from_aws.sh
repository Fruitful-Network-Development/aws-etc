# This one is the only script that touches /etc/nginx. 
# It copies from your staging area (~/aws/etc/nginx) to the real system, tests, and reloads.
#!/bin/bash
#
# Deploy nginx configuration from the aws model directory into /etc/nginx.
# aws:   ~/aws/etc/nginx
# live:  /etc/nginx
#
set -euo pipefail

AWS_NGINX="$HOME/aws/etc/nginx"
LIVE_NGINX="/etc/nginx"

echo "[1/5] Ensuring live nginx dirs exist..."
sudo mkdir -p "$LIVE_NGINX/sites-available" "$LIVE_NGINX/sites-enabled"

echo "[2/5] Copying core nginx configs (nginx.conf, mime.types)..."
sudo cp -v "$AWS_NGINX/nginx.conf" "$LIVE_NGINX/nginx.conf"
sudo cp -v "$AWS_NGINX/mime.types" "$LIVE_NGINX/mime.Types" 2>/dev/null || \
sudo cp -v "$AWS_NGINX/mime.types" "$LIVE_NGINX/mime.types"

echo "[3/5] Copying site configs into sites-available..."
sudo cp -v "$AWS_NGINX/sites-available/"*.conf "$LIVE_NGINX/sites-available/"

echo "[4/5] Ensuring site symlinks in sites-enabled..."
# Enable your two main sites (idempotent)
sudo ln -sf "$LIVE_NGINX/sites-available/fruitfulnetworkdevelopment.com.conf" \
             "$LIVE_NGINX/sites-enabled/fruitfulnetworkdevelopment.com.conf"

sudo ln -sf "$LIVE_NGINX/sites-available/cuyahogaterravita.com.conf" \
             "$LIVE_NGINX/sites-enabled/cuyahogaterravita.com.conf"

echo "[5/5] Testing nginx configuration..."
if sudo nginx -t; then
  echo "nginx -t OK, reloading..."
  sudo systemctl reload nginx
  echo "Deployment complete: aws → /etc/nginx."
else
  echo "nginx -t FAILED. Not reloading. Check errors above." >&2
  exit 1
fi

# Make it executable:
    # chmod +x ~/GH-etc/scripts/02_deploy_nginx_from_aws.sh

# Usage:
    # bash ~/GH-etc/scripts/02_deploy_nginx_from_aws.sh
# That’s your “push to live” for nginx config.
# If nginx -t ever fails, it won’t reload, so you won’t break the running server.
