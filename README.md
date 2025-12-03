# aws-ec2-dev

## Project Layout

```
- ├── /ect 
  - └── nginx/
    - ├── nginx.conf
    - ├── sites-available/
      - └── fruitfulnetwork.com.conf
    - └── sites-enabled/
      - └── fruitfulnetwork.com.conf
- ├── /srv/webapps
  - ├── platform/
    - ├── app.py
    - └── modules/
      - └── __init__.py
  - └── clients/
  - └── fruitfulnetwork.com/
    - ├── frontend/
      - ├── mycite.html
      - ├── style.css
      - ├── app.js
      - ├── script.js
      - ├── msn_<user_id>.json
      - ├── assets/...
      - └── webpage/
        - ├── demo/...
    - ├── data/
      - └── backend_data.json
    - └── config/
      - └── settings.json
  - └── cuyahogaterravita.com/...
- └── [README](README.md)                   # <-- this file
```

### Server Layout
project-root/
- ├── repo/
- │   └── srv/webapps/…      # Flask app and front‑end code
- ├── deploy/
- │   ├── etc/nginx/…        # a local copy of the server’s /etc/nginx configuration
- │   └── srv/webapps/…      # a local copy of /srv/webapps from the server
- ├── scripts/
- │   ├── pull_srv.sh
- │   ├── deploy_repo.sh
- │   └── deploy_etc.sh
- └── README.md

---

## Mycite Profile Directory — Intended Operation

The **Fruitful Network Development** site acts as a **central profile directory** that can display Mycite profiles from any client website. Each client site exposes a standardized `msn_<user_id>.json`, which the directory loads and renders inside the Mycite layout.

### How It Works
1. Every Mycite-capable domain must publish `https://<client>/msn_<user_id>.json` using the shared schema.

2. Remote profiles are visualized by visiting:
   **`/profiles/<client_slug>`** (for example `/profiles/cuyahogaterravita.com`).
   The server redirects to **`/mysite?external=<client_slug>`**, and the front‑end fetches the canonical `https://<client_slug>/msn_<user_id>.json` through `/proxy/<client_slug>/msn_<user_id>.json`.

3. The proxy always performs a remote HTTPS fetch with structured JSON error responses (no local fallbacks or dev overrides).

4. User-specific routes such as `/<user_id>` resolve against the server-side directory of stored `msn_<user_id>.json` files. Accessing `/directory` forces a refresh of those files so updates on disk become available immediately.

5. The Mycite framework renders the received JSON as a full profile page across both the hub domain and external client domains.

---

## Matenance Scipts

### update_repo.sh
```bash
# scripts/update_repo.sh
# !/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_DIR="$PROJECT_ROOT/repo"

cd "$REPO_DIR"
git pull

echo "Repo updated at: $REPO_DIR"
```

### deploy_repo.sh
```bash
# scripts/deploy_repo.sh
# !/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

SRC="$PROJECT_ROOT/repo/srv/webapps/"
DST="/srv/webapps/"

# Make sure source exists
if [ ! -d "$SRC" ]; then
  echo "Source path does not exist: $SRC"
  exit 1
fi

echo "Syncing $SRC -> $DST ..."
sudo rsync -az --delete "$SRC" "$DST"

echo "Deployed: $SRC  -->  $DST"
```

### deploy.sh
```bash
# scripts/deploy.sh
#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

./update_repo.sh
./deploy_repo.sh

echo "Full deploy complete."
```

