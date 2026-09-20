"""Build a compact, hash-verified index for the complete canonical SP1 results."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from viu_mrob_tfm.sp1_canonical.validation.conference import (
    _e6_obstacle_retention_summary,
)


def build_sp1_result_package(
    canonical_dir: str | Path,
    conference_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Verify child campaigns and create an organized, non-duplicating package."""

    canonical = Path(canonical_dir)
    conference = Path(conference_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    canonical_manifest = _load_json(canonical / "manifest.json")
    conference_manifest = _load_json(conference / "manifest.json")
    conference_audit = _load_json(conference / "audit.json")
    video_manifest = _load_json(conference / "videos" / "manifest.json")

    child_statuses = {
        "canonical_audit": canonical_manifest.get("audit_status"),
        "conference_audit": conference_manifest.get("audit_status"),
        "video_audit": video_manifest.get("status"),
    }
    if any(status != "passed" for status in child_statuses.values()):
        raise ValueError(f"SP1 package rejected because a child audit did not pass: {child_statuses}")

    artifact_rows = []
    artifact_rows.extend(
        _verified_manifest_artifacts(
            canonical,
            canonical_manifest.get("artifact_sha256", {}),
            campaign="canonical_confirmatory",
            declared_by="canonical manifest",
        )
    )
    artifact_rows.extend(
        _verified_manifest_artifacts(
            conference,
            conference_manifest.get("artifact_sha256", {}),
            campaign="conference_validation",
            declared_by="conference manifest",
        )
    )
    for entry in video_manifest.get("videos", []):
        artifact_rows.append(
            _verified_artifact(
                conference / entry["video"],
                entry["sha256"],
                campaign="e6_videos",
                declared_by="video manifest",
            )
        )
    for path, campaign, declared_by in (
        (canonical / "manifest.json", "canonical_confirmatory", "package verifier"),
        (conference / "manifest.json", "conference_validation", "package verifier"),
        (conference / "audit.json", "conference_validation", "package verifier"),
        (conference / "videos" / "manifest.json", "e6_videos", "package verifier"),
        (conference / "videos" / "video_catalog.csv", "e6_videos", "package verifier"),
        (conference / "videos" / "VIDEO_INDEX.md", "e6_videos", "package verifier"),
    ):
        artifact_rows.append(
            _verified_artifact(path, _sha256(path), campaign=campaign, declared_by=declared_by)
        )

    artifact_index = (
        pd.DataFrame(artifact_rows)
        .drop_duplicates(subset=["path", "sha256"])
        .sort_values(["campaign", "category", "path"], kind="mergesort")
        .reset_index(drop=True)
    )
    artifact_index_path = output / "artifact_index.csv"
    artifact_index.to_csv(artifact_index_path, index=False)

    statistics = _key_statistics(canonical, conference)
    statistics_path = output / "key_statistics.csv"
    statistics.to_csv(statistics_path, index=False)

    readme = _build_readme(
        canonical,
        conference,
        output,
        canonical_manifest,
        conference_manifest,
        conference_audit,
        video_manifest,
        statistics,
        artifact_count=len(artifact_index),
    )
    readme_path = output / "README.md"
    readme_path.write_text(readme, encoding="utf-8")

    manifest = {
        "experiment_id": output.name,
        "canonical_sp": "SP1",
        "status": "passed",
        "scientific_status": conference_manifest.get("scientific_status", "partial"),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "organization_rule": "index child artifacts without duplicating raw campaign data",
        "child_statuses": child_statuses,
        "canonical": {
            "path": _display_path(canonical),
            "experiment_id": canonical_manifest.get("experiment_id"),
            "worlds": canonical_manifest.get("worlds"),
            "runs": canonical_manifest.get("runs"),
            "evidence_level": canonical_manifest.get("evidence_level"),
            "manifest_sha256": _sha256(canonical / "manifest.json"),
        },
        "conference": {
            "path": _display_path(conference),
            "experiment_id": conference_manifest.get("experiment_id"),
            "audit_status": conference_manifest.get("audit_status"),
            "scientific_status": conference_manifest.get("scientific_status"),
            "checks_passed": int(sum(bool(value) for value in conference_audit.get("checks", {}).values())),
            "checks_total": int(len(conference_audit.get("checks", {}))),
            "gates_passed": int(sum(bool(value) for value in conference_audit.get("gates", {}).values())),
            "gates_total": int(len(conference_audit.get("gates", {}))),
            "failed_gates": conference_audit.get("failed_gates", []),
            "manifest_sha256": _sha256(conference / "manifest.json"),
        },
        "videos": {
            "status": video_manifest.get("status"),
            "count": int(video_manifest.get("video_count", 0)),
            "manifest_sha256": _sha256(conference / "videos" / "manifest.json"),
        },
        "artifact_count": int(len(artifact_index)),
        "package_files": {
            "README.md": _sha256(readme_path),
            "artifact_index.csv": _sha256(artifact_index_path),
            "key_statistics.csv": _sha256(statistics_path),
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def _verified_manifest_artifacts(
    base: Path,
    declared: dict[str, str],
    *,
    campaign: str,
    declared_by: str,
) -> list[dict[str, Any]]:
    return [
        _verified_artifact(
            base / relative,
            expected,
            campaign=campaign,
            declared_by=declared_by,
        )
        for relative, expected in sorted(declared.items())
    ]


def _verified_artifact(
    path: Path,
    expected_sha256: str,
    *,
    campaign: str,
    declared_by: str,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Declared SP1 artifact is missing: {path}")
    actual = _sha256(path)
    if actual != expected_sha256:
        raise ValueError(f"SHA-256 mismatch for {path}: {actual} != {expected_sha256}")
    return {
        "campaign": campaign,
        "category": _category(path),
        "path": _display_path(path),
        "bytes": int(path.stat().st_size),
        "sha256": actual,
        "declared_by": declared_by,
        "verification": "passed",
    }


def _key_statistics(canonical: Path, conference: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    summary_path = canonical / "tables" / "sp1_canonical_summary.csv"
    if summary_path.exists():
        summary = pd.read_csv(summary_path)
        for method in (
            "local_gossip__sparse",
            "local_gossip__nominal",
            "local_gossip__dense",
            "local_no_gossip__nominal",
            "global_greedy",
            "central_milp",
        ):
            selected = summary[summary.method == method]
            if selected.empty:
                continue
            row = selected.iloc[0]
            for metric in ("started_loads", "social_value", "optimality_gap", "messages"):
                rows.append(
                    _stat_row(
                        "canonical_confirmatory",
                        method,
                        metric,
                        row.get(f"{metric}_mean"),
                        row.get(f"{metric}_ci_low"),
                        row.get(f"{metric}_ci_high"),
                        row.get("n"),
                        "bootstrap 95% CI; paired worlds",
                    )
                )

    contrasts_path = canonical / "tables" / "sp1_canonical_contrasts.csv"
    if contrasts_path.exists():
        contrasts = pd.read_csv(contrasts_path)
        for contrast in contrasts.itertuples(index=False):
            rows.append(
                _stat_row(
                    "canonical_confirmatory",
                    str(contrast.id),
                    str(contrast.metric) + "_paired_effect",
                    contrast.effect_a_minus_b,
                    contrast.ci95_low,
                    contrast.ci95_high,
                    contrast.n_pairs,
                    str(contrast.analysis_status),
                )
            )

    raw = conference / "raw"
    e1_path = raw / "e1_runs.csv"
    if e1_path.exists():
        e1 = pd.read_csv(e1_path, low_memory=False)
        population = e1[e1.method.str.startswith("Rep")]
        rows.extend(
            [
                _stat_row("conference_validation", "E1", "population_convergence_rate", population.converged.astype(bool).mean(), None, None, len(population), "frozen gate >=0.95"),
                _stat_row("conference_validation", "E1", "strict_lp_comparability_rate", population.comparable_to_lp.astype(bool).mean(), None, None, len(population), "frozen gate >=0.90"),
            ]
        )
    e4_path = raw / "e4_runs.csv"
    if e4_path.exists():
        e4 = pd.read_csv(e4_path, low_memory=False)
        full = e4[e4.method == "Argmax+repair+prune+local-exchange"]
        gaps = full.loc[full.feasible.astype(bool), "integer_gap_milp"].dropna()
        rows.extend(
            [
                _stat_row("conference_validation", "E4", "full_recovery_feasibility", full.feasible.astype(bool).mean(), None, None, len(full), "frozen gate >=0.95"),
                _stat_row("conference_validation", "E4", "certified_gap_median_percent", gaps.median(), None, None, len(gaps), "conditional on feasible certified cases"),
                _stat_row("conference_validation", "E4", "certified_gap_p95_percent", gaps.quantile(0.95), None, None, len(gaps), "conditional on feasible certified cases"),
            ]
        )
    e5_path = raw / "e5_runs.csv"
    if e5_path.exists():
        e5 = pd.read_csv(e5_path, low_memory=False)
        for method in ("Auction-D", "Rep-D+recovery"):
            selected = e5[e5.method == method]
            rows.append(
                _stat_row("conference_validation", "E5", f"{method}_feasibility", selected.feasible.astype(bool).mean(), None, None, len(selected), "all configured sizes")
            )
    e6_path = raw / "e6_runs.csv"
    if e6_path.exists():
        e6 = pd.read_csv(e6_path, low_memory=False)
        valid = e6[e6.assignment_feasible.astype(bool)]
        rows.append(
            _stat_row("conference_validation", "E6", "arrival_rate", valid.arrival_rate.mean(), None, None, len(valid), "approach only; no docking or transport")
        )
        for obstacle in _e6_obstacle_retention_summary(e6).itertuples(index=False):
            rows.append(
                _stat_row(
                    "conference_validation",
                    f"E6-warehouse-N{int(obstacle.n_robots)}",
                    "cases_with_retained_obstacles_rate",
                    obstacle.nonempty_cases / max(obstacle.cases, 1),
                    None,
                    None,
                    obstacle.cases,
                    f"max retained rectangles={int(obstacle.max_obstacles)}",
                )
            )
    return pd.DataFrame(rows)


def _stat_row(
    campaign: str,
    comparison: str,
    metric: str,
    estimate: Any,
    ci95_low: Any,
    ci95_high: Any,
    n: Any,
    interpretation: str,
) -> dict[str, Any]:
    return {
        "campaign": campaign,
        "comparison": comparison,
        "metric": metric,
        "estimate": estimate,
        "ci95_low": ci95_low,
        "ci95_high": ci95_high,
        "n": n,
        "interpretation": interpretation,
    }


def _build_readme(
    canonical: Path,
    conference: Path,
    output: Path,
    canonical_manifest: dict[str, Any],
    conference_manifest: dict[str, Any],
    conference_audit: dict[str, Any],
    video_manifest: dict[str, Any],
    statistics: pd.DataFrame,
    *,
    artifact_count: int,
) -> str:
    checks = conference_audit.get("checks", {})
    gates = conference_audit.get("gates", {})
    e1_conv = _estimate(statistics, "population_convergence_rate")
    e1_comp = _estimate(statistics, "strict_lp_comparability_rate")
    e4_feasible = _estimate(statistics, "full_recovery_feasibility")
    e4_gap = _estimate(statistics, "certified_gap_median_percent")
    e4_p95 = _estimate(statistics, "certified_gap_p95_percent")
    e6_arrival = _estimate(statistics, "arrival_rate")
    video_lines = []
    for video in video_manifest.get("videos", []):
        relative = Path(video["video"])
        link = _relative_link(conference / relative, output)
        video_lines.append(
            f"| {video['scenario']} | {video['n_robots']} | {video['seed']} | "
            f"{video.get('retained_obstacles', 0)} | {video['frame_count']} | [{relative.name}]({link}) |"
        )
    failed = ", ".join(f"`{gate}`" for gate in conference_audit.get("failed_gates", []))
    canonical_link = _relative_link(canonical / "report.md", output)
    conference_link = _relative_link(conference / "report.md", output)
    figures_link = _relative_link(conference / "figures", output)
    tables_link = _relative_link(conference / "tables", output)
    return "\n".join(
        [
            "# Resultados completos de SP1",
            "",
            "Este índice reúne las dos campañas vigentes del SP1 canónico sin copiar sus datos crudos. Los identificadores históricos `sp0`–`sp3` no se mezclan aquí: se conservan únicamente para reproducibilidad según `docs/02_RESEARCH_MATRIX.md`.",
            "",
            "## Estado de la entrega",
            "",
            f"- Campaña canónica: `{canonical_manifest.get('experiment_id')}`, {canonical_manifest.get('worlds')} mundos, {canonical_manifest.get('runs')} ejecuciones, auditoría `passed`, nivel `{canonical_manifest.get('evidence_level')}`.",
            f"- Validación P0/E0–E6: `{conference_manifest.get('experiment_id')}`, auditoría `passed`, estado científico `{conference_manifest.get('scientific_status')}`.",
            f"- Integridad: {sum(bool(value) for value in checks.values())}/{len(checks)} checks y {sum(bool(value) for value in gates.values())}/{len(gates)} gates aprobados; {artifact_count} artefactos verificados por SHA-256.",
            f"- Puertas científicas pendientes: {failed or 'ninguna'}.",
            "",
            "## Resultados clave",
            "",
            f"- E1: convergencia fraccionaria {e1_conv:.3f} y comparabilidad LP estricta {e1_comp:.3f}.",
            f"- E4: factibilidad del cierre completo {e4_feasible:.3f}; gap certificado mediano {e4_gap:.3f}% y p95 {e4_p95:.3f}% entre casos comparables.",
            f"- E5 alcanzó N=500; las tasas y costes completos están en `key_statistics.csv` y T2.",
            f"- E6: tasa media de llegada {e6_arrival:.3f} entre asignaciones factibles, limitada a aproximación uniciclo.",
            "",
            "## Navegación",
            "",
            f"- [Informe canónico]({canonical_link})",
            f"- [Informe de validación]({conference_link})",
            f"- [Figuras F1–F6]({figures_link})",
            f"- [Tablas estadísticas]({tables_link})",
            "- `key_statistics.csv`: estimaciones, IC y denominadores seleccionados.",
            "- `artifact_index.csv`: rutas, tamaños, hashes y manifest de procedencia.",
            "- `manifest.json`: estado consolidado y hashes de este paquete.",
            "",
            "## Vídeos cenitales E6",
            "",
            "La semilla de cada vídeo es una ejecución exitosa próxima a la mediana de tiempo de llegada de su grupo. Son aproximaciones a poses de contacto fijas; no muestran docking, wrench ni transporte de carga.",
            "",
            "| Escenario | N | Semilla | Obstáculos retenidos | Fotogramas | MP4 |",
            "|---|---:|---:|---:|---:|---|",
            *video_lines,
            "",
            "## Limitaciones que no deben ocultarse",
            "",
            "- El estado `partial` es científico, no de integridad: E1 no alcanza las puertas de convergencia/comparabilidad y E4 no alcanza 95% de factibilidad.",
            "- En E6 warehouse, el generador descarta rectángulos que solapan poses iniciales/finales. N=20 y N=40 retienen cero obstáculos en todos los casos; no son evidencia de evitación aunque empleen una malla A*.",
            "- La simulación no prueba convergencia global, estabilidad, robustez, optimalidad entera general ni validez en hardware.",
            "",
        ]
    )


def _estimate(statistics: pd.DataFrame, metric: str) -> float:
    if "metric" not in statistics.columns:
        return float("nan")
    selected = statistics[statistics.metric == metric]
    return float(selected.estimate.iloc[0]) if not selected.empty else float("nan")


def _relative_link(target: Path, base: Path) -> str:
    import os

    return Path(os.path.relpath(target.resolve(), base.resolve())).as_posix()


def _category(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".mp4":
        return "video"
    if "figures" in path.parts:
        return "figure"
    if "tables" in path.parts:
        return "table"
    if "raw" in path.parts:
        return "raw"
    if path.name.startswith("manifest") or path.name.startswith("audit"):
        return "audit"
    if suffix in {".md", ".pdf"}:
        return "report"
    return "data"


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


__all__ = ["build_sp1_result_package"]
