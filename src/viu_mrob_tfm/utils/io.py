"""Input/output helpers with pathlib-based filesystem access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if it does not exist and return the resolved path."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return dict(data)


def save_json(path: str | Path, data: dict[str, Any]) -> Path:
    """Save a dictionary as JSON and return the target path."""

    target = Path(path)
    ensure_directory(target.parent)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
    return target
