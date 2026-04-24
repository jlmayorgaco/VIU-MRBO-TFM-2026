"""Registry helpers for named experiment configurations."""

from __future__ import annotations

from pathlib import Path


def build_experiment_registry(root: Path | None = None) -> dict[str, Path]:
    """Return a map from experiment folder names to config files."""

    base_path = Path("experiments") if root is None else root
    return {
        directory.name: directory / "config.yaml"
        for directory in sorted(base_path.glob("exp-*"))
        if directory.is_dir() and (directory / "config.yaml").exists()
    }
