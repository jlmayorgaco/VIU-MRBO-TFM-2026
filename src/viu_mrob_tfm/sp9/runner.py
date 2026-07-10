"""Runtime availability checks for SP9.

The actual CoppeliaSim campaign requires an external simulator.  This module
keeps the check explicit so the thesis can distinguish prepared integration
from executed evidence.
"""

from __future__ import annotations

import shutil
from pathlib import Path


COPPELIA_COMMANDS = ("coppeliaSim", "CoppeliaSim", "coppeliaSim.exe", "CoppeliaSim.exe")


def find_coppeliasim() -> str | None:
    """Return an executable path/name if CoppeliaSim is available."""

    for command in COPPELIA_COMMANDS:
        found = shutil.which(command)
        if found:
            return found
    return None


def required_scene_files(scene_dir: Path, scenarios: list[str]) -> list[Path]:
    """Return expected YAML/Lua scene files for each named SP9 scenario."""

    files: list[Path] = []
    for scenario in scenarios:
        base = scene_dir / f"{scenario}_smith_qr"
        files.extend([base.with_suffix(".yaml"), base.with_suffix(".lua")])
    return files
