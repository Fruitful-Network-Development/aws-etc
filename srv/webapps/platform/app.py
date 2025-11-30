# /srv/webapps/platform/app.py

import json
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, abort, redirect, url_for
from urllib.request import urlopen
from client_context import get_client_slug, get_client_paths
from data_access import load_json  # save_json not needed here

app = Flask(__name__)


# -------------------------------------------------------------------
# Helpers for client-specific frontend behavior
# -------------------------------------------------------------------

def load_client_settings(client_slug: str, paths=None) -> dict:
    """
    Load config/settings.json for a given client and derive useful paths.

    Expected layout for a client (e.g. fruitfulnetworkdevelopment.com):

      client_root/
        config/settings.json
        frontend/
          mycite.html
          index.html (optional)
          webpage/home.html
          assets/...

    settings.json keys that matter here:
      - frontend_root: e.g. "frontend"
      - backend_data_file (optional)
    """
    if paths is None:
        paths = get_client_paths(client_slug)

    config_dir: Path = paths["config_dir"]
    client_root: Path = paths["client_root"]

    settings_path = config_dir / "settings.json"
    if not settings_path.exists():
        raise FileNotFoundError(
            f"settings.json not found for client {client_slug}: {settings_path}"
        )

    with settings_path.open("r") as f:
        settings = json.load(f)

    # Where the frontend lives relative to client_root
    frontend_dir = paths.get(
        "frontend_dir",
        client_root / settings.get("frontend_root", "frontend"),
    )
    if not frontend_dir.exists():
        raise FileNotFoundError(
            f"Frontend dir not found for client {client_slug}: {frontend_dir}"
        )

    # Attach handy derived paths onto the settings dict
    settings["_client_root"] = client_root
    settings["_config_dir"] = config_dir
    settings["_frontend_dir"] = frontend_dir

    backend_name = settings.get("backend_data_file", "backend_data.json")
    settings["_backend_data_path"] = client_root / "data" / backend_name

    return settings


def serve_client_file(frontend_root: Path, rel_path: str):
    """
    Serve a file relative to the client's frontend root.

    rel_path examples:
      'mycite.html'
      'webpage/home.html'
      'assets/imgs/logo.jpeg'
      'style.css'
    """
    full_path = frontend_root / rel_path
    if not full_path.exists():
        abort(404)

    return send_from_directory(full_path.parent, full_path.name)


def get_default_page(settings: dict) -> str:
    """
    Decide which page to serve at "/" based on settings.json.

    settings.json keys used:
      - default_view_mode: "auto" | "mysite" | "webpage"
      - mysite_page:      e.g. "mycite.html"
      - webpage_home:     e.g. "webpage/home.html"
      - fallback_index:   e.g. "index.html"
    """
    mode = settings.get("default_view_mode", "auto")
    mysite_page = settings.get("mysite_page", "mycite.html")
    webpage_home = settings.get("webpage_home", "webpage/home.html")
    fallback_index = settings.get("fallback_index", "index.html")

    frontend_root: Path = settings["_frontend_dir"]

    mysite_full = frontend_root / mysite_page
    home_full = frontend_root / webpage_home
    fallback_full = frontend_root / fallback_index

    # Explicit overrides
    if mode == "mysite":
        if not mysite_full.exists():
            abort(404)
        return mysite_page

    if mode == "webpage":
        if not home_full.exists():
            abort(404)
        return webpage_home

    # "auto" mode:
    # Prefer a traditional webpage home if it exists,
    # then Mycite, then a simple index.html fallback.
    if home_full.exists():
        return webpage_home
    if mysite_full.exists():
        return mysite_page
    if fallback_full.exists():
        return fallback_index

    abort(404)


# -------------------------------------------------------------------
# Frontend routes (per-client HTML + static assets)
# -------------------------------------------------------------------


def fetch_remote_json(url):
    """Fetch JSON from a remote URL using urllib."""
    try:
        resp = urlopen(url)
        # Only proceed if we get HTTP 200 (OK)
        if resp.getcode() == 200:
            # Decode bytes and parse JSON:contentReference[oaicite:3]{index=3}.
            return json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        raise RuntimeError(f'Could not fetch {url}: {exc}')

    raise RuntimeError(f'Non‑200 response for {url}')

