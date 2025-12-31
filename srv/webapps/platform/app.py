# /srv/webapps/platform/app.py

from __future__ import annotations

import os
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
from modules.donation_receipts import donation_receipts_bp

# -------------------------------------------------------------------
# Configuration and Environment Setup
# -------------------------------------------------------------------


def validate_env(required: list[str] = None, optional: dict[str, str] = None) -> dict[str, str]:
    """
    Validate environment variables and return a config dict.
    
    This helper is intentionally limited to generic, core environment variables.
    Future configuration for client-specific settings (paths, images, colors, build.js behavior)
    will come from msn_<userId>.json files, not from environment variables.
    Additional validation can be added later once the JSON schema is defined.
    
    Args:
        required: List of required environment variable names
        optional: Dict mapping env var names to default values
        
    Returns:
        Dict of validated environment variables
        
    Raises:
        ValueError: If a required environment variable is missing
    """
    if required is None:
        required = []
    if optional is None:
        optional = {}
    
    config = {}
    missing = []
    
    for var in required:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            config[var] = value
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    for var, default in optional.items():
        config[var] = os.getenv(var, default)
    
    return config


# Validate core environment variables
try:
    env_config = validate_env(
        required=['FLASK_SECRET_KEY'],
        optional={
            'FLASK_DEBUG': '0',
            'FLASK_ENABLE_CORS': '0'
        }
    )
except ValueError as e:
    # In development, allow missing FLASK_SECRET_KEY with a clear warning
    if os.getenv('FLASK_ENV') != 'production':
        env_config = {
            'FLASK_SECRET_KEY': 'DEV-ONLY-INSECURE-KEY-DO-NOT-USE-IN-PRODUCTION',
            'FLASK_DEBUG': os.getenv('FLASK_DEBUG', '0'),
            'FLASK_ENABLE_CORS': os.getenv('FLASK_ENABLE_CORS', '0')
        }
        print("⚠️  WARNING: Using development-only SECRET_KEY. Set FLASK_SECRET_KEY in production!")
    else:
        raise


# Initialize Flask app
app = Flask(__name__)

# SECRET_KEY is critical for Flask's session management and cookie signing.
# Without it, sessions are cryptographically insecure and vulnerable to tampering.
# The fallback value above is ONLY for development and must never be used in production.
app.config['SECRET_KEY'] = env_config['FLASK_SECRET_KEY']

# Production configuration settings
# DEBUG should be False in production to prevent exposing error details and enabling auto-reload
app.config['DEBUG'] = env_config['FLASK_DEBUG'] in ('1', 'true', 'True', 'yes', 'Yes')

# Additional production settings
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Disable pretty JSON in production
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # Cache static files for 1 year


# -------------------------------------------------------------------
# Optional CORS Configuration
# -------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) is needed when your API is accessed
# from browsers on different domains/origins than your Flask server.
# If your frontend is served from the same domain or handled by Nginx,
# you may not need CORS. This section can be ignored or removed if not needed.

if env_config['FLASK_ENABLE_CORS'] == '1':
    try:
        from flask_cors import CORS
        # Configure CORS to allow requests from specified origins
        # Update ALLOWED_ORIGINS environment variable with comma-separated origins if needed
        allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else ['*']
        CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
        print("✓ CORS enabled for /api/* routes")
    except ImportError:
        print("⚠️  WARNING: FLASK_ENABLE_CORS is set but flask-cors is not installed.")
        print("   Install with: pip install flask-cors")


# -------------------------------------------------------------------
# Future: Request Validation and Rate Limiting
# -------------------------------------------------------------------
# As the platform grows, you may want to add:
# - Request size limits (MAX_CONTENT_LENGTH)
# - Rate limiting to prevent abuse (consider Flask-Limiter)
# - Input validation middleware
# - Request logging and monitoring
#
# Example rate limiting (requires: pip install flask-limiter):
#   from flask_limiter import Limiter
#   from flask_limiter.util import get_remote_address
#   limiter = Limiter(app=app, key_func=get_remote_address)
#   Then add @limiter.limit("10 per minute") decorators to routes


