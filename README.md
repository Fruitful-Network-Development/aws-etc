# awsDev

## OVERVIEW

### Server environment
- AWS EC2 instance running Debian.
- Nginx handles:
  - Virtual hosting for multiple domains.
  - Static file serving for each client frontend.
  - Reverse proxying of API calls to a shared Flask backend.
- Flask (running under Gunicorn or similar) lives in a central “platform” directory and serves JSON + API endpoints for all clients.

### Nginx role
- Each `*.conf` in `sites-available/`:
  - Sets `roo`t to `/srv/webapps/clients/<domain>/frontend`.
  - Serves `index.html`, CSS, and assets directly.
  - Proxies `/api/` (and possibly `/static/`) to the shared Flask app in `/srv/webapps/platform`.

### Flask role (platform/app.py)
- Single shared backend, not per-client.
- On startup, scans `/srv/webapps/clients/` for each `<domain>/frontend/msn_*.json`.
- Builds an in-memory lookup table mapping:
  - `domain → user_id → msn_<userId>.json path`.
- Exposes endpoints like:
  - `/api/site/<user_id>.json` → returns that client’s canonical JSON file.
  - Optional: `/api/sites` → returns a directory listing of all known sites.

### Project Layout

```text
- ├── /ect 
  - └── nginx/
    - ├── nginx.conf
    - ├── mime.types
    - ├── sites-available/
      - ├── cuyahogaterravita.com.conf
      - └── fruitfulnetworkdevelopment.com.conf
    - └── sites-enabled/
      - ├── cuyahogaterravita.com.conf -> ../sites-available/cuyahogaterravita.com.conf
      - └── fruitfulnetworkdevelopment.com.conf -> ../sites-available/fruitfulnetworkdevelopment.com.conf
- ├── /srv/webapps
  - ├── platform/
    - ├── app.py
    - └── modules/
      - └── __init__.py
  - └── clients/
  - └── fruitfulnetworkdevelopment.com/
    - ├── frontend/
      - ├── index.html
      - ├── style.css
      - ├── app.js
      - ├── script.js
      - ├── msn_<user_id>.json
      - └── assets/...
    - ├── data/...
    - └── config/
      - └── settings.json
  - └── cuyahogaterravita.com/...
- └── [README](README.md)                   # <-- this file
```

---

## TWO LAYERS OF STANDARDIZATION

## Server standardization (EC2 + Nginx + Flask world)
- For every client under /srv/webapps/clients/<domain>/frontend/:
  - There is exactly one config file named `msn_<userId>.json`.
  - The universal `index.html` for that client is built from the same template and includes metadata derived from the filename:
    - The `userId`.
    - Optionally the JSON file’s exact name or path.

Example head section:
```html
<head>
  <meta charset="UTF-8">
  <title>Cuyahoga Terra Vita</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- MSN server standard: identifies which msn_<userId>.json this index is bound to -->
  <meta name="msn-id" content="323577191019">
  <meta name="msn-config" content="msn_323577191019.json">

  <link rel="stylesheet" href="/style.css">
</head>
```
- Every internal client follows the same pattern.
- Nginx just serves `index.html` and assets.
- Flask doesn’t need bespoke per-client logic; it just recognizes the `msn_<userId>.json` naming convention and path.

### MSN standardization (works outside your server too)
- Separately, the MSN standard aims to have any host (even if it’s not on this local EC2 box) can be understood by tooling if:
  1. It has an index.html.
  2. That index.html contains MSN metadata like:
```html
<meta name="msn-id" content="323577191019">
<meta name="msn-config" content="msn_323577191019.json">
```
  3. There exists a corresponding msn_<userId>.json on that host, or at a well-defined URL predictable from the metadata.

In other words:
  - The server standard is a concrete implementation of the MSN spec. Any external site that follows the same metadata + filename rules can be “understood” by platform/tooling without being hosted on a particular local server.

This is why it’s important that:
  - The userId is encoded in the JSON filename.
  - That mapping is reflected in the <meta> tags of index.html.

---

## IMPLEMENT MSN STANDARDIZATION
Implement a unified multi-client architecture where each client website is identified only by an msn_<userId>.json file and a universal index.html that contains MSN metadata. Flask should handle all client sites uniformly, using the msn_<userId>.json naming convention to locate the correct config for each domain.

### Key Requirements:
#### 1. Each client directory contains exactly one config file named:
   `msn_<userId>.json`

#### 2. Each client contains a universal index.html that:
   - Is generated from one template
   - Embeds MSN metadata:
       `<meta name="msn-id" content="<userId>">`
       `<meta name="msn-config" content="msn_<userId>.json">`
   - Unified JSON Configuration:
       All client-specific settings that were previously in a separate `settings.json` should now be included directly in the `msn_<userId>.json file.`
       The universal index.html should reference the `msn_<userId>.json` file for all configuration, making that JSON file the single source of truth.

#### 3. Flask backend should:
   - On startup, scan each client directory for `msn_<userId>.json`
   - Extract `userId` from filename
   - Build an in-memory lookup table:
       domain → {user_id, frontend_path, msn_filename}
   - Expose consistent API endpoints for returning the MSN JSON file based on `userId`
   - Use the request Host header (or provided `userId`) to determine which client a request belongs to

#### 4. Frontend JS (build.js):
   - Reads `<meta name="msn-id">` or `window.MSN_CONFIG`
   - Fetches the correct `msn_<userId>.json` from either same-origin or `/api/msn/<userId>.json`
   - Dynamically renders the client site

