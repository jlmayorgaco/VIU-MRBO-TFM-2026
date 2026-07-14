"""Single auditable command for the CPU-only physical-coalition campaign."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from viu_mrob_tfm.physical_coalition.runner import (
    analyze_campaign,
    extend_by_precision,
    finalize_manifest,
    freeze_protocol,
    prepare_protocol,
    render_figures,
    run_dry_run,
    run_official,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m experiments.physical_coalition")
    sub = parser.add_subparsers(dest="command", required=True)
    full = sub.add_parser("run-full")
    full.add_argument("--config", required=True, type=Path)
    full.add_argument("--prepare", action="store_true")
    full.add_argument("--dry-run", action="store_true")
    full.add_argument("--freeze", action="store_true")
    full.add_argument("--run", action="store_true")
    full.add_argument("--extend-by-precision", action="store_true")
    full.add_argument("--analyze", action="store_true")
    full.add_argument("--render", action="store_true")
    full.add_argument("--resume", action="store_true")
    full.add_argument("--workers", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    args = build_parser().parse_args(argv)
    results: dict[str, object] = {}
    if args.prepare:
        results["prepare"] = prepare_protocol(args.config)
    if args.dry_run:
        results["dry_run"] = run_dry_run(args.config)
        if not results["dry_run"]["passed"]:
            print(json.dumps(results, indent=2, sort_keys=True))
            return 2
    if args.freeze:
        results["freeze"] = freeze_protocol(args.config)
    if args.run:
        results["run"] = run_official(args.config, workers=args.workers, resume=args.resume)
        if results["run"]["status"] != "base_complete":
            print(json.dumps(results, indent=2, sort_keys=True))
            return 3
    if args.extend_by_precision:
        results["extension"] = extend_by_precision(args.config, workers=args.workers)
    if args.analyze:
        results["analysis"] = analyze_campaign(args.config)
    if args.render:
        results["figures"] = render_figures(args.config)
    if args.run and args.extend_by_precision and args.analyze and args.render:
        results["final"] = finalize_manifest(args.config)
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if not results.get("final") or results["final"]["status"] == "campaign_closed" else 4


if __name__ == "__main__":
    raise SystemExit(main())