### deploy.sh
```bash
#!/bin/bash
# maintenance.sh
# A helper script for common nginx + diagnostics tasks on cuyahogaterravita.com
#
# Usage examples:
#   ./maintenance.sh nginx-test
#   ./maintenance.sh nginx-reload
#   ./maintenance.sh curl-site
#   ./maintenance.sh curl-image
#
# Run "./maintenance.sh help" to list all commands.

set -euo pipefail

# --- Colors for nicer output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # no color

DOMAIN="cuyahogaterravita.com"

# --- Generic helpers ---

header() {
    echo -e "\n${CYAN}==> $1${NC}"
}

usage() {
    echo -e "${YELLOW}Maintenance Script - Available Commands:${NC}"
    echo "  nginx-test        - Test nginx config (syntax) BEFORE reloading or restarting."
    echo "  nginx-reload      - Reload nginx AFTER you change config (safer than restart)."
    echo "  nginx-restart     - Full restart if nginx got wedged or crashed."
    echo "  nginx-status      - Check whether nginx is running and see its health."
    echo "  nginx-errors      - Tail the main nginx error log for recent issues."
    echo ""
    echo "  curl-site         - Test HTTPS for / (does the site load at all?)."
    echo "  curl-http         - Test HTTP and ensure redirect to HTTPS is working."
    echo "  curl-image        - Test a known asset (verifies static file serving)."
    echo "  curl-api          - Test the weather API endpoint (backend/Flask wiring)."
    echo ""
    echo "  dns-check         - Check that DNS for the domain points to this server."
    echo "  vhosts            - List active nginx vhosts (sites-enabled symlinks)."
    echo ""
    echo "  help              - Show this help message."
}

# -------------------------
# NGINX MANAGEMENT COMMANDS
# -------------------------

nginx_test() {
    # WHEN TO USE:
    #   Any time you change /etc/nginx/nginx.conf or a vhost in /etc/nginx/sites-available.
    #
    # WHAT IT TELLS YOU:
    #   Checks nginx syntax and basic config validity without applying changes.
    #   If this fails, DO NOT reload/restart nginx.
    header "Testing nginx configuration (syntax + basic validity)"
    sudo nginx -t
}

nginx_reload() {
    # WHEN TO USE:
    #   After nginx-test passes and you want to apply config changes without
    #   dropping existing connections.
    #
    # WHAT IT TELLS YOU:
    #   If this succeeds, your new config is live. If it fails, nginx stays
    #   on the old config and systemctl will print the error.
    header "Reloading nginx (apply config changes safely)"
    sudo systemctl reload nginx
}

nginx_restart() {
    # WHEN TO USE:
    #   Only when nginx is in a bad state (e.g. crashed, stuck, or reload
    #   isn't fixing behavior). Rare compared to reload.
    #
    # WHAT IT TELLS YOU:
    #   Confirms nginx can stop and start cleanly with the current config.
    header "Restarting nginx (hard reset of the service)"
    sudo systemctl restart nginx
}

nginx_status() {
    # WHEN TO USE:
    #   If you suspect nginx is down or misbehaving, or after a restart/reload.
    #
    # WHAT IT TELLS YOU:
    #   Shows whether nginx is active, when it was started, and recent log lines
    #   from systemd.
    header "Nginx systemctl status (is it running / any recent errors?)"
    sudo systemctl status nginx
}

nginx_errors() {
    # WHEN TO USE:
    #   When you’re seeing 4xx/5xx responses, or nginx-test passes but the site behaves oddly.
    #
    # WHAT IT TELLS YOU:
    #   Shows the last ~40 lines of /var/log/nginx/error.log, which usually
    #   captures config issues, upstream (Flask) problems, permission errors, etc.
    header "Tailing nginx error log (last 40 lines)"
    sudo tail -n 40 /var/log/nginx/error.log
}

# -------------------------
# CURL / HTTP DIAGNOSTICS
# -------------------------

curl_site() {
    # WHEN TO USE:
    #   First-line check when "the site seems down" or after you change
    #   nginx or deploy static files.
    #
    # WHAT IT TELLS YOU:
    #   Whether HTTPS returns a 200/301/302/etc for the root URL and which
    #   headers are being sent (e.g., server, content-type).
    header "curl -I https://${DOMAIN}/  (basic HTTPS site check)"
    curl -I "https://${DOMAIN}/"
}

curl_http() {
    # WHEN TO USE:
    #   After setting up HTTPS + redirects, or if browsers hit HTTP and you
    #   want to confirm they are being redirected.
    #
    # WHAT IT TELLS YOU:
    #   Shows HTTP status for plain http:// and whether there's a 301/302
    #   redirect to https://.
    header "curl -I http://${DOMAIN}/  (check HTTP→HTTPS redirect)"
    curl -I "http://${DOMAIN}/"
}

curl_image() {
    # WHEN TO USE:
    #   When images or static assets don't show up in the browser.
    #
    # WHAT IT TELLS YOU:
    #   Confirms whether nginx can serve a known static file with a 200.
    #   If this 404s but index.html works, it's almost always a root/path issue.
    IMAGE_PATH="/assets/web-splash-page-img.png"
    header "Testing known asset: https://${DOMAIN}${IMAGE_PATH}"
    curl -I "https://${DOMAIN}${IMAGE_PATH}"
}

curl_api() {
    # WHEN TO USE:
    #   After wiring up the weather Flask module or any /api/ route.
    #
    # WHAT IT TELLS YOU:
    #   Whether the API endpoint responds, and what JSON it returns.
    #   Good for checking upstream Flask errors without involving the front-end.
    API="/api/weather/daily?lat=41.1&lon=-81.5&days=3&past_days=1"
    header "Testing weather API: https://${DOMAIN}${API}"
    if command -v jq >/dev/null 2>&1; then
        curl -s "https://${DOMAIN}${API}" | jq .
    else
        echo "(jq not installed; showing raw JSON)"
        curl -s "https://${DOMAIN}${API}"
    fi
}

# -------------------------
# DNS / VHOST HELPERS
# -------------------------

dns_check() {
    # WHEN TO USE:
    #   When curl says "Could not resolve host" or you're not sure your DNS
    #   is pointing at the correct server.
    #
    # WHAT IT TELLS YOU:
    #   Shows the IP addresses that cuyahogaterravita.com and www.* resolve to.
    header "DNS Check (dig +short ${DOMAIN} and www.${DOMAIN})"
    dig +short "${DOMAIN}"
    dig +short "www.${DOMAIN}"
}

vhosts() {
    # WHEN TO USE:
    #   When you're unsure which sites are enabled in nginx, or whether the
    #   config file you edited is actually symlinked in sites-enabled/.
    #
    # WHAT IT TELLS YOU:
    #   Lists the vhost files that nginx is including (sites-enabled symlinks).
    header "Active nginx vhosts (sites-enabled)"
    ls -l /etc/nginx/sites-enabled/
}

# -------------------------
# DISPATCH
# -------------------------

case "${1:-help}" in
    nginx-test)    nginx_test ;;
    nginx-reload)  nginx_reload ;;
    nginx-restart) nginx_restart ;;
    nginx-status)  nginx_status ;;
    nginx-errors)  nginx_errors ;;
    curl-site)     curl_site ;;
    curl-http)     curl_http ;;
    curl-image)    curl_image ;;
    curl-api)      curl_api ;;
    dns-check)     dns_check ;;
    vhosts)        vhosts ;;
    help|*)        usage ;;
esac
```

