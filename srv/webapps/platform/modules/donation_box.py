# /srv/webapps/platform/modules/donation_box.py

"""
Donation box abstraction module for Flask backend.

This module provides a provider-agnostic donation interface that abstracts
payment provider details (PayPal, Stripe, etc.) behind a simple JSON API.

REGISTRATION IN app.py:
-----------------------
To register this Blueprint in your Flask app, add to app.py:

    from modules.donation_box import donation_bp
    app.register_blueprint(donation_bp)

This will register the following endpoints:
- POST /api/donations/create
- POST /api/donations/confirm
- GET  /api/donations/status/<donation_id>
"""

from __future__ import annotations

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from flask import Blueprint, request, jsonify

# Import PayPal gateway functions for provider integration
from modules.paypal_gateway import _make_paypal_request, PayPalClientError

# Configure logging
logger = logging.getLogger(__name__)

# Flask Blueprint for donation endpoints
donation_bp = Blueprint("donations", __name__, url_prefix="/api/donations")

# In-memory donation store
# TODO: Replace with persistent database (e.g., PostgreSQL, SQLite)
# Key: donation_reference_id (str)
# Value: donation record dict
_donations_store: Dict[str, Dict[str, Any]] = {}


class DonationError(Exception):
    """Custom exception for donation processing errors."""
    pass


def _generate_donation_id() -> str:
    """
    Generate a unique donation reference ID.
    
    Returns:
        str: Unique donation reference ID (UUID-based)
    """
    return f"don_{uuid.uuid4().hex[:16]}"


