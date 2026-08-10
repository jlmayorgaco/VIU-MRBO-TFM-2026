"""Run the versioned SP1-GEO benchmark with checkpoint/resume support."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from viu_mrob_tfm.sp1_geo.runner import main


if __name__ == "__main__":
    raise SystemExit(main())