---

## Nginx

### nginx.conf
```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    # Log formats, gzip, etc. could go here

    include /etc/nginx/sites-enabled/*;
}

```

### fruitfulnetworkdevelopment.com.conf
```nginx
# Redirect HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name fruitfulnetworkdevelopment.com www.fruitfulnetworkdevelopment.com;

    # Leave this for certbot HTTP challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name fruitfulnetworkdevelopment.com www.fruitfulnetworkdevelopment.com;

    # --- SSL config (paths from certbot) ---
    ssl_certificate     /etc/letsencrypt/live/fruitfulnetworkdevelopment.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fruitfulnetworkdevelopment.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    access_log /var/log/nginx/fruitfulnetwork.access.log;
    error_log  /var/log/nginx/fruitfulnetwork.error.log;

    # If you *ever* want to serve static directly, this root is handy,
    # but in this design, most traffic just goes to Flask.
    root /srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend;
    index index.html;

    # (Optional) Serve really heavy static assets directly from NGINX
    # location /assets/ {
    #     alias /srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/assets/;
    # }

    # Everything else → shared Flask backend
    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_redirect off;
    }
}
```

### fruitfulnetworkdevelopment.com.conf
```nginx
# /etc/nginx/sites-enabled/fruitfulnetworkdevelopment.com.conf
../sites-available/fruitfulnetworkdevelopment.com.conf
```