def _create_paypal_donation(
    amount: float,
    currency: str,
    description: Optional[str] = None,
    return_url: Optional[str] = None,
    cancel_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a PayPal order for a donation.
    
    This is a provider-specific implementation. Other providers (Stripe, etc.)
    would have similar functions.
    
    Args:
        amount: Donation amount
        currency: Currency code (e.g., "USD")
        description: Optional donation description
        return_url: Optional return URL after approval
        cancel_url: Optional cancel URL
        
    Returns:
        dict: PayPal order response with order_id, status, approval_url, etc.
        
    Raises:
        PayPalClientError: If PayPal API call fails
    """
    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": currency.upper(),
                    "value": f"{amount:.2f}"
                }
            }
        ]
    }
    
    if description:
        order_data["purchase_units"][0]["description"] = description
    
    if return_url or cancel_url:
        order_data["application_context"] = {}
        if return_url:
            order_data["application_context"]["return_url"] = return_url
        if cancel_url:
            order_data["application_context"]["cancel_url"] = cancel_url
    
    # Call PayPal API to create order
    response = _make_paypal_request("POST", "/v2/checkout/orders", data=order_data)
    
    return response


def _capture_paypal_donation(order_id: str) -> Dict[str, Any]:
    """
    Capture a PayPal order after approval.
    
    Args:
        order_id: PayPal order ID to capture
        
    Returns:
        dict: PayPal capture response with transaction details
        
    Raises:
        PayPalClientError: If PayPal API call fails
    """
    response = _make_paypal_request(
        "POST",
        f"/v2/checkout/orders/{order_id}/capture",
        data={}
    )
    
    return response


def _get_provider_for_donation(donation_record: Dict[str, Any]) -> str:
    """
    Get the payment provider type for a donation record.
    
    Args:
        donation_record: Donation record dict
        
    Returns:
        str: Provider type (e.g., "paypal")
    """
    return donation_record.get("provider", "paypal")


@donation_bp.route("/create", methods=["POST"])
def create_donation():
    """
    Create a new donation and initiate payment processing.
    
    Request body (JSON):
    {
        "amount": 25.00,                    # Required: donation amount
        "currency": "USD",                  # Optional: currency code (default: "USD")
        "donor_name": "John Doe",            # Optional: donor name
        "donor_email": "john@example.com",  # Optional: donor email
        "client_id": "optional",            # Optional: client/site identifier
        "description": "Donation",          # Optional: donation description
        "return_url": "https://...",        # Optional: return URL after approval
        "cancel_url": "https://..."         # Optional: cancel URL
    }
    
    Returns:
        JSON response with donation reference ID and provider-specific data:
        {
            "donation_id": "don_abc123...",
            "provider": "paypal",
            "provider_data": {
                "order_id": "5O190127TN364715T",
                "status": "CREATED",
                "approval_url": "https://..."
            }
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
    
    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return jsonify({"error": "amount must be greater than 0"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "amount must be a valid number"}), 400
    
    # Generate unique donation reference ID
    donation_id = _generate_donation_id()
    
    # Extract optional metadata
    donor_name = data.get("donor_name")
    donor_email = data.get("donor_email")
    client_id = data.get("client_id")
    description = data.get("description", f"Donation of {currency} {amount_float:.2f}")
    return_url = data.get("return_url")
    cancel_url = data.get("cancel_url")
    
    # Create donation record (status: pending)
    donation_record = {
        "donation_id": donation_id,
        "amount": amount_float,
        "currency": currency.upper(),
        "status": "pending",
        "provider": "paypal",  # TODO: Make provider configurable (e.g., from client settings)
        "created_at": datetime.utcnow().isoformat(),
        "donor_name": donor_name,
        "donor_email": donor_email,
        "client_id": client_id,
        "description": description,
        "provider_order_id": None,
        "provider_data": None,
        "confirmed_at": None,
        "transaction_id": None
    }
    
    try:
        # Create payment order with provider (currently PayPal)
        # TODO: Add support for other providers (Stripe, etc.) via provider factory
        provider_response = _create_paypal_donation(
            amount=amount_float,
            currency=currency,
            description=description,
            return_url=return_url,
            cancel_url=cancel_url
        )
        
        # Extract provider-specific data
        order_id = provider_response.get("id")
        status = provider_response.get("status")
        links = provider_response.get("links", [])
        
        # Find approval link
        approval_url = None
        for link in links:
            if link.get("rel") == "approve":
                approval_url = link.get("href")
                break
        
        # Update donation record with provider data
        donation_record["provider_order_id"] = order_id
        donation_record["provider_data"] = provider_response
        
        # Store donation record
        # TODO: Persist to database instead of in-memory store
        _donations_store[donation_id] = donation_record
        
        # Prepare response
        result = {
            "donation_id": donation_id,
            "provider": "paypal",
            "provider_data": {
                "order_id": order_id,
                "status": status,
                "approval_url": approval_url,
                "links": links
            }
        }
        
        logger.info(f"Donation created: {donation_id}, amount: {currency} {amount_float:.2f}, client: {client_id}")
        
        return jsonify(result), 201
        
    except PayPalClientError as exc:
        logger.error(f"Donation creation failed (PayPal error): {exc}")
        return jsonify({"error": f"Payment provider error: {str(exc)}"}), 502
    
    except Exception as exc:
        logger.error(f"Unexpected error creating donation: {exc}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@donation_bp.route("/confirm", methods=["POST"])
def confirm_donation():
    """
    Confirm a donation after payment approval.
    
    Request body (JSON):
    {
        "donation_id": "don_abc123...",     # Required: internal donation reference ID
        "provider_order_id": "5O190127..."  # Optional: provider order ID (for verification)
    }
    
    Returns:
        JSON response indicating success/failure:
        {
            "donation_id": "don_abc123...",
            "status": "completed",
            "transaction_id": "...",
            "amount": {...},
            "confirmed_at": "2024-01-01T12:00:00"
        }
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    donation_id = data.get("donation_id")
    if not donation_id:
        return jsonify({"error": "donation_id is required"}), 400
    
    # Retrieve donation record
    # TODO: Query from database instead of in-memory store
    donation_record = _donations_store.get(donation_id)
    if not donation_record:
        return jsonify({"error": "donation not found"}), 404
    
    # Check for terminal states - prevent retrying captures
    current_status = donation_record.get("status")
    if current_status == "completed":
        return jsonify({
            "donation_id": donation_id,
            "status": "completed",
            "message": "Donation already confirmed",
            "transaction_id": donation_record.get("transaction_id"),
            "confirmed_at": donation_record.get("confirmed_at")
        }), 200
    
    if current_status == "failed":
        return jsonify({
            "donation_id": donation_id,
            "status": "failed",
            "error": "Donation capture previously failed. Cannot retry capture for failed donations.",
            "transaction_id": donation_record.get("transaction_id"),
            "confirmed_at": donation_record.get("confirmed_at")
        }), 409  # 409 Conflict - resource is in a state that prevents the operation
    
    # Verify provider order ID if provided
    provider_order_id = data.get("provider_order_id")
    stored_order_id = donation_record.get("provider_order_id")
    if provider_order_id and provider_order_id != stored_order_id:
        return jsonify({"error": "provider_order_id mismatch"}), 400
    
    # Use stored order ID if not provided
    if not provider_order_id:
        provider_order_id = stored_order_id
    
    if not provider_order_id:
        return jsonify({"error": "provider_order_id is required"}), 400
    
    try:
        # Get provider type
        provider = _get_provider_for_donation(donation_record)
        
        # Capture payment with provider
        # TODO: Add support for other providers via provider factory
        if provider == "paypal":
            capture_response = _capture_paypal_donation(provider_order_id)
        else:
            return jsonify({"error": f"Unsupported provider: {provider}"}), 400
        
        # Extract transaction details
        status = capture_response.get("status")
        purchase_units = capture_response.get("purchase_units", [])
        transaction_id = None
        amount_info = None
        
        if purchase_units:
            payments = purchase_units[0].get("payments", {})
            captures = payments.get("captures", [])
            if captures:
                transaction_id = captures[0].get("id")
                amount_info = captures[0].get("amount")
        
        # Update donation record
        donation_record["status"] = "completed" if status == "COMPLETED" else "failed"
        donation_record["transaction_id"] = transaction_id
        donation_record["confirmed_at"] = datetime.utcnow().isoformat()
        donation_record["provider_data"] = capture_response
        
        # Store updated record
        # TODO: Persist to database
        _donations_store[donation_id] = donation_record
        
        # Prepare response
        result = {
            "donation_id": donation_id,
            "status": donation_record["status"],
            "transaction_id": transaction_id,
            "amount": amount_info,
            "confirmed_at": donation_record["confirmed_at"]
        }
        
        logger.info(f"Donation confirmed: {donation_id}, transaction_id: {transaction_id}")
        
        return jsonify(result), 200
        
    except PayPalClientError as exc:
        logger.error(f"Donation confirmation failed (PayPal error): {exc}")
        return jsonify({"error": f"Payment provider error: {str(exc)}"}), 502
    
    except Exception as exc:
        logger.error(f"Unexpected error confirming donation: {exc}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@donation_bp.route("/status/<donation_id>", methods=["GET"])
def get_donation_status(donation_id: str):
    """
    Get the status of a donation.
    
    URL parameter:
        donation_id: Internal donation reference ID
        
    Returns:
        JSON response with donation status and details:
        {
            "donation_id": "don_abc123...",
            "status": "pending" | "completed" | "failed",
            "amount": 25.00,
            "currency": "USD",
            "created_at": "2024-01-01T12:00:00",
            "confirmed_at": null | "2024-01-01T12:05:00",
            "transaction_id": null | "..."
        }
    """
    # Retrieve donation record
    # TODO: Query from database instead of in-memory store
    donation_record = _donations_store.get(donation_id)
    if not donation_record:
        return jsonify({"error": "donation not found"}), 404
    
    # Return sanitized donation info (exclude sensitive provider data)
    result = {
        "donation_id": donation_record["donation_id"],
        "status": donation_record["status"],
        "amount": donation_record["amount"],
        "currency": donation_record["currency"],
        "created_at": donation_record["created_at"],
        "confirmed_at": donation_record.get("confirmed_at"),
        "transaction_id": donation_record.get("transaction_id"),
        "provider": donation_record.get("provider")
    }
    
    return jsonify(result), 200