# -------------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------------
# These are basic placeholders that can be improved later with custom templates
# or more detailed error responses based on your API design.


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    # For now, return a simple string. This can be enhanced later with
    # custom templates or JSON error responses based on request content type.
    return 'Not Found', 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error."""
    # In production, you may want to log this error and return a generic message
    # to avoid exposing internal details. This is a placeholder for future enhancement.
    return 'Internal Server Error', 500


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
# Blueprint Registration
# -------------------------------------------------------------------
# All Flask blueprints should be registered here. Blueprints allow you to
# organize routes into separate modules (e.g., weather.py, paypal_gateway.py).
# To add a new blueprint:
#   1. Import it: from modules.your_module import your_bp
#   2. Register it: app.register_blueprint(your_bp)


app.register_blueprint(weather_bp)
app.register_blueprint(donation_receipts_bp)

# Example of how to register additional blueprints (commented out until needed):
# from modules.paypal_gateway import paypal_bp
# from modules.donation_box import donation_bp
# from modules.square_inventory import square_bp
# app.register_blueprint(paypal_bp)
# app.register_blueprint(donation_bp)
# app.register_blueprint(square_bp)


# -------------------------------------------------------------------
# API routes
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# Static File Serving Routes (Fallback Only - Currently Unused)
# -------------------------------------------------------------------
# NOTE: These routes are FALLBACK-ONLY and are currently UNUSED in production.
#
# Current architecture:
# - NGINX serves all static files directly using 'root' and 'try_files' directives
# - Only /api/* requests are proxied to Gunicorn/Flask
# - These Flask routes would only be hit if NGINX configuration changed to proxy
#   non-API requests to Gunicorn
#
# These routes are kept for:
# 1. Development/testing scenarios where Flask dev server is used
# 2. Potential future architecture changes where Flask handles routing
# 3. Fallback if NGINX misconfiguration causes static files to miss
#
# DO NOT add proxy_pass for root location in NGINX unless you intend for Flask
# to handle static file serving (which is less efficient than NGINX direct serving).
# -------------------------------------------------------------------


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


# Fallback route: Serves default entry file (index.html) for client
# Currently unused - NGINX handles this via root/index directives
@app.route("/")
def client_root():
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    rel_path = settings.get("default_entry", "index.html")
    return serve_client_file(settings["frontend_dir"], rel_path)


# Fallback route: Serves assets from frontend/assets/
# Currently unused - NGINX serves static files directly
@app.route("/assets/<path:asset_path>")
def client_assets(asset_path: str):
    """
    Serve client-specific assets (images, fonts, etc.) under frontend/assets/.
      /assets/imgs/logo.jpeg -> frontend/assets/imgs/logo.jpeg
    
    NOTE: This route is currently unused. NGINX serves static assets directly.
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    rel_path = f"assets/{asset_path}"
    return serve_client_file(settings["frontend_dir"], rel_path)


# Fallback route: Serves files under /frontend/ path
# Currently unused - NGINX serves static files directly
@app.route("/frontend/<path:static_path>")
def client_frontend_static(static_path: str):
    """
    Serve files addressed explicitly under /frontend/, like:
      /frontend/style.css
      /frontend/app.js
      /frontend/script.js
      /frontend/msn_<user_id>.json
    
    NOTE: This route is currently unused. NGINX serves static files directly.
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    settings = load_client_settings(client_slug, paths=paths)

    return serve_client_file(settings["frontend_dir"], static_path)


# Fallback route: Catch-all for frontend files
# Currently unused - NGINX serves static files directly
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
    
    NOTE: This route is currently unused. NGINX serves static files directly
    using root and try_files directives. Only /api/* requests reach Flask.
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


# -------------------------------------------------------------------
# Development Server (for local testing only)
# -------------------------------------------------------------------
# In production, use Gunicorn or uWSGI behind Nginx.
# The DEBUG flag from environment variables controls whether debug mode is enabled.


if __name__ == "__main__":
    # For development only; in production use gunicorn/uwsgi behind NGINX
    app.run(host="0.0.0.0", port=5000, debug=app.config['DEBUG'])
