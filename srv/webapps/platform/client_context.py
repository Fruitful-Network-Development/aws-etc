"""Client detection and path utilities for multi-tenant front-end serving."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

# Base directory for all client sites
PLATFORM_ROOT = Path(__file__).resolve().parent
WEBAPPS_ROOT = PLATFORM_ROOT.parent
CLIENTS_ROOT = WEBAPPS_ROOT / "clients"

# Default client fallback when the host header doesn't match a known site.
DEFAULT_CLIENT_SLUG = os.getenv(
    "DEFAULT_CLIENT_SLUG", "fruitfulnetworkdevelopment.com"
)


def _discover_clients() -> set[str]:
    if not CLIENTS_ROOT.exists():
        return set()
    return {p.name for p in CLIENTS_ROOT.iterdir() if p.is_dir()}


KNOWN_CLIENTS = _discover_clients()


def get_client_slug(request) -> str:
    """
    Determine which client to serve based on the Host header.

    Falls back to DEFAULT_CLIENT_SLUG so local development under localhost:5000
    still resolves to a valid client.
    """

    host = (request.headers.get("X-Forwarded-Host") or request.host or "").split(":")[0]
    if host in KNOWN_CLIENTS:
        return host

    return DEFAULT_CLIENT_SLUG


def get_client_paths(client_slug: str) -> Dict[str, Path]:
    """
    Return key filesystem locations for a client.
    """

    client_root = CLIENTS_ROOT / client_slug
    config_dir = client_root / "config"
    frontend_dir = client_root / "frontend"

    return {
        "client_root": client_root,
        "config_dir": config_dir,
        "frontend_dir": frontend_dir,
    }
