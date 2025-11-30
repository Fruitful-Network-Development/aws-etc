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
      - ├── user_data.js
      - ├── assets/...
      - └── webpage/
        - ├── demo/...
    - ├── data/
      - └── backend_data.json
    - └── config/
      - └── settings.json
  - └── trappfamilyfarm.com/
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

## Matenance Scipts

### ~/script/update_repo.sh
    #!/bin/bash
    set -euo pipefail
    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    cd "$PROJECT_ROOT/repo"
    git pull

### ~/script/update_repo.sh
    #!/bin/bash
    set -euo pipefail
    
    # Project root = one level up from scripts/
    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    
    SRC="$PROJECT_ROOT/repo/srv/"
    DST="$PROJECT_ROOT/deploy/srv/"
    
    # Make sure source exists
    if [ ! -d "$SRC" ]; then
      echo "Source path does not exist: $SRC"
      exit 1
    fi
    
    # Ensure destination exists
    mkdir -p "$DST"
    
    # Sync repo/srv -> deploy/srv
    rsync -az --delete "$SRC" "$DST"
    
    echo "Deployed: $SRC  -->  $DST"

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
