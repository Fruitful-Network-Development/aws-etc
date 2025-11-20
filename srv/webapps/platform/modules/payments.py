# /srv/webapps/platform/modules/payments.py

from pathlib import Path
from typing import Dict


def create_order(request, client_slug: str, paths: Dict[str, Path]) -> dict:
    """
    Placeholder for PayPal integration.
    Here you'd:
      - load client-specific PayPal config from paths['config_dir']/paypal.json
      - call PayPal API to create an order
      - return an approval link or order ID
    """
    # Example skeleton:
    config_path = paths["config_dir"] / "paypal.json"
    # TODO: read config and call PayPal APIs
    return {
        "status": "placeholder",
        "message": "PayPal order creation not yet implemented",
        "client": client_slug,
        "config_file": str(config_path),
    }