### cuyahogaterravita.com.conf
```nginx
# /etc/nginx/sites-available/cuyahogaterravita.com.conf

# ------------------------------------------------
# HTTP → HTTPS
# ------------------------------------------------
server {
    listen 80;
    listen [::]:80;
    server_name cuyahogaterravita.com www.cuyahogaterravita.com;

    # Let’s Encrypt HTTP-01 challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect everything else to HTTPS
    return 301 https://$host$request_uri;
}

# ------------------------------------------------
# HTTPS: serve static frontend, proxy /api to Flask
# ------------------------------------------------
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name cuyahogaterravita.com www.cuyahogaterravita.com;

    ssl_certificate     /etc/letsencrypt/live/cuyahogaterravita.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cuyahogaterravita.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    access_log /var/log/nginx/cuyahogaterravita.access.log;
    error_log  /var/log/nginx/cuyahogaterravita.error.log;

    # ---- STATIC ROOT ----
    # Serve the built frontend directly from its project root so
    # /index.html and other assets resolve correctly.
    root /srv/webapps/clients/cuyahogaterravita.com/frontend;
    index index.html;

    # ---- ASSETS ALIAS (Option A) ----
    # Map URLs /frontend/assets/... to the real assets directory
    # /srv/webapps/clients/cuyahogaterravita.com/frontend/assets/...
    location /frontend/assets/ {
        alias /srv/webapps/clients/cuyahogaterravita.com/frontend/assets/;
    }

    # ---- API PROXY ----
    # Only /api/... is proxied to your shared Flask backend.
    # (adjust the port if your Flask app is on a different one)
    location /api/ {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_redirect off;
    }

    # ---- DEFAULT STATIC HANDLER ----
    # Everything else is served from the static root (webpages)
    # Use SPA fallback so front-end routes resolve correctly.
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### cuyahogaterravita.com.conf
```nginx
# /etc/nginx/sites-enabled/cuyahogaterravita.com.conf
../sites-available/cuyahogaterravita.com.conf
```

---

## Mycite Profile Framework

The Mycite Profile Framework provides a unified data schema (`msn_<user_id>.json`) and a standardized rendering layer defined at the repository root (index.html, style.css, app.js), which together establish a neutral, interoperable profile format.

This format is deliberately designed so that:
1. Any website can embed or access a standardized version of a user’s profile.
2. Creative, free-form websites (stored in /webpage/) can reinterpret the same data without layout constraints.
3. The root-level index.html acts as the default profile view and canonical structural definition, but not the definitive layout for alternative pages.
4. Third-party aggregators (markets, co-ops, directories, etc.) can load the same JSON file and render a consistent view.
This project provides both:
- A standardized profile interface (Mycite View)
- A free-form creative layer that consumes the same schema
The result is an extensible personal or organizational site with built-in interoperability and layout independence.

### Conceptual Purpose

The Mycite framework addresses a common problem:
    Websites often contain rich personal or organizational content, but there is no universal, neutral way to exchange or display profiles across platforms.
The Mycite approach solves this by:
- Defining a data-first profile schema (Compendium, Oeuvre, Anthology)
- Building a standardized UI that can be used anywhere
- Allowing creative reinterpretation through a separate free-form site

This allows:
1. A single canonical profile source
    - All information is stored structurally in `msn_<user_id>.json`, independent of HTML layout.
2. Multiple render layers
    - Mycite Standard View → neutral, predictable, portable
    - Free-form Webpage View → expressive, themeable, personal
3. Interoperability
    - Any third-party environment can pull the JSON and display a stable profile.
4. Future-proof extension
    - New sections (videos, certifications, links, project groups) can be added to the JSON without breaking existing pages.
This achieves a philosophical and technical goal:
separation of content and representation, enabling multi-context identity display.

### Objectives and Design Principles

- Separation of Content and Layout
    - All content is stored structurally in JSON.
    - The Mycite view and free-form site are merely renderers.
- Interoperability and Portability
    - Any host that understands the schema can generate a valid profile.
    - This creates a “portable identity page” across contexts.
- Extendability
    - Add new sections to the JSON without breaking the Mycite viewer.
- Neutral Standardization
    The Mycite layout is intentionally simple and standardized:
    - predictable typography
    - consistent left/right column structure
    - accessible and portable design
- Creative Freedom
    - The free-form website allows unrestricted design while still pulling accurate profile information.

---

## License

---

## Acknowledgments

Built and authored by Dylan Montgomery

MODIFIED:	####-##-##
VERSION:	##.##.##
STATUS:     Active prototyping and architectural refinement
