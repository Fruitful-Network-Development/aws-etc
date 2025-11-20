# /srv/webapps/platform/app.py

from flask import Flask, request, jsonify
from client_context import get_client_slug, get_client_paths
from data_access import load_json, save_json

# Placeholder module imports
from modules import donations, payments, pos_integration

app = Flask(__name__)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/text", methods=["GET"])
def get_text():
    """
    Returns the full text JSON for the current client.
    Optionally accepts ?page=home to filter.
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)

    text_path = paths["data_dir"] / "client_1_text.json"  # name per client or just text.json

    text_data = load_json(text_path, default={})
    page = request.args.get("page")

    if page and page in text_data:
        return jsonify(text_data[page])
    return jsonify(text_data)


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    """
    Example: GET /api/inventory
    Returns this client's inventory.json content.
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    inventory_path = paths["data_dir"] / "inventory.json"

    inventory = load_json(inventory_path, default=[])
    return jsonify(inventory)


@app.route("/api/customers", methods=["GET"])
def get_customers():
    """
    Example: GET /api/customers
    Returns this client's customers.json (or donors.json, etc.).
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)
    customers_path = paths["data_dir"] / "customers.json"  # adjust per client

    customers = load_json(customers_path, default=[])
    return jsonify(customers)


# --- Placeholder donation endpoint using a module ---
@app.route("/api/donations", methods=["POST"])
def create_donation():
    """
    Example POST endpoint to record a donation for the current client.
    The real logic would live in modules/donations.py.
    """
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)

    # Delegate logic to the donations module (placeholder)
    result = donations.handle_donation(request, client_slug, paths)
    return jsonify(result), 201


# --- Placeholder PayPal route ---
@app.route("/api/paypal/create-order", methods=["POST"])
def paypal_create_order():
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)

    # Delegate to payments module (placeholder)
    order = payments.create_order(request, client_slug, paths)
    return jsonify(order), 201


# --- Placeholder POS integration route ---
@app.route("/api/pos/sync", methods=["POST"])
def pos_sync():
    client_slug = get_client_slug(request)
    paths = get_client_paths(client_slug)

    result = pos_integration.sync_from_pos(request, client_slug, paths)
    return jsonify(result), 200


if __name__ == "__main__":
    # For development only; in production you'll use gunicorn/uwsgi
    app.run(host="0.0.0.0", port=5000, debug=True)

