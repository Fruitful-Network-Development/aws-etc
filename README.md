# aws-ec2-dev

## Project Layout

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
      - ├── user_data.json
      - ├── assets/...
      - └── webpage/
        - ├── demo/...
    - ├── data/
      - └── backend_data.json
    - └── config/
      - └── settings.json
  - └── cuyahogaterravita.com/...
- └── [README](README.md)                   # <-- this file

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

The **Fruitful Network Development** site acts as a **central profile directory** that can display Mycite profiles from any client website. Each client site exposes a standardized `/user_data.json`, which the directory loads and renders inside the Mycite layout.

### How It Works
1. Every Mycite-capable domain must publish `https://<client>/user_data.json` using the shared schema.

2. Remote profiles are visualized by visiting:
   **`/profiles/<client_slug>`** (for example `/profiles/cuyahogaterravita.com`).
   The server redirects to **`/mysite?external=<client_slug>`**, and the front‑end fetches the canonical `https://<client_slug>/user_data.json` through `/proxy/<client_slug>/user_data.json`.

3. The proxy always performs a remote HTTPS fetch with structured JSON error responses (no local fallbacks or dev overrides).

4. User-specific routes such as `/<user_id>` resolve against the server-side directory of stored user_data.json files. Accessing `/directory` forces a refresh of those files so updates on disk become available immediately.

5. The Mycite framework renders the received JSON as a full profile page across both the hub domain and external client domains.

---

## Matenance Scipts

### ~/script/update_repo.sh
```bash
#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_DIR="$PROJECT_ROOT/repo"

cd "$REPO_DIR"
git pull

echo "Repo updated at: $REPO_DIR"
```

### ~/script/update_repo.sh
```bash
#!/bin/bash
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

---

## Nginx

### ~deploy/etc/nginx/nginx.conf
```conf
# /etc/nginx/nginx.conf

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

### ~deploy/etc/nginx/nginx.conf
```bash
# /etc/nginx/sites-available/fruitfulnetworkdevelopment.com.conf

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

---

## Mycite Profile Framework

The Mycite Profile Framework provides a unified data schema (user_data.json) and a standardized rendering layer defined at the repository root (index.html, style.css, app.js), which together establish a neutral, interoperable profile format.

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
    - All information is stored structurally in user_data.json, independent of HTML layout.
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
