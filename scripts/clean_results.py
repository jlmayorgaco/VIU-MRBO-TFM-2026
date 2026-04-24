"""Clean generated result files while preserving the scaffold structure."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.utils.logging import get_logger


RESULT_DIRS = [
    Path("results/raw"),
    Path("results/processed"),
    Path("results/figures"),
    Path("results/tables"),
    Path("results/reports"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean all generated result directories.",
    )
    return parser.parse_args()


def _safe_clean_directory(directory: Path, repo_root: Path) -> None:
    target = (repo_root / directory).resolve()
    if repo_root not in target.parents and target != repo_root:
        msg = f"Refusing to clean path outside repository: {target}"
        raise ValueError(msg)

    for item in target.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def main() -> int:
    args = parse_args()
    logger = get_logger("clean_results")
    if not args.all:
        logger.info("Nothing to clean. Use --all to remove generated outputs.")
        return 0

    repo_root = ROOT
    for directory in RESULT_DIRS:
        _safe_clean_directory(directory, repo_root)
        logger.info("Cleaned %s", directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
