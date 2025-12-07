#!/usr/bin/env bash

# Notes from GPT Agent Session
# The script assumes Ubuntu 20.04 or later and uses apt-get for package management. You can adjust package versions if needed.
# The user, worker_processes and logging directives in the supplied Nginx configuration mirror typical production settings. The site files from aws-etc/etc/nginx/sites-available proxy /api/ to the Gunicorn server on port 8000 and serve the static front‑end from /srv/webapps/clients/<domain>/frontend.
# Certbot is configured to automatically modify the Nginx config and will create renewal timers; you can test renewal with certbot renew --dry-run.
# If you add new modules or blueprints to the Flask application, update requirements.txt or install additional packages within the virtual environment.
# Create varibles to run:
# export FND_SECRET_KEY="paste-your-secret-here"
# export FND_CONTACT_EMAIL="your-email@example.com"

# Then run:
# sudo -E bash deploy_platform.sh


#---------------------------------------------------------------------
#  Fruitful Network Development – clean server deployment script
#
#  This script bootstraps a brand‑new Ubuntu server for the FND
#  platform after a reset.  It installs system packages, clones the
#  required repositories, sets up a Python virtual environment,
#  configures Gunicorn, installs and configures Nginx, and obtains
#  SSL certificates with Certbot.  It also copies configuration files
#  from the dedicated GH‑etc repository into the live system.
#
#  IMPORTANT:
#    • Do not modify files directly under /etc or /srv/webapps.  The
#      GH‑etc repository should be treated as a sandbox for system
#      configuration.  Commit any changes there and use scripts to
#      pull updates.
#    • Running this script multiple times is idempotent.
#    • Before running Certbot, ensure that your domain names point to
#      this server’s public IP and that port 80 is open in the security group.
#
#  Usage:
#    sudo bash deploy_platform.sh
#
#  Required environment variables:
#    FND_CONTACT_EMAIL – email used for LetsEncrypt registration (optional)
#    FND_SECRET_KEY   – Flask secret key for session security (required)
#---------------------------------------------------------------------

set -euo pipefail

# Directories
APP_DIR="/srv/webapps/platform"
CLIENTS_DIR="/srv/webapps/clients"
GH_ETC_DIR="/home/admin/GH-etc"

# Repositories
REPO_USER="Fruitful-Network-Development"
PLATFORM_REPO="flask-app"
FND_FRONTEND_REPO="web-dir-fnd"
CTV_FRONTEND_REPO="web-dir-ctv"
ETC_REPO="aws-etc"

# Domains
DOMAIN_FND="fruitfulnetworkdevelopment.com"
DOMAIN_FND_WWW="www.${DOMAIN_FND}"
DOMAIN_CTV="cuyahogaterravita.com"
DOMAIN_CTV_WWW="www.${DOMAIN_CTV}"

# Contact email for Certbot; falls back to placeholder
CERTBOT_EMAIL="${FND_CONTACT_EMAIL:-admin@${DOMAIN_FND}}"

# Check required env var
if [[ -z "${FND_SECRET_KEY:-}" ]]; then
  echo "Error: FND_SECRET_KEY must be set before running this script."
  exit 1
fi

echo "[1/9] Updating system and installing packages..."
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y \
  python3 python3-venv python3-pip python3-dev \
  git nginx \
  certbot python3-certbot-nginx \
  ufw

echo "Configuring UFW..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo "[2/9] Creating directories..."
sudo mkdir -p "$APP_DIR" \
                 "$CLIENTS_DIR/${DOMAIN_FND}/frontend" \
                 "$CLIENTS_DIR/${DOMAIN_CTV}/frontend"
sudo mkdir -p /var/log/gunicorn /var/run/gunicorn
sudo chown -R www-data:www-data /var/log/gunicorn /var/run/gunicorn
sudo mkdir -p "$GH_ETC_DIR"
sudo chown -R "$(whoami)": "$(whoami)" "$GH_ETC_DIR"

