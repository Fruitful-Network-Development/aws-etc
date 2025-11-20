# /srv/webapps/platform/data_access.py

import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any = None) -> Any:
    """
    Safely load JSON from a file. Returns `default` if file does not exist.
    """
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    """
    Safely write JSON to a file (simple version, no locking).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

