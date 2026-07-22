"""Run the complete SP1 validation stack in one reproducible command.

The canonical SP1 campaign (role/contact formation) and the E0--E6
resource-population validation battery intentionally keep separate output
directories and manifests.  This runner orchestrates both campaigns and
creates a small top-level manifest that records their status and hashes.  It
does not merge raw data, so each campaign remains independently auditable.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from viu_mrob_tfm.sp1_canonical.experiment import run_sp1_config
from viu_mrob_tfm.sp1_canonical.validation.experiment import run_validation_config


def run_sp1_full(
    canonical_config: str | Path,
    validation_config: str | Path,
    *,
    experiment: str = "all",
    canonical_smoke: bool = False,
    output_dir: str | Path | None = None,
    skip_canonical: bool = False,
    skip_validation: bool = False,
) -> dict[str, Any]:
    """Execute canonical SP1 and/or E0--E6 validation and write a bundle.

    Parameters are explicit so a confirmatory run cannot accidentally reuse a
    smoke configuration. ``experiment`` is passed to the E0--E6 runner and may
    be one of ``all`` or ``e0``--``e6``. At least one campaign must be enabled.
    The returned dictionary is also written as ``manifest.json`` in
    ``output_dir``.
    """

    if skip_canonical and skip_validation:
        raise ValueError("At least one SP1 campaign must be enabled")

    canonical_path = Path(canonical_config)
    validation_path = Path(validation_config)
    canonical_manifest: dict[str, Any] | None = None
    validation_manifest: dict[str, Any] | None = None
    if not skip_canonical:
        canonical_manifest = run_sp1_config(canonical_path, smoke=canonical_smoke)
    if not skip_validation:
        validation_manifest = run_validation_config(validation_path, experiment=experiment)

    if output_dir is None:
        validation_id = (
            str(validation_manifest.get("experiment_id"))
            if validation_manifest is not None
            else canonical_path.stem
        )
        output_path = Path("results") / "sp1_full" / validation_id
    else:
        output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    campaign_statuses = [
        manifest.get("audit_status")
        for manifest in (canonical_manifest, validation_manifest)
        if manifest is not None
    ]
    status = (
        "passed"
        if campaign_statuses and all(value == "passed" for value in campaign_statuses)
        else "failed"
    )
    scientific_statuses = [
        manifest.get("scientific_status", "unknown")
        for manifest in (canonical_manifest, validation_manifest)
        if manifest is not None
    ]
    scientific_status = (
        "passed"
        if scientific_statuses and all(value == "passed" for value in scientific_statuses)
        else "partial"
    )

    bundle: dict[str, Any] = {
        "experiment_id": "SP1_FULL",
        "canonical_sp": "SP1",
        "protocol_family": "sp1_canonical_plus_resource_population_e0_e6",
        "canonical_config": str(canonical_path),
        "validation_config": str(validation_path),
        "validation_experiment": experiment,
        "canonical_smoke": canonical_smoke,
        "audit_status": status,
        "scientific_status": scientific_status,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git_commit": _git_value(["rev-parse", "HEAD"]),
        "git_dirty": bool(_git_value(["status", "--porcelain"])),
        "output_dir": str(output_path),
        "canonical": canonical_manifest,
        "validation": validation_manifest,
    }
    manifest_path = output_path / "manifest.json"
    manifest_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")

    report = _build_report(bundle)
    (output_path / "report.md").write_text(report, encoding="utf-8")
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run canonical SP1 plus its reproducible E0--E6 validation battery."
    )
    parser.add_argument(
        "--canonical-config",
        type=Path,
        default=Path("experiments/configs/sp1_canonical_smoke.yaml"),
        help="YAML for role/contact formation (canonical SP1).",
    )
    parser.add_argument(
        "--validation-config",
        type=Path,
        default=Path("experiments/configs/sp1_validation_smoke.yaml"),
        help="YAML for E0--E6 resource validation.",
    )
    parser.add_argument(
        "--experiment",
        choices=["all", "e0", "e1", "e2", "e3", "e4", "e5", "e6"],
        default="all",
        help="Validation layer to run (canonical campaign is complete unless skipped).",
    )
    parser.add_argument(
        "--canonical-smoke",
        action="store_true",
        help="Truncate the canonical campaign to its two-world software smoke test.",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--skip-canonical", action="store_true")
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    manifest = run_sp1_full(
        args.canonical_config,
        args.validation_config,
        experiment=args.experiment,
        canonical_smoke=args.canonical_smoke,
        output_dir=args.output_dir,
        skip_canonical=args.skip_canonical,
        skip_validation=args.skip_validation,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    if manifest["audit_status"] != "passed":
        raise SystemExit(1)


def _git_value(arguments: list[str]) -> str:
    try:
        return subprocess.run(
            ["git", *arguments], check=False, capture_output=True, text=True
        ).stdout.strip()
    except OSError:
        return ""


def _build_report(bundle: dict[str, Any]) -> str:
    lines = [
        "# Validación integral de SP1",
        "",
        f"- Auditoría de software: `{bundle['audit_status']}`",
        f"- Estado científico: `{bundle['scientific_status']}`",
        f"- Capa E0--E6 solicitada: `{bundle['validation_experiment']}`",
        "",
        "Los datos y las figuras permanecen en los directorios declarados por "
        "cada configuración. Este directorio solo agrupa manifiestos y no "
        "combina muestras de campañas distintas.",
        "",
    ]
    for key, title in (("canonical", "SP1 canónico"), ("validation", "Batería E0--E6")):
        campaign = bundle.get(key)
        if campaign is None:
            continue
        lines.extend(
            [
                f"## {title}",
                "",
                f"- Experimento: `{campaign.get('experiment_id', 'n/a')}`",
                f"- Auditoría: `{campaign.get('audit_status', 'n/a')}`",
                f"- Estado científico: `{campaign.get('scientific_status', 'n/a')}`",
                f"- Manifiesto: `{campaign.get('output_dir', 'n/a')}/manifest.json`",
                "",
            ]
        )
    lines.extend(
        [
            "## Alcance",
            "",
            "`audit_status=passed` certifica invariantes y artefactos del software. "
            "No demuestra por sí solo convergencia global, optimalidad, seguridad "
            "continua, docking o transporte físico; esas afirmaciones requieren la "
            "evidencia y el nivel declarados en cada campaña.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
