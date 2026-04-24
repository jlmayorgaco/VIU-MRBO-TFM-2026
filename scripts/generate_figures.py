"""Generate placeholder summary figures from available experiment outputs."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.plotting.summary import plot_metric_summary
from viu_mrob_tfm.utils.io import ensure_directory
from viu_mrob_tfm.utils.logging import get_logger


def main() -> int:
    logger = get_logger("generate_figures")
    output_dir = ensure_directory(Path("results/figures"))
    figure = plot_metric_summary(
        {
            "tracking_error": 0.0,
            "formation_error": 0.0,
            "control_effort": 0.0,
        },
        output_path=output_dir / "placeholder-summary.png",
    )
    figure.clf()
    logger.info("Placeholder figure written to %s", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
