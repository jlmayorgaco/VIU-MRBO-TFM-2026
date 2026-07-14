"""Build the Stage-4 claim/artifact and contrast/estimand registries."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/generated"
TEX_OUT = ROOT / "docs/doc-05-final-report/sections/claim-artifact-registry.tex"


def sha256(path: str) -> str:
    candidate = ROOT / path
    if not candidate.exists() or not candidate.is_file():
        return "NO_DISPONIBLE"
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


CLAIMS = [
    {
        "claim_id": "C-INT",
        "experiment": "A0--FULL",
        "status": "confirmatoria_simulacion_planar",
        "authorized_claim": "La escalera separa cardinalidad, capacidad, wrench, mecánica y recuperación; los efectos dependen de la familia.",
        "config": "configs/experiments/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN.yaml",
        "seed_registry": "results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/protocol/seed_registry.yaml",
        "command": "python scripts/run_physical_coalition_certificate.py run --config configs/experiments/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN.yaml",
        "manifest": "results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/FINAL_RUN_MANIFEST.json",
        "evidence": "results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/statistics/paired_contrasts_holm.csv",
        "limitation": "Planta planar numérica; selector FULL con candidatos globales; sin fricción de contacto ni hardware.",
    },
    {
        "claim_id": "C-SP0",
        "experiment": "SP0",
        "status": "historica_bloqueada_para_MARL",
        "authorized_claim": "Existen tres checkpoints MAPPO-GNN trazables de 200.000 transiciones; el éxito cerrado observado procede de la reparación.",
        "config": "configs/experiments/sp0/SP0_PROTOCOL_v1_2_CPU.yaml",
        "seed_registry": "results/sp0/SP0_PROTOCOL_v1_2_CPU/protocol/seed_registry.yaml",
        "command": "python scripts/run_sp0_experiment.py configs/experiments/sp0/SP0_PROTOCOL_v1_2_CPU.yaml",
        "manifest": "results/sp0/SP0_PROTOCOL_v1_2_CPU/FINAL_RUN_MANIFEST.json",
        "evidence": "results/sp0/SP0_AUDIT_v1/SP0_AUDIT_REPORT.md",
        "limitation": "RAW no supera controles; separación reparación/QR y varios gates estadísticos fallan. No autoriza superioridad aprendida.",
    },
    {
        "claim_id": "C-SP1",
        "experiment": "SP1",
        "status": "confirmatoria_modular",
        "authorized_claim": "Smith-QR mejora a greedy en regret, pero no a todos los controles; el cierre explica parte sustancial del desempeño.",
        "config": "configs/experiments/sp1/SP1_HOMOGENEOUS_v1_1.yaml",
        "seed_registry": "NO_DISPONIBLE",
        "command": "python scripts/run_sp1_homogeneous.py configs/experiments/sp1/SP1_HOMOGENEOUS_v1_1.yaml",
        "manifest": "results/sp1/SP1_HOMOGENEOUS_v1_1/manifest.json",
        "evidence": "results/sp1/SP1_HOMOGENEOUS_v1_1/tables/hypothesis_results.csv",
        "limitation": "El cierre QR usa preferencias globales; no acredita distribución extremo a extremo.",
    },
    {
        "claim_id": "C-SP2",
        "experiment": "SP2",
        "status": "confirmatoria_modular",
        "authorized_claim": "La capacidad efectiva mejora la señal, pero ninguna dinámica domina y uniforme+closure es competitivo.",
        "config": "configs/experiments/sp2/SP2_HETEROGENEOUS_GAME_v1_2.yaml",
        "seed_registry": "NO_DISPONIBLE",
        "command": "python scripts/run_sp2_heterogeneous.py configs/experiments/sp2/SP2_HETEROGENEOUS_GAME_v1_2.yaml",
        "manifest": "results/sp2/SP2_HETEROGENEOUS_GAME_v1_2/manifest.json",
        "evidence": "results/sp2/SP2_HETEROGENEOUS_GAME_v1_2/tables/hypothesis_results.csv",
        "limitation": "Capacidad escalar; no certifica fuerza, torque ni contacto.",
    },
    {
        "claim_id": "C-SP3",
        "experiment": "SP3",
        "status": "confirmatoria_modular",
        "authorized_claim": "La relajación satisface la referencia QP/KKT y la guardia elimina falsos positivos wrench en el generador.",
        "config": "configs/experiments/sp3/SP3_WRENCH_NASH_GAME_v1_1.yaml",
        "seed_registry": "NO_DISPONIBLE",
        "command": "python scripts/run_sp3_wrench_nash.py configs/experiments/sp3/SP3_WRENCH_NASH_GAME_v1_1.yaml",
        "manifest": "results/sp3/SP3_WRENCH_NASH_GAME_v1_1/manifest.json",
        "evidence": "results/sp3/SP3_WRENCH_NASH_GAME_v1_1/tables/hypothesis_results.csv",
        "limitation": "La guardia es global y domina CLOSED; equivalencia continua no implica optimalidad entera.",
    },
    {
        "claim_id": "C-SP4",
        "experiment": "SP4",
        "status": "confirmatoria_modular_con_sensibilidad",
        "authorized_claim": "Los cinco contrastes conservan dirección y soporte al agregar por 18 bloques independientes.",
        "config": "configs/experiments/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3.yaml",
        "seed_registry": "NO_DISPONIBLE",
        "command": "python scripts/run_sp4_docking_game.py configs/experiments/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3.yaml",
        "manifest": "results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/manifest.json",
        "evidence": "results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/statistics/block_sensitivity.csv",
        "limitation": "18 bloques semilla-flota; 108 instancias no son réplicas independientes; uniciclo dinámico reducido.",
    },
    {
        "claim_id": "C-SP5",
        "experiment": "SP5",
        "status": "confirmatoria_modular",
        "authorized_claim": "El filtro CBF reduce colisiones de la variante Hamiltoniana RAW, sin demostrar dominancia global.",
        "config": "configs/experiments/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2.yaml",
        "seed_registry": "results/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2/protocol/seed_registry.yaml",
        "command": "python scripts/run_sp5_payload_transport.py configs/experiments/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2.yaml",
        "manifest": "results/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2/manifest.json",
        "evidence": "results/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2/tables/hypothesis_results.csv",
        "limitation": "Simulación CPU desde contactos fijos; cero colisiones observadas no equivale a seguridad funcional.",
    },
    {
        "claim_id": "C-SP6",
        "experiment": "SP6",
        "status": "descriptiva_historica",
        "authorized_claim": "La campaña mide reemplazo, recuperación y pérdida de carga bajo fallos simulados.",
        "config": "configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml",
        "seed_registry": "NO_DISPONIBLE",
        "command": "python scripts/run_sp6_experiment.py configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml",
        "manifest": "results/sp6/SP6_MC_robustness_comparison_high_power/manifest.json",
        "evidence": "results/sp6/SP6_MC_robustness_comparison_high_power/tables/hypothesis_results.csv",
        "limitation": "Modelo de fallo y recuperación simulado; no HIL ni robot real.",
    },
    {
        "claim_id": "C-SP7",
        "experiment": "SP7",
        "status": "descriptiva",
        "authorized_claim": "La canalización cuantifica conectividad, pérdida, retardo, sensing y éxito dentro de su generador.",
        "config": "configs/experiments/sp7/SP7_MC_communication_robustness_high_power.yaml",
        "seed_registry": "NO_DISPONIBLE",
        "command": "python scripts/run_sp7_experiment.py configs/experiments/sp7/SP7_MC_communication_robustness_high_power.yaml",
        "manifest": "NO_DISPONIBLE",
        "evidence": "results/sp7/SP7_MC_communication_robustness_high_power/report.md",
        "limitation": "Sin freeze/manifiesto final promovible ni modelo RF; no se eleva a evidencia confirmatoria.",
    },
    {
        "claim_id": "C-SP8",
        "experiment": "SP8",
        "status": "exploratoria",
        "authorized_claim": "El generador mesoscópico describe tendencias de calidad entre 5 y 50.000 AMR.",
        "config": "configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml",
        "seed_registry": "NO_DISPONIBLE",
        "command": "python scripts/run_sp8_experiment.py configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml",
        "manifest": "NO_DISPONIBLE",
        "evidence": "results/sp8/SP8_MC_fleet_ladder_high_power/report.md",
        "limitation": "Tiempo y memoria no fueron medidos con watchdog/RSS común; no demuestra intractabilidad industrial.",
    },
]


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def tex_escape(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("#", r"\#")
    )


STATUS_LABELS = {
    "confirmatoria_simulacion_planar": "confirmatoria en simulación planar",
    "historica_bloqueada_para_MARL": "histórica bloqueada para MARL",
    "confirmatoria_modular": "confirmatoria modular",
    "confirmatoria_modular_con_sensibilidad": "confirmatoria modular con sensibilidad",
    "descriptiva_historica": "descriptiva histórica",
    "descriptiva": "descriptiva",
    "exploratoria": "exploratoria",
}


def build_claim_registry() -> list[dict[str, object]]:
    records = []
    for claim in CLAIMS:
        record = dict(claim)
        record["config_sha256"] = sha256(str(claim["config"]))
        record["manifest_sha256"] = sha256(str(claim["manifest"]))
        record["evidence_sha256"] = sha256(str(claim["evidence"]))
        records.append(record)
    write_csv(OUT / "claim_artifact_registry.csv", records)
    (OUT / "claim_artifact_registry.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Claim–artifact registry",
        "",
        "| Claim | Experiment | Status | Authorized claim | Evidence | Limitation |",
        "|---|---|---|---|---|---|",
    ]
    for row in records:
        lines.append(
            f"| {row['claim_id']} | {row['experiment']} | {row['status']} | {row['authorized_claim']} | "
            f"`{row['evidence']}` | {row['limitation']} |"
        )
    lines.append("")
    (OUT / "claim_artifact_registry.md").write_text("\n".join(lines), encoding="utf-8")

    tex = [
        r"\begin{landscape}",
        r"\scriptsize",
        r"\begin{longtable}{p{1.2cm}p{1.5cm}p{3.5cm}p{7.8cm}p{6.7cm}}",
        r"\caption{Registro único afirmación--artefacto y límite de inferencia.}\label{tab:claim-artifact-registry}\\",
        r"\toprule",
        r"ID & Campaña & Estado & Afirmación autorizada & Límite decisivo \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule ID & Campaña & Estado & Afirmación autorizada & Límite decisivo \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in records:
        tex.append(
            "{} & {} & {} & {} & {} \\\\".format(
                tex_escape(str(row["claim_id"])),
                tex_escape(str(row["experiment"])),
                tex_escape(STATUS_LABELS[str(row["status"])]),
                tex_escape(str(row["authorized_claim"])),
                tex_escape(str(row["limitation"])),
            )
        )
    tex.extend([r"\bottomrule", r"\end{longtable}", r"\end{landscape}", ""])
    TEX_OUT.write_text("\n".join(tex), encoding="utf-8")
    return records


def build_contrast_registry() -> list[dict[str, object]]:
    hyp_path = ROOT / "configs/experiments/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN_hypotheses.yaml"
    hypotheses = yaml.safe_load(hyp_path.read_text(encoding="utf-8"))
    contrasts = pd.read_csv(
        ROOT / "results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/statistics/paired_contrasts_holm.csv"
    )
    records: list[dict[str, object]] = []
    for hypothesis in hypotheses["contrasts"]:
        row = contrasts[
            (contrasts["scenario_family"] == hypothesis["family"])
            & (contrasts["before"] == hypothesis["before"])
            & (contrasts["after"] == hypothesis["after"])
        ].iloc[0]
        records.append(
            {
                "scope": "A0--FULL",
                "contrast_id": hypothesis["id"],
                "endpoint": "final_physical_success",
                "independent_unit": "paired_world",
                "estimand": "paired risk difference after-minus-before",
                "test": "exact two-sided McNemar",
                "interval": "paired percentile bootstrap 95%",
                "multiplicity": "Holm across 20",
                "analysis_seed": hypothesis["bootstrap_seed"],
                "n_independent": int(row["n_worlds"]),
                "effect": float(row["effect_estimate"]),
                "ci95_low": float(row["CI95_low"]),
                "ci95_high": float(row["CI95_high"]),
                "p_holm": float(row["Holm_adjusted_p"]),
                "decision": row["decision"],
                "artifact": "results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/statistics/paired_contrasts_holm.csv",
            }
        )

    block = pd.read_csv(
        ROOT / "results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/statistics/block_sensitivity.csv"
    )
    for _, row in block.iterrows():
        records.append(
            {
                "scope": "SP4",
                "contrast_id": row["hypothesis"],
                "endpoint": row["metric"],
                "independent_unit": "seed-by-fleet block",
                "estimand": "mean paired difference; sign consistency by block",
                "test": "exact one-sided sign test",
                "interval": "instance-level interval descriptive only",
                "multiplicity": "Holm across 5",
                "analysis_seed": "deterministic",
                "n_independent": int(row["independent_blocks"]),
                "effect": float(row["mean_original_difference"]),
                "ci95_low": "NA",
                "ci95_high": "NA",
                "p_holm": float(row["p_holm"]),
                "decision": "supported" if row["supported_at_0_05"] else "not_supported",
                "artifact": "results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/statistics/block_sensitivity.csv",
            }
        )
    write_csv(OUT / "contrast_estimand_registry.csv", records)
    (OUT / "contrast_estimand_registry.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Contrast–estimand registry",
        "",
        "| Scope | Contrast | Unit | Endpoint | Test | Multiplicity | n | Effect | Holm p | Decision |",
        "|---|---|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in records:
        lines.append(
            f"| {row['scope']} | {row['contrast_id']} | {row['independent_unit']} | {row['endpoint']} | "
            f"{row['test']} | {row['multiplicity']} | {row['n_independent']} | {row['effect']:.6g} | "
            f"{row['p_holm']:.6g} | {row['decision']} |"
        )
    lines.append("")
    (OUT / "contrast_estimand_registry.md").write_text("\n".join(lines), encoding="utf-8")
    return records


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    claims = build_claim_registry()
    contrasts = build_contrast_registry()
    print(f"wrote {len(claims)} claims and {len(contrasts)} contrasts")


if __name__ == "__main__":
    main()