@app.route('/proxy/<path:client_slug>/user_data.json')
def proxy_user_data(client_slug):
    """
    Fetch a user_data.json file from another site and return it as JSON.
    A client_slug like 'example.com' will be turned into
    'https://example.com/frontend/user_data.json'.  Adjust the URL pattern
    if your client sites expose the JSON elsewhere.
    """
    remote_url = f'https://{client_slug}/frontend/user_data.json'
    try:
        data = fetch_remote_json(remote_url)
    except Exception as e:
        abort(502, description=str(e))

    return jsonify(data)

@app.route('/profiles/<path:client_slug>')
def profiles(client_slug):
    """
    Redirect to our Mycite page but include ?external=<client_slug>.
    The front‑end will read this parameter and use it to load the
    proxied user_data.json.
    """
    # url_for('mysite_view') builds the URL of the /mysite route:contentReference[oaicite:4]{index=4}.
    return redirect(url_for('mysite_view') + f'?external={client_slug}')


@app.route("/")
def client_root():
    """
    Root route for the domain.

    Uses the client's settings.json to choose the landing page:
      - webpage_home (e.g. webpage/home.html), if present
      - else mysite_page (e.g. mycite.html), if present
      - else fallback_index (e.g. index.html)
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    rel_path = get_default_page(settings)
    return serve_client_file(settings["_frontend_dir"], rel_path)


@app.route("/mysite")
def mysite_view():
    """
    Explicit route to the Mycite / MySite framework (mysite_page).
    e.g. /mysite -> frontend/mycite.html
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    rel_path = settings.get("mysite_page", "mycite.html")
    return serve_client_file(settings["_frontend_dir"], rel_path)


@app.route("/webpage/<page_slug>")
def webpage_page(page_slug: str):
    """
    Serve pages under frontend/webpage/.

    Uses optional 'routes' mapping from settings.json; otherwise:
      /webpage/home        -> frontend/webpage/home.html
      /webpage/csa_browser -> frontend/webpage/csa_browser.html
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    route_map = settings.get("routes", {})
    if page_slug in route_map:
        rel_path = route_map[page_slug]
    else:
        rel_path = f"webpage/{page_slug}.html"

    return serve_client_file(settings["_frontend_dir"], rel_path)


@app.route("/demo-design-1")
def demo_design_1():
    """
    Serve the specific demo subpage:
      /demo-design-1 -> frontend/webpage/demo-design-1/demo-design-1.html
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    rel_path = "webpage/demo-design-1/demo-design-1.html"
    return serve_client_file(settings["_frontend_dir"], rel_path)


@app.route("/assets/<path:asset_path>")
def client_assets(asset_path: str):
    """
    Serve client-specific assets (images, fonts, etc.) under frontend/assets/.
      /assets/imgs/logo.jpeg -> frontend/assets/imgs/logo.jpeg
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    rel_path = f"assets/{asset_path}"
    return serve_client_file(settings["_frontend_dir"], rel_path)


@app.route("/frontend/<path:static_path>")
def client_frontend_static(static_path: str):
    """
    Serve files addressed explicitly under /frontend/, like:
      /frontend/style.css
      /frontend/app.js
      /frontend/script.js
      /frontend/user_data.js
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    return serve_client_file(settings["_frontend_dir"], static_path)

@app.route("/<path:filename>")
def client_catch_all(filename: str):
    """
    Catch-all for other front-end files that live directly under frontend/.

    Examples:
      /style.css
      /app.js
      /script.js
      /user_data.js
      /mycite.html
      /demo-design-1  -> demo-design-1.html
    (Note: /api/... is reserved for API endpoints.)
    """
    if filename.startswith("api/"):
        abort(404)

    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    # If the filename has no extension, assume it's an .html page
    if "." not in filename:
        filename = f"{filename}.html"

    return serve_client_file(settings["_frontend_dir"], filename)


# -------------------------------------------------------------------
# API routes
# -------------------------------------------------------------------

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # For development only; in production use gunicorn/uwsgi behind NGINX
    app.run(host="0.0.0.0", port=5000, debug=True)
