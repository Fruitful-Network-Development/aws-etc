# /srv/webapps/platform/modules/donation_receipts.py

"""
Blueprint for storing and retrieving donation receipts as JSON files per client.

Registration example in app.py::

    from modules.donation_receipts import donation_receipts_bp
    app.register_blueprint(donation_receipts_bp)

Endpoints
---------
- GET  /api/donation-receipts
    Query params:
      - filename (optional): override the target JSON filename (defaults to
        "donation_receipts.json"). ".json" is appended automatically if omitted.
    Returns an array of stored receipts (empty array when file is absent).

- POST /api/donation-receipts
    JSON body:
    {
        "amount": 120.50,                  # required, number > 0
        "currency": "USD",                 # optional (defaults to USD)
        "donor": {                         # donor info (structure is flexible)
            "name": "Jane Doe",
            "email": "jane@example.com",
            "address": "123 Main St"
        },
        "designation": "Annual Fund",      # optional
        "provider": "paypal",              # optional
        "provider_metadata": {...},        # optional provider-specific fields
        "no_goods_or_services_statement": "No goods or services...",  # optional
        "ein": "00-0000000"                # optional placeholder EIN
    }

    Appends the receipt to the client-scoped JSON file.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

from data_access import (
    get_client_paths,
    get_client_slug,
    load_client_manifest,
    load_json,
    resolve_backend_data_path,
    save_json,
)

logger = logging.getLogger(__name__)

donation_receipts_bp = Blueprint(
    "donation_receipts", __name__, url_prefix="/api/donation-receipts"
)

DEFAULT_FILENAME = "donation_receipts.json"


def _normalize_filename(raw: str | None) -> str:
    """Ensure we only work with a filename (no directories) and a .json suffix."""
    if not raw:
        return DEFAULT_FILENAME

    clean = Path(raw).name
    if not clean.lower().endswith(".json"):
        clean = f"{clean}.json"
    return clean


def _resolve_receipts_path(client_slug: str, filename: str) -> Path:
    """Resolve the target receipts JSON path, preferring manifest-backed entries."""
    paths = get_client_paths(client_slug)
    cleaned_name = _normalize_filename(filename)

    try:
        manifest = load_client_manifest(paths)
        return resolve_backend_data_path(paths, manifest, cleaned_name)
    except Exception as exc:
        # Fall back to a strict data_dir resolution when manifest validation fails
        if not isinstance(exc, (FileNotFoundError, ValueError)):
            logger.debug("Unexpected manifest error, using data_dir fallback", exc_info=True)

    data_dir = paths["data_dir"].resolve()
    target = (data_dir / cleaned_name).resolve()
    try:
        target.relative_to(data_dir)
    except ValueError:
        raise ValueError("Receipt filename escapes the client data directory")
    return target


def _load_receipts(path: Path) -> List[Dict[str, Any]]:
    """Load receipt list or return an empty list if the file does not exist."""
    if not path.exists():
        return []

    payload = load_json(path)
    if not isinstance(payload, list):
        raise ValueError("Receipts file must contain a JSON array")
    return payload


@donation_receipts_bp.route("", methods=["GET"])
def get_donation_receipts():
    """Fetch stored donation receipts for the current client."""
    client_slug = get_client_slug(request)
    filename = request.args.get("filename")

    try:
        target_path = _resolve_receipts_path(client_slug, filename)
        receipts = _load_receipts(target_path)
    except ValueError as exc:
        return jsonify({"error": "invalid_receipts_file", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive logging for unexpected issues
        logger.error("Failed to load donation receipts", exc_info=True)
        return (
            jsonify({"error": "server_error", "message": "Could not load receipts"}),
            500,
        )

    return jsonify({"receipts": receipts, "source": target_path.name})


def _coerce_amount(raw: Any) -> float:
    """Validate amount is a positive number."""
    amount = float(raw)
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    return amount


@donation_receipts_bp.route("", methods=["POST"])
def save_donation_receipt():
    """Persist a donation receipt for the current client."""
    client_slug = get_client_slug(request)
    filename = request.args.get("filename")

    try:
        target_path = _resolve_receipts_path(client_slug, filename)
    except ValueError as exc:
        return jsonify({"error": "invalid_receipts_file", "message": str(exc)}), 400

    if not request.is_json:
        return jsonify({"error": "invalid_json", "message": "Request must be JSON"}), 400

    try:
        payload = request.get_json()
    except Exception:
        return jsonify({"error": "invalid_json", "message": "Request body could not be parsed as JSON"}), 400

    if not payload:
        return jsonify({"error": "invalid_json", "message": "Request body is required"}), 400

    try:
        amount = _coerce_amount(payload.get("amount"))
    except Exception:
        return jsonify({"error": "invalid_amount", "message": "amount is required and must be a number greater than zero"}), 400

    donor_info = payload.get("donor") or {}
    if donor_info and not isinstance(donor_info, dict):
        return jsonify({"error": "invalid_donor", "message": "donor must be an object with donor details"}), 400

    receipt = {
        "amount": amount,
        "currency": payload.get("currency", "USD"),
        "donor": donor_info,
        "designation": payload.get("designation"),
        "provider": payload.get("provider"),
        "provider_metadata": payload.get("provider_metadata") or payload.get("provider_meta"),
        "no_goods_or_services_statement": payload.get(
            "no_goods_or_services_statement",
            payload.get("no_goods_or_services"),
        ),
        "ein": payload.get("ein") or payload.get("ein_placeholder"),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        receipts = _load_receipts(target_path)
    except ValueError as exc:
        return jsonify({"error": "invalid_receipts_file", "message": str(exc)}), 400
    except Exception:
        logger.error("Failed reading existing receipts", exc_info=True)
        return (
            jsonify({"error": "server_error", "message": "Could not read existing receipts"}),
            500,
        )

    receipts.append(receipt)

    try:
        save_json(target_path, receipts)
    except Exception:
        logger.error("Failed writing receipts file", exc_info=True)
        return (
            jsonify({"error": "server_error", "message": "Could not save receipt"}),
            500,
        )

    return jsonify({"status": "saved", "receipt": receipt, "source": target_path.name}), 201
