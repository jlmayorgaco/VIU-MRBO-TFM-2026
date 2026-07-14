"""Run one lifecycle step of a physical-coalition certificate protocol."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

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


Step = Callable[..., dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument(
        "step",
        choices=(
            "prepare",
            "dry-run",
            "freeze",
            "run",
            "sampling",
            "analyze",
            "figures",
            "finalize",
            "close",
        ),
    )
    parser.add_argument("--workers", type=int, default=None)
    return parser.parse_args()


def invoke(step: str, config: Path, workers: int | None) -> dict[str, Any]:
    simple_steps: dict[str, Step] = {
        "prepare": prepare_protocol,
        "dry-run": run_dry_run,
        "freeze": freeze_protocol,
        "analyze": analyze_campaign,
        "figures": render_figures,
        "finalize": finalize_manifest,
    }
    if step in simple_steps:
        return simple_steps[step](config)
    if step == "run":
        return run_official(config, workers=workers, resume=True)
    if step == "sampling":
        return extend_by_precision(config, workers=workers)
    if step == "close":
        outputs: dict[str, Any] = {}
        outputs["sampling"] = extend_by_precision(config, workers=workers)
        outputs["analyze"] = analyze_campaign(config)
        outputs["figures"] = render_figures(config)
        outputs["finalize"] = finalize_manifest(config)
        return outputs
    raise ValueError(f"unsupported lifecycle step: {step}")


def main() -> None:
    args = parse_args()
    result = invoke(args.step, args.config, args.workers)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
