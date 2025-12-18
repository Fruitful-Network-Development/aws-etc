# /srv/webapps/platform/modules/paypal_gateway.py

"""
PayPal card processing module for Flask backend.

This module provides a Flask Blueprint with endpoints for:
- Creating PayPal orders
- Capturing PayPal orders
- Webhook handling (stub for future implementation)

All PayPal API credentials are read from environment variables.

REGISTRATION IN app.py:
-----------------------
To register this Blueprint in your Flask app, add to app.py:

    from modules.paypal_gateway import paypal_bp
    app.register_blueprint(paypal_bp)

This will register the following endpoints:
- POST /api/payments/paypal/create-order
- POST /api/payments/paypal/capture-order
- POST /api/payments/paypal/webhook
- GET  /api/payments/paypal/health

ENVIRONMENT VARIABLES:
---------------------
Required:
- PAYPAL_CLIENT_ID: Your PayPal application client ID
- PAYPAL_CLIENT_SECRET: Your PayPal application client secret

Optional:
- PAYPAL_API_BASE: PayPal API base URL (defaults to sandbox)
  Production: https://api-m.paypal.com
  Sandbox: https://api-m.sandbox.paypal.com
"""

from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import requests
from flask import Blueprint, request, jsonify

# Configure logging
logger = logging.getLogger(__name__)

# Flask Blueprint for PayPal endpoints
paypal_bp = Blueprint("paypal", __name__, url_prefix="/api/payments/paypal")

# PayPal API configuration from environment variables
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_API_BASE = os.getenv(
    "PAYPAL_API_BASE", 
    "https://api-m.sandbox.paypal.com"  # Default to sandbox for safety
)

# In-memory token cache (in production, consider Redis or similar)
_token_cache: Optional[Dict[str, Any]] = None


class PayPalClientError(Exception):
    """Custom exception for PayPal API errors."""
    pass


def get_paypal_access_token() -> str:
    """
    Obtain or refresh a PayPal OAuth access token.
    
    Uses client credentials flow. Caches the token until it expires.
    
    Returns:
        str: Access token for PayPal API requests
        
    Raises:
        PayPalClientError: If authentication fails
    """
    global _token_cache
    
    # Check if we have a valid cached token
    if _token_cache and _token_cache.get("expires_at"):
        expires_at = _token_cache.get("expires_at")
        if datetime.now() < expires_at:
            return _token_cache["access_token"]
    
    # Validate credentials are configured
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise PayPalClientError(
            "PayPal credentials not configured. Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET."
        )
    
    # Determine OAuth endpoint based on API base URL
    if "sandbox" in PAYPAL_API_BASE:
        oauth_url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    else:
        oauth_url = "https://api-m.paypal.com/v1/oauth2/token"
    
    # Request access token
    auth = (PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(
            oauth_url,
            auth=auth,
            headers=headers,
            data=data,
            timeout=10
        )
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 32400)  # Default 9 hours
        
        if not access_token:
            raise PayPalClientError("PayPal OAuth response missing access_token")
        
        # Cache the token (expire 5 minutes before actual expiry for safety)
        expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
        _token_cache = {
            "access_token": access_token,
            "expires_at": expires_at
        }
        
        logger.info("PayPal access token obtained successfully")
        return access_token
        
    except requests.RequestException as exc:
        logger.error(f"PayPal OAuth request failed: {exc}")
        raise PayPalClientError(f"Failed to obtain PayPal access token: {exc}")