echo "[3/9] Cloning/updating repositories..."
clone_or_update() {
  local repo_name="$1"
  local dest_dir="$2"
  local branch="${3:-main}"
  if [[ -d "$dest_dir/.git" ]]; then
    echo "  Updating $repo_name..."
    (cd "$dest_dir" && git fetch --all && git reset --hard "origin/$branch")
  else
    echo "  Cloning $repo_name..."
    git clone --branch "$branch" "https://github.com/${REPO_USER}/${repo_name}.git" "$dest_dir"
  fi
}
clone_or_update "$PLATFORM_REPO" "$APP_DIR"
clone_or_update "$FND_FRONTEND_REPO" "$CLIENTS_DIR/${DOMAIN_FND}/frontend"
clone_or_update "$CTV_FRONTEND_REPO" "$CLIENTS_DIR/${DOMAIN_CTV}/frontend"
clone_or_update "$ETC_REPO" "$GH_ETC_DIR"

echo "[4/9] Deploying Nginx/systemd configuration from GH‑etc..."
sudo cp -f "$GH_ETC_DIR/etc/nginx/nginx.conf" /etc/nginx/nginx.conf
sudo cp -rf "$GH_ETC_DIR/etc/nginx/snippets" /etc/nginx/  || true
sudo cp -rf "$GH_ETC_DIR/etc/nginx/conf.d" /etc/nginx/    || true
sudo cp -rf "$GH_ETC_DIR/etc/nginx/sites-available"/* /etc/nginx/sites-available/

for site in "$DOMAIN_FND" "$DOMAIN_CTV"; do
  conf="/etc/nginx/sites-available/${site}.conf"
  link="/etc/nginx/sites-enabled/${site}.conf"
  if [[ -f "$conf" && ! -L "$link" ]]; then
    sudo ln -s "$conf" "$link"
  fi
done

if [[ -d "$GH_ETC_DIR/etc/systemd/system" ]]; then
  sudo cp -rf "$GH_ETC_DIR/etc/systemd/system/"* /etc/systemd/system/
fi

echo "[5/9] Setting up Python virtual environment..."
if [[ ! -d "$APP_DIR/venv" ]]; then
  python3 -m venv "$APP_DIR/venv"
fi
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip
if [[ -f "$APP_DIR/requirements.txt" ]]; then
  pip install -r "$APP_DIR/requirements.txt"
else
  # core dependencies if no requirements file present
  pip install flask flask-cors requests gunicorn
fi
deactivate

echo "[6/9] Creating Gunicorn systemd service..."
sudo tee /etc/systemd/system/platform.service > /dev/null <<EOF
[Unit]
Description=Gunicorn instance to serve Fruitful Platform
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
Environment="FLASK_SECRET_KEY=${FND_SECRET_KEY}"
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable platform.service
sudo systemctl restart platform.service

echo "[7/9] Testing and reloading Nginx..."
sudo nginx -t
sudo systemctl reload nginx

echo "[8/9] Obtaining SSL certificates via Certbot..."
sudo certbot --non-interactive --agree-tos \
  --nginx -m "$CERTBOT_EMAIL" \
  -d "$DOMAIN_FND" -d "$DOMAIN_FND_WWW" \
  -d "$DOMAIN_CTV" -d "$DOMAIN_CTV_WWW" || true

echo "[9/9] Deployment complete."
echo "  Flask app:        $APP_DIR"
echo "  Virtual env:      $APP_DIR/venv"
echo "  Client sites:     $CLIENTS_DIR/$DOMAIN_FND/frontend and $CLIENTS_DIR/$DOMAIN_CTV/frontend"
echo "  Gunicorn service: platform.service (binding to 127.0.0.1:8000)"
echo "  SSL domains:      $DOMAIN_FND, $DOMAIN_FND_WWW, $DOMAIN_CTV, $DOMAIN_CTV_WWW"
echo "Verify DNS records point at this server’s IP before running Certbot and test that HTTPS works."
