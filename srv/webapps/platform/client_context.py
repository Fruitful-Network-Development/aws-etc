# /srv/webapps/platform/client_context.py

from pathlib import Path
from typing import Dict

BASE_CLIENTS_DIR = Path("/srv/webapps/clients")


def normalize_host(host_header: str) -> str:
    """
    Turn 'www.client1-example.com:80' into 'client1-example.com'
    """
    host = host_header.split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def get_client_slug(request) -> str:
    """
    Derive client slug from the Host header.
    E.g. Host: client1-example.com -> 'client1-example.com'
    """
    return normalize_host(request.host)


def get_client_paths(client_slug: str) -> Dict[str, Path]:
    """
    Return the key directories for a client (data, config, frontend).
    """
    root = BASE_CLIENTS_DIR / client_slug

    return {
        "root": root,
        "frontend_public": root / "frontend" / "public",
        "data_dir": root / "data",
        "config_dir": root / "config",
    }

