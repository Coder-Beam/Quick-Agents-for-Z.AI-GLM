"""Utility functions."""

import json
from pathlib import Path


def read_json(path: Path) -> dict:
    """Read JSON file."""
    with open(path) as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    """Write JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
