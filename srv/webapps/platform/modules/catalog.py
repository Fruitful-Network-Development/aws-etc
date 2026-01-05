# /srv/webapps/platform/modules/catalog.py
from __future__ import annotations

from flask import Blueprint, jsonify
from data_access import load_platform_json

# Blueprint for platform-level catalog data
catalog_bp = Blueprint("catalog", __name__, url_prefix="/api")

@catalog_bp.route("/taxonomy", methods=["GET"])
def get_taxonomy():
    """Return the global taxonomy JSON."""
    try:
        data = load_platform_json("taxonomy.json")
    except FileNotFoundError:
        return jsonify({"error": "not_found", "message": "taxonomy.json not found"}), 404
    return jsonify(data)

@catalog_bp.route("/product-types", methods=["GET"])
def get_product_types():
    """Return the global product_type list."""
    try:
        data = load_platform_json("product_type.json")
    except FileNotFoundError:
        return jsonify(
            {"error": "not_found", "message": "product_type.json not found"}
        ), 404
    return jsonify(data)
