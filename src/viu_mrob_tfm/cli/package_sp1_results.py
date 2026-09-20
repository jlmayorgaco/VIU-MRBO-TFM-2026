"""CLI for the hash-verified complete SP1 result index."""

from __future__ import annotations

import argparse
import json

from viu_mrob_tfm.sp1_canonical.validation.result_package import (
    build_sp1_result_package,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Package the current canonical SP1 results")
    parser.add_argument(
        "--canonical-dir",
        default="results/sp1_canonical/SP1_CANONICAL_CONFIRMATORY_v1",
    )
    parser.add_argument(
        "--conference-dir",
        default="results/sp1_validation/SP1_CONFERENCE_VALIDATION_v1",
    )
    parser.add_argument(
        "--output-dir",
        default="results/sp1_full/SP1_COMPLETE_RESULTS_v1",
    )
    arguments = parser.parse_args()
    manifest = build_sp1_result_package(
        arguments.canonical_dir,
        arguments.conference_dir,
        arguments.output_dir,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
