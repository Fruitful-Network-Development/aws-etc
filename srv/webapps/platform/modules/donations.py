# /srv/webapps/platform/modules/donations.py

from pathlib import Path
from typing import Dict
from ..data_access import load_json, save_json


def handle_donation(request, client_slug: str, paths: Dict[str, Path]) -> dict:
    """
    Placeholder implementation.
    In the future, you might:
      - validate payload
      - optionally talk to a payment gateway
      - append the donation record to donations.json
    """
    payload = request.get_json(force=True)

    donations_path = paths["data_dir"] / "donations.json"
    donations = load_json(donations_path, default=[])
    donations.append(payload)
    save_json(donations_path, donations)

    return {"status": "recorded", "client": client_slug}

