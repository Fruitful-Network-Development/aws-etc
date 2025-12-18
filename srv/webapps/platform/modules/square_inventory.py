# /srv/webapps/platform/modules/square_inventory.py

"""
Square POS inventory integration module for Flask backend.

This module provides endpoints to read inventory and product data from Square's
APIs for use in the platform (e.g., surfacing items on websites or ensuring
donations/products align with POS inventory).

REGISTRATION IN app.py:
-----------------------
To register this Blueprint in your Flask app, add to app.py:

    from modules.square_inventory import square_bp
    app.register_blueprint(square_bp)

This will register the following endpoints:
- GET /api/square/items
- GET /api/square/items/<item_id>/inventory
- GET /api/square/health

ENVIRONMENT VARIABLES:
---------------------
Required:
- SQUARE_ACCESS_TOKEN: Your Square application access token
- SQUARE_LOCATION_ID: Your Square location ID

Optional:
- SQUARE_API_BASE: Square API base URL (defaults to production)
  Production: https://connect.squareup.com
  Sandbox: https://connect.squareupsandbox.com
"""

from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any, List

import requests
from flask import Blueprint, request, jsonify

# Configure logging
logger = logging.getLogger(__name__)

# Flask Blueprint for Square endpoints
square_bp = Blueprint("square_inventory", __name__, url_prefix="/api/square")

# Square API configuration from environment variables
SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
SQUARE_LOCATION_ID = os.getenv("SQUARE_LOCATION_ID")
SQUARE_API_BASE = os.getenv(
    "SQUARE_API_BASE",
    "https://connect.squareup.com"  # Default to production
)


class SquareClientError(Exception):
    """Custom exception for Square API errors."""
    pass


def _get_square_headers() -> Dict[str, str]:
    """
    Get headers for Square API requests.
    
    Returns:
        dict: Headers with authorization and content type
        
    Raises:
        SquareClientError: If access token is not configured
    """
    if not SQUARE_ACCESS_TOKEN:
        raise SquareClientError(
            "Square access token not configured. Set SQUARE_ACCESS_TOKEN."
        )
    
    return {
        "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Square-Version": "2024-01-18"  # Square API version
    }


def _make_square_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make an authenticated request to the Square API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path (e.g., "/v2/catalog/list")
        data: Optional request body as dict
        params: Optional query parameters
        
    Returns:
        dict: JSON response from Square API
        
    Raises:
        SquareClientError: If the request fails
    """
    headers = _get_square_headers()
    url = f"{SQUARE_API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, params=params, timeout=30)
        else:
            raise SquareClientError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.HTTPError as exc:
        error_detail = "Unknown error"
        try:
            error_data = exc.response.json()
            # Square API errors are typically in errors array
            errors = error_data.get("errors", [])
            if errors:
                error_detail = "; ".join(
                    err.get("detail", err.get("code", "Unknown error"))
                    for err in errors
                )
            else:
                error_detail = error_data.get("message", str(exc))
        except (ValueError, AttributeError):
            error_detail = str(exc)
        
        logger.error(f"Square API request failed: {method} {endpoint} - {error_detail}")
        raise SquareClientError(f"Square API error: {error_detail}")
        
    except requests.RequestException as exc:
        logger.error(f"Square API request exception: {exc}")
        raise SquareClientError(f"Square API request failed: {exc}")


def list_catalog_items(
    location_id: Optional[str] = None,
    types: Optional[List[str]] = None,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    List catalog items from Square.
    
    Args:
        location_id: Optional location ID filter (defaults to SQUARE_LOCATION_ID)
        types: Optional list of catalog object types (e.g., ["ITEM", "ITEM_VARIATION"])
        cursor: Optional pagination cursor
        
    Returns:
        dict: Square API response with catalog objects
        
    Raises:
        SquareClientError: If API call fails
    """
    # TODO: Support per-client location_id override (e.g., from client settings)
    # For now, use environment variable or provided location_id
    effective_location_id = location_id or SQUARE_LOCATION_ID
    if not effective_location_id:
        raise SquareClientError(
            "Square location ID not configured. Set SQUARE_LOCATION_ID or provide location_id parameter."
        )
    
    request_data = {
        "location_ids": [effective_location_id]
    }
    
    if types:
        request_data["types"] = types
    else:
        # Default to ITEM and ITEM_VARIATION to get products
        request_data["types"] = ["ITEM", "ITEM_VARIATION"]
    
    if cursor:
        request_data["cursor"] = cursor
    
    return _make_square_request("POST", "/v2/catalog/list", data=request_data)


