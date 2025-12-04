# aws-ec2-dev

## Project Layout

```
- ├── /ect 
  - └── nginx/
    - ├── nginx.conf
    - ├── sites-available/
      - ├── fruitfulnetworkdevelopment.com.conf
      - └── fruitfulnetwork.com.conf
    - └── sites-enabled/
      - └── fruitfulnetworkdevelopment.com.conf
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

## Matenance Scipts

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

## Mycite Profile Framework

The Mycite Profile Framework provides a unified data schema (`msn_<user_id>.json`) and a standardized rendering layer defined at the repository root (index.html, style.css, app.js), which together establish a neutral, interoperable profile format.

This format is deliberately designed so that:
1. Any website can embed or access a standardized version of a user’s profile.
2. Creative, free-form websites (stored in /webpage/) can reinterpret the same data without layout constraints.
3. Third-party aggregators (markets, co-ops, directories, etc.) can load the same JSON file and render a consistent view.
This project provides both:
- A standardized profile interface (Mycite View)
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
2. Multiple render layers
    - Mycite Standard View → neutral, predictable, portable
    - Free-form Webpage View → expressive, themeable, personal
3. Interoperability
    - Any third-party environment can pull the JSON and display a stable profile.
4. Future-proof extension
    - New sections (videos, certifications, links, project groups) can be added to the JSON without breaking existing pages.
This achieves a philosophical and technical goal:
separation of content and representation, enabling multi-context identity display.

---

## Possible Ideas

### Mycite Profile Directory — Idea of Operation
The **Fruitful Network Development** site acts as a **central profile directory** that can display Mycite profiles from any client website. Each client site exposes a standardized `msn_<user_id>.json`, which the directory loads and renders inside the Mycite layout.
- Every Mycite-capable domain must publish `https://<client>/msn_<user_id>.json` using the shared schema.
- Then the Fruitful Network Development website reloads the same universal index.html with build.js, but using called profile JSON file.


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
