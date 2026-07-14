"""CLI for the SP0 protocol audit and guarded campaign runner."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from viu_mrob_tfm.sp0.audit import run_full, validate_b0


def _set_thread_env() -> None:
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m experiments.sp0")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-b0", help="Validate SP0 B0 gates G1-G7 and smoke suite.")
    validate.add_argument("--config", required=True)

    full = sub.add_parser("run-full", help="Guarded SP0 full campaign command.")
    full.add_argument("--config", required=True)
    full.add_argument("--validate-b0", action="store_true")
    full.add_argument("--repair-and-validate-b0", action="store_true")
    full.add_argument("--train-data-driven", action="store_true")
    full.add_argument("--freeze", action="store_true")
    full.add_argument("--run-b1-b7", action="store_true")
    full.add_argument("--extend-by-precision", action="store_true")
    full.add_argument("--analyze", action="store_true")
    full.add_argument("--render-figures", action="store_true")
    full.add_argument("--render-videos", action="store_true")
    full.add_argument("--resume", action="store_true")
    full.add_argument("--block", default=None)
    full.add_argument("--dry-run", action="store_true")
    full.add_argument("--workers", type=int, default=1)
    full.add_argument("--device", default="auto")
    full.add_argument("--allow-long-cpu-training", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    _set_thread_env()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate-b0":
        manifest = validate_b0(Path(args.config))
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0 if manifest.get("passed") else 1
    if args.command == "run-full":
        os.environ["SP0_WORKERS"] = str(args.workers)
        manifest = run_full(
            Path(args.config),
            validate=bool(args.validate_b0 or args.repair_and_validate_b0),
            freeze=bool(args.freeze),
            run_b1_b7=bool(args.run_b1_b7),
            analyze=bool(args.analyze),
            render_figures=bool(args.render_figures),
            render_videos=bool(args.render_videos),
            dry_run=bool(args.dry_run),
            train_data_driven=bool(args.train_data_driven),
            device=str(args.device),
            allow_long_cpu_training=bool(args.allow_long_cpu_training),
            extend_by_precision=bool(args.extend_by_precision),
            resume=bool(args.resume),
            block=args.block,
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        if str(manifest.get("status", "")).startswith("blocked"):
            return 3
        if manifest.get("status") == "incomplete_acceptance":
            return 4
        campaign = manifest.get("campaign", {})
        if campaign.get("status") == "blocked_before_confirmatory_seed_opening":
            return 2
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