def get_inventory_counts(
    catalog_object_ids: Optional[List[str]] = None,
    location_ids: Optional[List[str]] = None,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get inventory counts for catalog objects.
    
    Args:
        catalog_object_ids: Optional list of catalog object IDs to filter
        location_ids: Optional list of location IDs (defaults to SQUARE_LOCATION_ID)
        cursor: Optional pagination cursor
        
    Returns:
        dict: Square API response with inventory counts
        
    Raises:
        SquareClientError: If API call fails
    """
    # TODO: Support per-client location_ids override
    effective_location_ids = location_ids or ([SQUARE_LOCATION_ID] if SQUARE_LOCATION_ID else None)
    if not effective_location_ids:
        raise SquareClientError(
            "Square location ID not configured. Set SQUARE_LOCATION_ID or provide location_ids parameter."
        )
    
    request_data = {
        "location_ids": effective_location_ids
    }
    
    if catalog_object_ids:
        request_data["catalog_object_ids"] = catalog_object_ids
    
    if cursor:
        request_data["cursor"] = cursor
    
    return _make_square_request("POST", "/v2/inventory/batch-retrieve-counts", data=request_data)


@square_bp.route("/items", methods=["GET"])
def list_items():
    """
    List products/items from Square catalog.
    
    Query parameters:
        location_id: Optional location ID (overrides SQUARE_LOCATION_ID)
        types: Optional comma-separated list of catalog types (default: ITEM,ITEM_VARIATION)
        cursor: Optional pagination cursor
        include_inventory: Optional boolean to include inventory counts (default: false)
        
    Returns:
        JSON response with list of items:
        {
            "items": [
                {
                    "id": "...",
                    "name": "...",
                    "description": "...",
                    "price": {...},
                    "category": {...},
                    "variations": [...]
                }
            ],
            "cursor": "...",
            "has_more": false
        }
    """
    try:
        # Parse query parameters
        location_id = request.args.get("location_id")
        types_param = request.args.get("types")
        cursor = request.args.get("cursor")
        include_inventory = request.args.get("include_inventory", "false").lower() == "true"
        
        # Parse types if provided
        types = None
        if types_param:
            types = [t.strip() for t in types_param.split(",")]
        
        # Fetch catalog items
        response = list_catalog_items(
            location_id=location_id,
            types=types,
            cursor=cursor
        )
        
        # Extract and format items
        objects = response.get("objects", [])
        items = []
        item_ids = []
        
        for obj in objects:
            obj_type = obj.get("type")
            obj_data = obj.get(obj_type, {})
            
            # Process ITEM objects
            if obj_type == "ITEM":
                item_id = obj.get("id")
                item_ids.append(item_id)
                
                # Get variations for this item
                variation_ids = obj_data.get("item_variation_ids", [])
                variations = []
                for var_obj in objects:
                    if var_obj.get("type") == "ITEM_VARIATION" and var_obj.get("id") in variation_ids:
                        var_data = var_obj.get("ITEM_VARIATION", {})
                        price_money = var_data.get("price_money", {})
                        variations.append({
                            "id": var_obj.get("id"),
                            "name": var_data.get("name"),
                            "price": {
                                "amount": price_money.get("amount"),
                                "currency": price_money.get("currency")
                            } if price_money else None
                        })
                
                # Get category if available
                category_id = obj_data.get("category_id")
                category = None
                if category_id:
                    for cat_obj in objects:
                        if cat_obj.get("type") == "CATEGORY" and cat_obj.get("id") == category_id:
                            category = {
                                "id": category_id,
                                "name": cat_obj.get("CATEGORY", {}).get("name")
                            }
                            break
                
                items.append({
                    "id": item_id,
                    "name": obj_data.get("name"),
                    "description": obj_data.get("description"),
                    "category": category,
                    "variations": variations
                })
        
        # Optionally include inventory counts
        inventory_data = {}
        if include_inventory and item_ids:
            try:
                inventory_response = get_inventory_counts(
                    catalog_object_ids=item_ids,
                    location_ids=[location_id] if location_id else None
                )
                counts = inventory_response.get("counts", [])
                for count in counts:
                    catalog_id = count.get("catalog_object_id")
                    state = count.get("state")
                    quantity = count.get("quantity")
                    if catalog_id:
                        if catalog_id not in inventory_data:
                            inventory_data[catalog_id] = {}
                        inventory_data[catalog_id][state] = quantity
                
                # Attach inventory to items
                for item in items:
                    item["inventory"] = inventory_data.get(item["id"], {})
            except SquareClientError as exc:
                logger.warning(f"Failed to fetch inventory counts: {exc}")
                # Continue without inventory data
        
        result = {
            "items": items,
            "cursor": response.get("cursor"),
            "has_more": bool(response.get("cursor"))
        }
        
        return jsonify(result), 200
        
    except SquareClientError as exc:
        logger.error(f"Square items listing failed: {exc}")
        return jsonify({"error": str(exc)}), 502
    
    except Exception as exc:
        logger.error(f"Unexpected error listing Square items: {exc}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@square_bp.route("/items/<item_id>/inventory", methods=["GET"])
def get_item_inventory(item_id: str):
    """
    Get inventory/stock information for a specific item.
    
    URL parameter:
        item_id: Square catalog object ID (ITEM or ITEM_VARIATION)
        
    Query parameters:
        location_id: Optional location ID (overrides SQUARE_LOCATION_ID)
        
    Returns:
        JSON response with inventory counts:
        {
            "item_id": "...",
            "inventory": {
                "IN_STOCK": 10,
                "RESERVED_FOR_SALE": 2,
                "SOLD": 0
            },
            "location_id": "..."
        }
    """
    if not item_id:
        return jsonify({"error": "item_id is required"}), 400
    
    try:
        location_id = request.args.get("location_id")
        
        # Fetch inventory counts for this item
        response = get_inventory_counts(
            catalog_object_ids=[item_id],
            location_ids=[location_id] if location_id else None
        )
        
        counts = response.get("counts", [])
        inventory = {}
        
        for count in counts:
            if count.get("catalog_object_id") == item_id:
                state = count.get("state")
                quantity = count.get("quantity")
                if state:
                    inventory[state] = quantity
        
        result = {
            "item_id": item_id,
            "inventory": inventory,
            "location_id": location_id or SQUARE_LOCATION_ID
        }
        
        return jsonify(result), 200
        
    except SquareClientError as exc:
        logger.error(f"Square inventory fetch failed: {exc}")
        return jsonify({"error": str(exc)}), 502
    
    except Exception as exc:
        logger.error(f"Unexpected error fetching Square inventory: {exc}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@square_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint for Square module.
    
    Returns:
        JSON response indicating if Square credentials are configured
    """
    has_credentials = bool(SQUARE_ACCESS_TOKEN and SQUARE_LOCATION_ID)
    
    return jsonify({
        "status": "ok" if has_credentials else "misconfigured",
        "api_base": SQUARE_API_BASE,
        "credentials_configured": has_credentials,
        "location_id_configured": bool(SQUARE_LOCATION_ID)
    }), 200 if has_credentials else 503