def _make_paypal_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Make an authenticated request to the PayPal API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path (e.g., "/v2/checkout/orders")
        data: Optional request body as dict
        headers: Optional additional headers
        
    Returns:
        dict: JSON response from PayPal API
        
    Raises:
        PayPalClientError: If the request fails
    """
    access_token = get_paypal_access_token()
    
    url = f"{PAYPAL_API_BASE}{endpoint}"
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    if headers:
        request_headers.update(headers)
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, headers=request_headers, timeout=30)
        elif method.upper() == "GET":
            response = requests.get(url, headers=request_headers, timeout=30)
        elif method.upper() == "PATCH":
            response = requests.patch(url, json=data, headers=request_headers, timeout=30)
        else:
            raise PayPalClientError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.HTTPError as exc:
        error_detail = "Unknown error"
        try:
            error_data = exc.response.json()
            error_detail = error_data.get("message", str(exc))
        except (ValueError, AttributeError):
            error_detail = str(exc)
        
        logger.error(f"PayPal API request failed: {method} {endpoint} - {error_detail}")
        raise PayPalClientError(f"PayPal API error: {error_detail}")
        
    except requests.RequestException as exc:
        logger.error(f"PayPal API request exception: {exc}")
        raise PayPalClientError(f"PayPal API request failed: {exc}")


@paypal_bp.route("/create-order", methods=["POST"])
def create_order():
    """
    Create a PayPal order for card processing.
    
    Request body (JSON):
    {
        "amount": 10.00,              # Required: payment amount
        "currency": "USD",            # Required: currency code (USD, EUR, etc.)
        "client_id": "optional",      # Optional: client/site identifier for multi-tenant
        "description": "optional",    # Optional: order description
        "items": [                    # Optional: line items
            {
                "name": "Item name",
                "quantity": 1,
                "unit_amount": {"value": "10.00", "currency_code": "USD"}
            }
        ]
    }
    
    Returns:
        JSON response with order ID and approval links:
        {
            "order_id": "5O190127TN364715T",
            "status": "CREATED",
            "links": [...]
        }
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    # Validate required fields
    amount = data.get("amount")
    currency = data.get("currency", "USD")
    items = data.get("items")
    
    # If items are provided, amount is optional (will be calculated from items)
    # If items are not provided, amount is required
    if not items:
        if amount is None:
            return jsonify({"error": "amount is required when items are not provided"}), 400
        
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                return jsonify({"error": "amount must be greater than 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "amount must be a valid number"}), 400
    else:
        # Items are provided - validate and calculate total from items
        try:
            items_total = 0.0
            for item in items:
                if not isinstance(item, dict):
                    return jsonify({"error": "items must be an array of objects"}), 400
                
                unit_amount = item.get("unit_amount", {})
                if not isinstance(unit_amount, dict):
                    return jsonify({"error": "item unit_amount must be an object"}), 400
                
                try:
                    item_value = float(unit_amount.get("value", 0))
                    item_quantity = int(item.get("quantity", 1))
                except (ValueError, TypeError) as e:
                    return jsonify({
                        "error": "item unit_amount.value and quantity must be valid numbers"
                    }), 400
                
                if item_value < 0:
                    return jsonify({"error": "item unit_amount.value cannot be negative"}), 400
                if item_quantity < 1:
                    return jsonify({"error": "item quantity must be at least 1"}), 400
                
                items_total += item_value * item_quantity
            
            # If amount is also provided, validate it matches items total (within 0.01 tolerance for rounding)
            if amount is not None:
                try:
                    amount_float = float(amount)
                    if abs(amount_float - items_total) > 0.01:
                        return jsonify({
                            "error": "amount does not match items total",
                            "amount_provided": amount_float,
                            "items_total": round(items_total, 2)
                        }), 400
                except (ValueError, TypeError):
                    return jsonify({"error": "amount must be a valid number"}), 400
            
            # Use items total as the amount
            amount_float = items_total
        except (ValueError, TypeError) as e:
            return jsonify({
                "error": "invalid items data",
                "details": "items must contain valid numeric values for unit_amount.value and quantity"
            }), 400
    
    # Format amount as string with 2 decimal places
    amount_str = f"{amount_float:.2f}"
    
    # Build PayPal order request
    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": currency.upper(),
                    "value": amount_str
                }
            }
        ]
    }
    
    # Add description if provided
    description = data.get("description")
    if description:
        order_data["purchase_units"][0]["description"] = description
    
    # Add line items if provided
    if items:
        order_data["purchase_units"][0]["items"] = items
    
    # Optional: Add application context for return/cancel URLs
    # (Frontend can handle redirects, but we can set these if needed)
    return_url = data.get("return_url")
    cancel_url = data.get("cancel_url")
    if return_url or cancel_url:
        order_data["application_context"] = {}
        if return_url:
            order_data["application_context"]["return_url"] = return_url
        if cancel_url:
            order_data["application_context"]["cancel_url"] = cancel_url
    
    try:
        # Create order via PayPal API
        response = _make_paypal_request("POST", "/v2/checkout/orders", data=order_data)
        
        # Extract relevant information for frontend
        order_id = response.get("id")
        status = response.get("status")
        links = response.get("links", [])
        
        # Find approval link if available
        approval_link = None
        for link in links:
            if link.get("rel") == "approve":
                approval_link = link.get("href")
                break
        
        result = {
            "order_id": order_id,
            "status": status,
            "approval_url": approval_link,
            "links": links
        }
        
        # Log client identifier if provided (for multi-tenant tracking)
        client_id = data.get("client_id")
        if client_id:
            logger.info(f"PayPal order created for client: {client_id}, order_id: {order_id}")
        
        return jsonify(result), 201
        
    except PayPalClientError as exc:
        logger.error(f"PayPal order creation failed: {exc}")
        return jsonify({"error": str(exc)}), 502
    
    except Exception as exc:
        logger.error(f"Unexpected error creating PayPal order: {exc}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@paypal_bp.route("/capture-order", methods=["POST"])
def capture_order():
    """
    Capture a PayPal order after approval.
    
    Request body (JSON):
    {
        "order_id": "5O190127TN364715T"  # Required: PayPal order ID
    }
    
    Returns:
        JSON response with capture details:
        {
            "order_id": "5O190127TN364715T",
            "status": "COMPLETED",
            "transaction_id": "...",
            "amount": {...},
            "payer": {...}
        }
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    order_id = data.get("order_id")
    if not order_id:
        return jsonify({"error": "order_id is required"}), 400
    
    try:
        # Capture the order via PayPal API
        response = _make_paypal_request(
            "POST",
            f"/v2/checkout/orders/{order_id}/capture",
            data={}  # Empty body for capture
        )
        
        # Extract relevant information
        captured_order_id = response.get("id")
        status = response.get("status")
        
        # Get transaction details from purchase units
        purchase_units = response.get("purchase_units", [])
        transaction_id = None
        amount_info = None
        if purchase_units:
            payments = purchase_units[0].get("payments", {})
            captures = payments.get("captures", [])
            if captures:
                transaction_id = captures[0].get("id")
                amount_info = captures[0].get("amount")
        
        # Get payer information
        payer = response.get("payer", {})
        
        result = {
            "order_id": captured_order_id,
            "status": status,
            "transaction_id": transaction_id,
            "amount": amount_info,
            "payer": payer,
            "full_response": response  # Include full response for debugging/future use
        }
        
        logger.info(f"PayPal order captured: {order_id}, status: {status}")
        return jsonify(result), 200
        
    except PayPalClientError as exc:
        logger.error(f"PayPal order capture failed: {exc}")
        return jsonify({"error": str(exc)}), 502
    
    except Exception as exc:
        logger.error(f"Unexpected error capturing PayPal order: {exc}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@paypal_bp.route("/webhook", methods=["POST"])
def webhook():
    """
    Webhook endpoint for PayPal event notifications.
    
    This is a stub implementation. In production, you should:
    1. Verify webhook signatures
    2. Process events (payment completed, refunded, etc.)
    3. Update your database/state accordingly
    
    Request body: PayPal webhook event JSON
    
    Returns:
        JSON response acknowledging receipt
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    event_data = request.get_json()
    event_type = event_data.get("event_type") if event_data else None
    
    logger.info(f"PayPal webhook received: {event_type}")
    
    # TODO: Implement webhook signature verification
    # TODO: Process webhook events based on event_type
    # TODO: Update order status in database
    
    return jsonify({"status": "received", "event_type": event_type}), 200


@paypal_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint for PayPal module.
    
    Returns:
        JSON response indicating if PayPal credentials are configured
    """
    has_credentials = bool(PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)
    
    return jsonify({
        "status": "ok" if has_credentials else "misconfigured",
        "api_base": PAYPAL_API_BASE,
        "credentials_configured": has_credentials
    }), 200 if has_credentials else 503
