"""CLI for the preregistered supported-load Cargo campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from viu_mrob_tfm.coppelia_cargo import build_run_specs, load_config, run_campaign_file
from viu_mrob_tfm.coppelia_cargo.design import design_hash


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run or inspect the paired Cargo protocol. Deterministic outputs are "
            "software-contract tests, never CoppeliaSim evidence."
        )
    )
    parser.add_argument("--config", required=True, type=Path, help="campaign YAML")
    parser.add_argument("--output-dir", type=Path, help="new output directory")
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and print the immutable design only"
    )
    parser.add_argument(
        "--authorize-confirmatory",
        action="store_true",
        help="explicitly authorize the real confirmatory campaign (also requires --preflight-evidence)",
    )
    parser.add_argument(
        "--preflight-evidence",
        type=Path,
        help=(
            "approved, hash-bound physical preflight directory required for "
            "confirmatory execution"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    runs = build_run_specs(config)
    if args.dry_run:
        primary = sum(run.phase == "primary" for run in runs)
        sensitivity = len(runs) - primary
        print(
            json.dumps(
                {
                    "experiment_id": config.experiment_id,
                    "mode": config.mode,
                    "backend_kind": config.backend.kind,
                    "evidence_class": (
                        "synthetic_contract_test_only"
                        if config.backend.kind == "deterministic_contract"
                        else "physical_coppeliasim_candidate"
                    ),
                    "factorial_cells": config.design.cell_count,
                    "coalition_sizes": {
                        name: len(config.design.coalitions_m[name])
                        for name in config.design.coalition
                    },
                    "longitudinal_acceleration_m_s2": list(
                        config.design.longitudinal_acceleration_m_s2
                    ),
                    "paired_seeds": config.design.seeds.count,
                    "primary_runs": primary,
                    "dt_sensitivity_runs": sensitivity,
                    "design_sha256": design_hash(runs),
                    "inference": {
                        "confidence_level": config.inference.confidence_level,
                        "test": "exact two-sided McNemar",
                        "multiplicity": "Holm within cell and endpoint",
                    },
                    "confirmatory_execution_requires": [
                        "--authorize-confirmatory",
                        "--preflight-evidence DIR",
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    result = run_campaign_file(
        args.config,
        output_dir=args.output_dir,
        authorize_confirmatory=args.authorize_confirmatory,
        preflight_evidence=args.preflight_evidence,
    )
    print(
        json.dumps(
            {
                "output_dir": str(result.output_dir),
                "runs": result.run_count,
                "completed": result.completed_count,
                "failed": result.failed_count,
                "manifest": str(result.manifest_path),
            },
            indent=2,
        )
    )
    return 0 if result.failed_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