#### 5. Codex should generate:
   - Flask discovery code
   - Flask API routing code
   - The template for universal index.html
   - Functions for extracting userId from filename
   - Error handling for missing or multiple MSN files

#### Instructions for Codex:
- Do NOT worry about Nginx configuration or filesystem hierarchy; infer from repository.
- Implement scan, map, and API endpoints `inside app.py` or modules referenced by it.
- Provide clean, modular code.
- Assume `index.html` is generated from a template, but show the template.
- Ensure dynamic rendering logic is compatible with a shared build.js.

---

## MATENANCE SCRIPTS

### deploy_srv.sh
```bash
# This script will mirror ~/awsDev/srv/ onto /srv/
#!/bin/bash
set -euo pipefail

# Resolve project root as directory above this script
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

SRC="$PROJECT_ROOT/srv/"
DST="/srv/"

echo "=== Deploying srv → $DST"
echo "Source: $SRC"
echo

# WARNING: --delete removes files in /srv that are not in repo/srv
sudo rsync -az --delete "$SRC" "$DST"

echo
echo "=== Deployment of srv complete."
```

### deploy_nginx.sh
```bash
# This script will mirror ~/awsDev/etc/nginx/ onto /etc/nginx/, then test and reload nginx.
#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

SRC="$PROJECT_ROOT/etc/nginx/"
DST="/etc/nginx/"

echo "=== Deploying etc/nginx → $DST"
echo "Source: $SRC"
echo

# WARNING: --delete removes files under /etc/nginx that are not in repo/etc/nginx
sudo rsync -az --delete "$SRC" "$DST"

echo
echo "=== Testing nginx configuration..."
sudo nginx -t

echo
echo "=== Reloading nginx..."
sudo systemctl reload nginx

echo
echo "=== Deployment of etc/nginx complete."
```

### update_code.sh
```bash
# pull latest from GitHub
#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Updating git repository in $PROJECT_ROOT ..."
git pull --ff-only
echo "=== Git update complete."
```

### deploy_all.sh
```bash
# update + deploy both srv and nginx
#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

./scripts/update_code.sh
./scripts/deploy_srv.sh
./scripts/deploy_nginx.sh

echo
echo "=== Full deploy (srv + nginx) complete."
```

---

## MYCITE PROFILE FRAMEOWKORK

This format is deliberately designed so that:
1. Any website can embed or access a standardized version of a user’s profile.
2. Creative, free-form websites (stored in /webpage/) can reinterpret the same data without layout constraints.
3. Third-party aggregators (markets, co-ops, directories, etc.) can load the same JSON file and render a consistent view.
This project provides both:
- A standardized profile data interface
- A free-form creative layer that consumes the same schema
The result is an extensible personal or organizational site with built-in interoperability and layout independence.

### Conceptual Purpose

The Mycite framework addresses a common problem:
    Websites often contain rich personal or organizational content, but there is no universal, neutral way to exchange or display profiles across platforms.
The Mycite approach solves this by:
- Defining a data-first profile schema (Compendium, Oeuvre, Anthology)
- Allowing creative reinterpretation through a separate free-form site

This allows:
1. A single canonical profile source
    - All information is stored structurally in `msn_<user_id>.json`, independent of HTML layout.
2. Interoperability
    - Any third-party environment can pull the JSON and display a stable profile.
3. Future-proof extension
    - New sections (videos, certifications, links, project groups) can be added to the JSON without breaking existing pages.
This achieves a philosophical and technical goal:
separation of content and representation, enabling multi-context identity display.

---

## FURTHER ENVIORMENT NOTES

### Root

```bash
admin@ip-172-31-30-106:~$ ls -la
total 84
drwx------ 7 admin admin  4096 Dec  3 21:35 .
drwxr-xr-x 3 root  root   4096 Nov 20 15:30 ..
-rw------- 1 admin admin 34335 Dec  4 05:27 .bash_history
-rw-r--r-- 1 admin admin   220 Jul 30 19:28 .bash_logout
-rw-r--r-- 1 admin admin  3578 Nov 27 20:26 .bashrc
drwxrwxr-x 5 admin admin  4096 Nov 28 21:20 .cache
-rw------- 1 admin admin    20 Nov 30 00:03 .lesshst
drwxrwxr-x 3 admin admin  4096 Nov 27 19:34 .local
drwx------ 3 admin admin  4096 Nov 28 21:54 .pki
-rw-r--r-- 1 admin admin   807 Jul 30 19:28 .profile
drwx------ 2 admin admin  4096 Nov 26 00:39 .ssh
-rw-r--r-- 1 admin admin     0 Nov 20 15:45 .sudo_as_admin_successful
drwxrwxr-x 6 admin admin  4096 Dec  4 01:12 awsDev
```

### Repo

```bash
admin@ip-172-31-30-106:~/awsDev$ ls -la
total 32
drwxrwxr-x 6 admin admin 4096 Dec  4 01:12 .
drwx------ 7 admin admin 4096 Dec  3 21:35 ..
drwxrwxr-x 8 admin admin 4096 Dec  4 05:26 .git
-rw-rw-r-- 1 admin admin 6004 Dec  4 01:12 README.md
drwxrwxr-x 3 admin admin 4096 Dec  3 21:35 etc
drwxrwxr-x 2 admin admin 4096 Dec  4 02:33 scripts
drwxrwxr-x 3 admin admin 4096 Dec  3 21:35 srv
```

## License

---

## Acknowledgments

Built and authored by Dylan Montgomery

MODIFIED:	####-##-##
VERSION:	##.##.##
STATUS:     Active prototyping and architectural refinement
