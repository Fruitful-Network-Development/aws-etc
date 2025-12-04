# /srv/webapps/platform/app.py

from __future__ import annotations

from pathlib import Path

import requests
from flask import Flask, request, jsonify, send_from_directory, abort, redirect, url_for

from data_access import (
    get_client_paths,
    get_client_slug,
    load_client_manifest,
    load_json,
    resolve_backend_data_path,
    save_json,
)
from modules.weather import weather_bp

app = Flask(__name__)


# -------------------------------------------------------------------
# Helpers for client-specific frontend behavior backed by msn_<user>.json
# -------------------------------------------------------------------

def load_client_settings(client_slug: str, paths=None) -> dict:
    """
    Load the client manifest from msn_<user>.json and expose the core values
    the Flask app needs: frontend root, default entry file, and backend data
    whitelist.
    """

    if paths is None:
        paths = get_client_paths(client_slug)

    manifest = load_client_manifest(paths)

    frontend_dir = manifest["frontend_dir"]
    if not frontend_dir.exists():
        raise FileNotFoundError(
            f"Frontend dir not found for client {client_slug}: {frontend_dir}"
        )

    return manifest


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
    return redirect(url_for('client_root') + f'?external={client_slug}')


@app.route("/api/backend-data/<path:data_filename>", methods=["GET", "PUT"])
def backend_data(data_filename: str):
    """Read or write backend data declared in the client's msn_<user>.json."""

    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    try:
        target_path = resolve_backend_data_path(paths, settings, data_filename)
    except ValueError as exc:
        return jsonify({"error": "invalid_backend_data", "message": str(exc)}), 400

    if request.method == "GET":
        if not target_path.exists():
            abort(404)

        return jsonify(load_json(target_path))

    try:
        payload = request.get_json(force=True)
    except Exception:
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body must be valid JSON",
                }
            ),
            400,
        )

    save_json(target_path, payload)
    return jsonify({"status": "ok"})

@app.route("/")
def client_root():
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    rel_path = settings.get("default_entry", "index.html")
    return serve_client_file(settings["frontend_dir"], rel_path)


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
    return serve_client_file(settings["frontend_dir"], rel_path)


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

    return serve_client_file(settings["frontend_dir"], static_path)


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

    return serve_client_file(settings["frontend_dir"], filename)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # For development only; in production use gunicorn/uwsgi behind NGINX
    app.run(host="0.0.0.0", port=5000, debug=True)
