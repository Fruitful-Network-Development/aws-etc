# /srv/webapps/platform/app.py

from __future__ import annotations

import json
from pathlib import Path

import requests
from flask import Flask, request, jsonify, send_from_directory, abort, redirect, url_for
from client_context import CLIENTS_ROOT, get_client_slug, get_client_paths
from data_access import load_json  # save_json not needed here
from modules.weather import weather_bp

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
          index.html
          assets/...

    settings.json keys that matter here:
      - frontend_root: e.g. "frontend"
      - default: default page to serve (e.g. "index.html")
      - backend_data_file: filename under data/ for backend state
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
      'index.html'
      'script.js'
      'msn_<user_id>.json'
      'assets/imgs/logo.jpeg'
      'style.css'
    """
    full_path = frontend_root / rel_path
    if not full_path.exists():
        abort(404)

    return send_from_directory(full_path.parent, full_path.name)


CANONICAL_USER_DATA_GLOB = "msn_<user_id>.json"


def extract_user_id_from_msn(msn_value) -> str:
    """Create a stable user_id string from the MSN field in msn_<user_id>.json."""
    if isinstance(msn_value, list):
        parts = [str(item).strip() for item in msn_value if str(item).strip()]
        return "".join(parts)
    if isinstance(msn_value, str):
        return msn_value.strip()
    return ""


def _find_user_data_file(frontend_dir: Path) -> Path | None:
    matches = sorted(frontend_dir.glob(CANONICAL_USER_DATA_GLOB))
    if len(matches) == 1:
        return matches[0]
    # If there are zero or multiple matches, skip to avoid ambiguity
    return None


def _client_user_data_files() -> dict:
    """
    Return mapping of client slug -> canonical msn_<user_id>.json Path for all clients.

    Each client frontend is expected to contain exactly one such file in its root.
    """

    files = {}
    if not CLIENTS_ROOT.exists():
        return files

    for client_dir in CLIENTS_ROOT.iterdir():
        if not client_dir.is_dir():
            continue

        frontend_dir = client_dir / "frontend"
        user_data_path = _find_user_data_file(frontend_dir)
        if user_data_path:
            files[client_dir.name] = user_data_path

    return files


def _user_data_mtimes(files: dict) -> dict:
    return {slug: path.stat().st_mtime for slug, path in files.items()}


USER_MAP_CACHE = {"map": {}, "mtimes": {}}


def refresh_user_map(force_refresh: bool = False) -> dict:
    """Rebuild user_id -> client mappings when files change or on demand."""

    files = _client_user_data_files()
    current_mtimes = _user_data_mtimes(files)

    if not force_refresh and current_mtimes == USER_MAP_CACHE.get("mtimes"):
        return USER_MAP_CACHE.get("map", {})

    user_map: dict = {}
    for client_slug, user_data_path in files.items():
        try:
            user_data = load_json(user_data_path)
        except Exception:
            # Skip clients with malformed JSON so one bad file doesn't break routing.
            continue

        msn_value = user_data.get("MSS", {}).get("MSN")
        user_id = extract_user_id_from_msn(msn_value)
        if user_id:
            user_map[user_id] = client_slug

    USER_MAP_CACHE["map"] = user_map
    USER_MAP_CACHE["mtimes"] = current_mtimes
    return user_map


def get_user_map(force_refresh: bool = False) -> dict:
    return refresh_user_map(force_refresh=force_refresh)


# -------------------------------------------------------------------
# API routes
# -------------------------------------------------------------------


app.register_blueprint(weather_bp)


@app.route("/proxy/<path:client_slug>/<path:data_filename>")
def proxy_user_data(client_slug, data_filename):
    """Fetch remote msn_<user_id>.json with consistent error handling."""

    if (
        Path(data_filename).name != data_filename
        or not data_filename.startswith("msn_")
        or not data_filename.endswith(".json")
    ):
        abort(404)

    remote_url = f"https://{client_slug}/{data_filename}"

    try:
        response = requests.get(remote_url, timeout=10)
    except requests.exceptions.Timeout:
        return jsonify({"error": "timeout", "message": "Remote request timed out"}), 504
    except requests.exceptions.ConnectionError as exc:
        return jsonify(
            {"error": "connection_error", "message": str(exc) or "Connection failed"}
        ), 503
    except requests.RequestException as exc:
        return jsonify(
            {"error": "request_error", "message": str(exc) or "Request failed"}
        ), 502

    if response.status_code == 404:
        return (
            jsonify({"error": "not_found", "message": "user data file not found"}),
            404,
        )

    if response.status_code != 200:
        return (
            jsonify(
                {
                    "error": "upstream_error",
                    "message": f"Upstream returned {response.status_code}",
                }
            ),
            502,
        )

    try:
        data = response.json()
    except ValueError:
        return (
            jsonify({"error": "invalid_json", "message": "Remote data is not valid JSON"}),
            500,
        )

    return jsonify(data)


@app.route('/profiles/<path:client_slug>')
def profiles(client_slug):
    """
    Redirect to our Mycite page but include ?external=<client_slug>.
    The front‑end will read this parameter and use it to load the
    proxied msn_<user_id>.json file.
    """
    return redirect(url_for('mysite_view') + f'?external={client_slug}')


@app.route("/")
def client_root():
    """
    Root route for the domain.

    Uses the client's settings.json to choose the landing page:
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    rel_path = settings.get("default", "index.html")
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
      /frontend/msn_<user_id>.json
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
      /msn_<user_id>.json
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


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # For development only; in production use gunicorn/uwsgi behind NGINX
    app.run(host="0.0.0.0", port=5000, debug=True)
