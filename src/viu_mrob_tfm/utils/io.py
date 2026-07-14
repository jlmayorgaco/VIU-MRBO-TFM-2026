"""Input/output helpers with pathlib-based filesystem access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
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


def coerce_nullable_dataframe_types(frame: Any) -> Any:
    """Preserve nullable booleans and numeric columns before Parquet writes."""

    import numbers
    import pandas as pd

    for column in frame.columns:
        if str(frame[column].dtype) != "object":
            continue
        values = [value for value in frame[column].tolist() if value is not None and not pd.isna(value)]
        if not values:
            continue
        if all(isinstance(value, (bool, np.bool_)) for value in values):
            frame[column] = frame[column].astype("boolean")
        elif all(isinstance(value, numbers.Integral) and not isinstance(value, (bool, np.bool_)) for value in values):
            frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
        elif all(isinstance(value, numbers.Real) and not isinstance(value, (bool, np.bool_)) for value in values):
            frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Float64")
        elif all(isinstance(value, str) for value in values):
            frame[column] = frame[column].astype("string")
        else:
            frame[column] = frame[column].map(lambda value: None if value is None else str(value)).astype("string")
    return frame