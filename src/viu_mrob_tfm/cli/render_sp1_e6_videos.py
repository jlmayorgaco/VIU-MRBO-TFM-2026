"""Render audited top-down MP4 videos from a completed SP1 E6 campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from viu_mrob_tfm.sp1_canonical.validation.visualization import render_e6_videos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("results/sp1_validation/SP1_CONFERENCE_VALIDATION_v1"),
    )
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--dpi", type=int, default=110)
    parser.add_argument("--playback-duration-s", type=float, default=18.0)
    arguments = parser.parse_args()
    manifest = render_e6_videos(
        arguments.run_dir,
        fps=arguments.fps,
        dpi=arguments.dpi,
        playback_duration_s=arguments.playback_duration_s,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
