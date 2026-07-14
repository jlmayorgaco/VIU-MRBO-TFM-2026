"""Auditable CPU-only runner for the cumulative physical-coalition certificate campaign."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import yaml
from scipy.stats import binomtest

from .model import CertificateStage, FailureCode, PROTOCOL_VERSION
from .scenario import SCENARIO_FAMILIES, make_world
from .simulation import run_variant

REPO_ROOT = Path(__file__).resolve().parents[3]
STAGES = tuple(stage.value for stage in CertificateStage)


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["_config_path"] = str(config_path.resolve())
    return config


def output_root(config: dict[str, Any]) -> Path:
    return REPO_ROOT / str(config["output_dir"])


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _seed_for(config: dict[str, Any], family_index: int, ordinal: int) -> int:
    if ordinal < int(config["worlds"]["base_per_family"]):
        return int(config["worlds"]["base_seed_start"]) + 1000 * family_index + ordinal
    return int(config["worlds"]["extension_seed_start"]) + 1000 * family_index + ordinal


def prepare_protocol(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    root = output_root(config)
    protocol = root / "protocol"
    for directory in (protocol, root / "smoke", root / "campaign", root / "statistics", root / "figures", root / "audit"):
        directory.mkdir(parents=True, exist_ok=True)
    families = list(config["scenario_families"])
    checkpoints = list(config["worlds"]["precision_checkpoints"])
    registry: dict[str, Any] = {
        "protocol_id": config["protocol_id"],
        "confirmatory_opened": False,
        "dry_run_seeds": list(config["worlds"]["dry_run_seeds"]),
        "test_seeds_1_40": {},
        "extension_seeds_41_60": {},
        "extension_seeds_61_100": {},
    }
    for family_index, family in enumerate(families):
        all_seeds = [_seed_for(config, family_index, ordinal) for ordinal in range(max(checkpoints))]
        registry["test_seeds_1_40"][family] = all_seeds[:40]
        registry["extension_seeds_41_60"][family] = all_seeds[40:60]
        registry["extension_seeds_61_100"][family] = all_seeds[60:100]
    flattened = list(registry["dry_run_seeds"])
    for key in ("test_seeds_1_40", "extension_seeds_41_60", "extension_seeds_61_100"):
        for seeds in registry[key].values():
            flattened.extend(seeds)
    if len(flattened) != len(set(flattened)):
        raise RuntimeError("seed registry contains intersections")
    (protocol / "seed_registry.yaml").write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    environment = {
        "cpu_only": True,
        "cpu_model": platform.processor() or platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "gpu_model": "NOT_USED_CPU_ONLY",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "omp_threads": int(config["runtime"]["omp_threads"]),
    }
    (protocol / "environment.lock.json").write_text(json.dumps(environment, indent=2, sort_keys=True), encoding="utf-8")
    snapshot = {key: value for key, value in config.items() if not key.startswith("_")}
    (protocol / "protocol_snapshot.yaml").write_text(yaml.safe_dump(snapshot, sort_keys=False), encoding="utf-8")
    return {"status": "prepared_pre_freeze", "seed_count": len(flattened), "output_root": str(root)}


def run_dry_run(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    root = output_root(config)
    prepare_protocol(config_path)
    rows: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    for ordinal, family in enumerate(config["scenario_families"]):
        seed = int(config["worlds"]["dry_run_seeds"][ordinal])
        world = make_world(family=family, seed=seed, ordinal=ordinal)
        for stage in CertificateStage:
            row, trajectory = run_variant(world, stage, retain_trajectory=stage == CertificateStage.ROBUST_LOCAL)
            row["campaign_partition"] = "dry_run"
            rows.append(row)
            for point in trajectory:
                trajectories.append({"run_id": row["run_id"], "family": family, "stage": stage.value, **point})
    frame = pd.DataFrame(rows)
    frame.to_parquet(root / "smoke" / "runs.parquet", index=False)
    frame.to_csv(root / "smoke" / "runs.csv", index=False)
    pd.DataFrame(trajectories).to_parquet(root / "smoke" / "trajectories.parquet", index=False)
    deterministic_world = make_world(family=SCENARIO_FAMILIES[0], seed=991337, ordinal=99)
    first, _ = run_variant(deterministic_world, CertificateStage.ROBUST_LOCAL)
    second, _ = run_variant(deterministic_world, CertificateStage.ROBUST_LOCAL)
    ignored = {"runtime_wall_s", "runtime_cpu_s", "runtime_s"}
    deterministic = all(first[key] == second[key] for key in first.keys() - ignored)
    expected_rows = len(config["scenario_families"]) * len(config["certificate_stages"])
    hash_counts = frame.groupby("world_id")["world_hash"].nunique()
    checks = {
        "row_count_valid": len(frame) == expected_rows,
        "stage_set_valid": set(frame["stage"]) == set(config["certificate_stages"]),
        "paired_world_hash_valid": bool((hash_counts == 1).all()),
        "deterministic_reexecution": bool(deterministic),
        "all_runtime_units_seconds": all(column in frame for column in ("runtime_wall_s", "runtime_cpu_s")),
        "failure_rows_preserved": not frame["failure_code"].isna().any(),
        "cpu_only": bool(config["cpu_only"]),
        "no_oracle_fields": not any("oracle" in column.lower() for column in frame.columns),
        "full_obstacle_safe": bool(
            frame.loc[
                (frame["scenario_family"] == "obstacle_network_dropout")
                & (frame["stage"] == CertificateStage.ROBUST_LOCAL.value),
                "collision",
            ].eq(False).all()
        ),
    }
    manifest = {"status": "dry_run_passed" if all(checks.values()) else "dry_run_failed", "passed": all(checks.values()), "checks": checks, "rows": len(frame)}
    (root / "smoke" / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def freeze_protocol(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    root = output_root(config)
    smoke_manifest_path = root / "smoke" / "manifest.json"
    if not smoke_manifest_path.exists() or not json.loads(smoke_manifest_path.read_text(encoding="utf-8")).get("passed"):
        raise RuntimeError("dry-run gate must pass before freeze")
    protocol = root / "protocol"
    source_files = [
        REPO_ROOT / "src/viu_mrob_tfm/physical_coalition/model.py",
        REPO_ROOT / "src/viu_mrob_tfm/physical_coalition/scenario.py",
        REPO_ROOT / "src/viu_mrob_tfm/physical_coalition/simulation.py",
        Path(__file__),
        REPO_ROOT / "scripts/validate_theory_vgne_share.py",
        REPO_ROOT / "scripts/validate_theory_poa.py",
        REPO_ROOT / "scripts/validate_theory_stability.py",
        REPO_ROOT / "docs/research/physical_coalition_theory_v1.md",
    ]
    combined = hashlib.sha256("".join(sha256_path(path) for path in source_files).encode()).hexdigest()
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        commit = "UNAVAILABLE"
    manifest = {
        "protocol_id": config["protocol_id"],
        "protocol_version": config["protocol_version"],
        "frozen": True,
        "status": "frozen_ready_for_execution",
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit_sha": commit,
        "config_sha256": sha256_path(Path(config["_config_path"])),
        "hypotheses_sha256": sha256_path(protocol / "hypotheses.yaml"),
        "seed_registry_sha256": sha256_path(protocol / "seed_registry.yaml"),
        "environment_lock_sha256": sha256_path(protocol / "environment.lock.json"),
        "dry_run_evidence_sha256": sha256_path(smoke_manifest_path),
        "implementation_sha256": combined,
        "theory_v1_evidence_sha256": sha256_path(REPO_ROOT / "results/theory_validation/v1/manifest.json"),
        "theory_v2_evidence_sha256": sha256_path(REPO_ROOT / "results/theory_validation/v2/manifest.json"),
        "theory_v3_evidence_sha256": sha256_path(REPO_ROOT / "results/theory_validation/v3/manifest.json"),
        "cpu_only": True,
        "confirmatory_seeds_opened": False,
    }
    (protocol / "frozen_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    hashes = [f"{sha256_path(path)}  {path.relative_to(root)}" for path in protocol.iterdir() if path.is_file()]
    (protocol / "HASHES.sha256").write_text("\n".join(sorted(hashes)) + "\n", encoding="utf-8")
    return manifest


def _task_payload(config: dict[str, Any], family: str, family_index: int, ordinal: int, stage: str) -> tuple[str, int, int, str]:
    return family, _seed_for(config, family_index, ordinal), ordinal, stage


def _safe_task(payload: tuple[str, int, int, str]) -> dict[str, Any]:
    family, seed, ordinal, stage = payload
    try:
        world = make_world(family=family, seed=seed, ordinal=ordinal)
        row, _ = run_variant(world, stage)
        row["world_ordinal"] = ordinal
        row["campaign_partition"] = "base" if ordinal < 40 else ("extension_41_60" if ordinal < 60 else "extension_61_100")
        row["exception"] = None
        return row
    except Exception as exc:  # failures are evidence and must remain rows
        return {
            "protocol_version": PROTOCOL_VERSION,
            "run_id": hashlib.sha256(stable_json(payload).encode()).hexdigest()[:24],
            "world_id": f"pcert-{family}-{ordinal:03d}",
            "world_hash": None,
            "world_seed": seed,
            "world_ordinal": ordinal,
            "scenario_family": family,
            "stage": stage,
            "method_id": stage,
            "final_physical_success": False,
            "success": False,
            "failure_code": FailureCode.NUMERICAL_ERROR.value,
            "campaign_partition": "base" if ordinal < 40 else ("extension_41_60" if ordinal < 60 else "extension_61_100"),
            "runtime_wall_s": np.nan,
            "runtime_cpu_s": np.nan,
            "exception": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
        }


def _load_runs(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


def _persist_runs(frame: pd.DataFrame, root: Path) -> None:
    frame = frame.drop_duplicates("run_id", keep="first").sort_values(["scenario_family", "world_ordinal", "stage"])
    frame.to_parquet(root / "campaign" / "runs.parquet", index=False)
    frame.to_csv(root / "campaign" / "runs.csv", index=False)


def _execute_tasks(tasks: list[tuple[str, int, int, str]], existing: pd.DataFrame, root: Path, workers: int) -> pd.DataFrame:
    existing_ids = set(existing["run_id"].astype(str)) if not existing.empty and "run_id" in existing else set()
    pending: list[tuple[str, int, int, str]] = []
    for payload in tasks:
        family, seed, ordinal, stage = payload
        world = make_world(family=family, seed=seed, ordinal=ordinal)
        expected_id = hashlib.sha256(f"{PROTOCOL_VERSION}|{world.world_hash}|{stage}".encode()).hexdigest()
        if expected_id not in existing_ids:
            pending.append(payload)
    rows = existing.to_dict("records") if not existing.empty else []
    if workers <= 1:
        iterator: Iterable[dict[str, Any]] = (_safe_task(task) for task in pending)
        for index, row in enumerate(iterator, 1):
            rows.append(row)
            if index % 24 == 0:
                _persist_runs(pd.DataFrame(rows), root)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_safe_task, task) for task in pending]
            for index, future in enumerate(as_completed(futures), 1):
                rows.append(future.result())
                if index % 24 == 0:
                    _persist_runs(pd.DataFrame(rows), root)
    frame = pd.DataFrame(rows)
    _persist_runs(frame, root)
    return pd.read_parquet(root / "campaign" / "runs.parquet")


def run_official(config_path: str | Path, *, workers: int | None = None, resume: bool = True) -> dict[str, Any]:
    config = load_config(config_path)
    root = output_root(config)
    frozen = root / "protocol" / "frozen_manifest.json"
    if not frozen.exists() or json.loads(frozen.read_text(encoding="utf-8")).get("status") != "frozen_ready_for_execution":
        raise RuntimeError("confirmatory seeds cannot be opened before a valid freeze")
    registry_path = root / "protocol" / "seed_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not registry.get("confirmatory_opened"):
        registry["confirmatory_opened"] = True
        registry["opened_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        opening = {"event": "confirmatory_seed_opening", "after_freeze": True, "frozen_manifest_sha256": sha256_path(frozen), "time_utc": registry["opened_at_utc"]}
        (root / "audit" / "seed_opening.json").write_text(json.dumps(opening, indent=2), encoding="utf-8")
    runs_path = root / "campaign" / "runs.parquet"
    existing = _load_runs(runs_path) if resume else pd.DataFrame()
    tasks = [
        _task_payload(config, family, family_index, ordinal, stage)
        for family_index, family in enumerate(config["scenario_families"])
        for ordinal in range(int(config["worlds"]["base_per_family"]))
        for stage in config["certificate_stages"]
    ]
    started = time.perf_counter()
    frame = _execute_tasks(tasks, existing, root, workers or int(config["runtime"]["workers"]))
    expected = len(config["scenario_families"]) * int(config["worlds"]["base_per_family"]) * len(config["certificate_stages"])
    base = frame.loc[frame["world_ordinal"] < int(config["worlds"]["base_per_family"])]
    manifest = {
        "status": "base_complete" if len(base) == expected and base["run_id"].nunique() == expected else "base_incomplete",
        "expected_base_rows": expected,
        "executed_base_rows": len(base),
        "unique_base_rows": int(base["run_id"].nunique()),
        "numerical_errors": int((base["failure_code"] == FailureCode.NUMERICAL_ERROR.value).sum()),
        "elapsed_wall_s_this_invocation": time.perf_counter() - started,
        "cpu_only": True,
    }
    (root / "campaign" / "base_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def _paired_bootstrap(values: np.ndarray, samples: int, seed: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    estimate = float(np.mean(values)) if len(values) else np.nan
    if len(values) < 2:
        return estimate, np.nan, np.nan
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(samples, len(values)))
    means = values[indices].mean(axis=1)
    return estimate, float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _family_precision(frame: pd.DataFrame, family: str, n_worlds: int, config: dict[str, Any]) -> list[dict[str, Any]]:
    subset = frame.loc[(frame["scenario_family"] == family) & (frame["world_ordinal"] < n_worlds)]
    pivot = subset.pivot(index="world_ordinal", columns="stage", values="final_physical_success").astype(float)
    rows: list[dict[str, Any]] = []
    for index, (before, after) in enumerate(zip(STAGES[:-1], STAGES[1:])):
        paired = pivot[[before, after]].dropna()
        delta = paired[after].to_numpy() - paired[before].to_numpy()
        estimate, low, high = _paired_bootstrap(delta, int(config["precision"]["bootstrap_samples"]), 88000 + index + 100 * n_worlds + sum(map(ord, family)))
        rows.append({"scenario_family": family, "n_worlds": len(paired), "before": before, "after": after, "estimate": estimate, "ci95_low": low, "ci95_high": high, "ci95_width": high - low})
    return rows


def extend_by_precision(config_path: str | Path, *, workers: int | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    root = output_root(config)
    frame = _load_runs(root / "campaign" / "runs.parquet")
    if frame.empty:
        raise RuntimeError("base campaign must run before precision extension")
    decisions: list[dict[str, Any]] = []
    active_families = set(config["scenario_families"])
    checkpoints = list(config["worlds"]["precision_checkpoints"])
    for checkpoint_index, checkpoint in enumerate(checkpoints[:-1]):
        next_checkpoint = checkpoints[checkpoint_index + 1]
        to_extend: set[str] = set()
        for family in sorted(active_families):
            precision_rows = _family_precision(frame, family, checkpoint, config)
            max_width = max(row["ci95_width"] for row in precision_rows)
            extend = bool(max_width > float(config["precision"]["max_ci95_width"]))
            decisions.append({"checkpoint": checkpoint, "scenario_family": family, "max_ci95_width": max_width, "threshold": float(config["precision"]["max_ci95_width"]), "decision": "extend" if extend else "stop", "reason": "precision_width_only"})
            if extend:
                to_extend.add(family)
        if not to_extend:
            break
        tasks = [
            _task_payload(config, family, list(config["scenario_families"]).index(family), ordinal, stage)
            for family in sorted(to_extend)
            for ordinal in range(checkpoint, next_checkpoint)
            for stage in config["certificate_stages"]
        ]
        frame = _execute_tasks(tasks, frame, root, workers or int(config["runtime"]["workers"]))
        active_families = to_extend
    decision_frame = pd.DataFrame(decisions)
    decision_frame.to_csv(root / "campaign" / "precision_decisions.csv", index=False)
    decision_frame.to_parquet(root / "campaign" / "precision_decisions.parquet", index=False)
    final_sizes = frame.groupby("scenario_family")["world_ordinal"].nunique().astype(int).to_dict()
    manifest = {"status": "precision_extension_complete", "final_worlds_by_family": final_sizes, "total_rows": len(frame), "extension_rule": "ci95_width_only"}
    (root / "campaign" / "precision_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def _holm(p_values: list[float]) -> list[float]:
    count = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(count, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = min(1.0, (count - rank) * float(p_values[idx]))
        running = max(running, candidate)
        adjusted[idx] = running
    return adjusted.tolist()


def analyze_campaign(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    root = output_root(config)
    frame = _load_runs(root / "campaign" / "runs.parquet")
    if frame.empty:
        raise RuntimeError("no campaign rows")
    summary = frame.groupby(["scenario_family", "stage"], as_index=False).agg(
        n_worlds=("world_ordinal", "nunique"), success_rate=("final_physical_success", "mean"), physical_false_positive_rate=("physical_false_positive", "mean"), accepted_rate=("accepted_by_stage", "mean"), mean_time_to_solution_s=("time_to_solution_s", "mean"), mean_messages=("messages", "mean"), mean_runtime_wall_s=("runtime_wall_s", "mean"), collision_rate=("collision", "mean"), dropout_unrecovered_rate=("dropout_unrecovered", "mean"), mean_minimum_clearance_m=("minimum_clearance_m", "mean"), mean_static_wrench_residual=("static_wrench_residual", "mean"), mean_dynamic_wrench_residual=("mean_dynamic_wrench_residual", "mean"),
    )
    summary.to_csv(root / "statistics" / "summary.csv", index=False)
    summary.to_parquet(root / "statistics" / "summary.parquet", index=False)
    contrasts: list[dict[str, Any]] = []
    for family in config["scenario_families"]:
        n_worlds = int(frame.loc[frame["scenario_family"] == family, "world_ordinal"].nunique())
        subset = frame.loc[frame["scenario_family"] == family]
        pivot = subset.pivot(index="world_ordinal", columns="stage", values="final_physical_success").astype(int)
        for index, (before, after) in enumerate(zip(STAGES[:-1], STAGES[1:])):
            paired = pivot[[before, after]].dropna()
            delta = paired[after].to_numpy() - paired[before].to_numpy()
            estimate, low, high = _paired_bootstrap(delta, int(config["precision"]["bootstrap_samples"]), 120000 + index + sum(map(ord, family)))
            n01 = int(((paired[before] == 0) & (paired[after] == 1)).sum())
            n10 = int(((paired[before] == 1) & (paired[after] == 0)).sum())
            raw_p = float(binomtest(min(n01, n10), n01 + n10, 0.5, alternative="two-sided").pvalue) if n01 + n10 else 1.0
            contrasts.append({"scenario_family": family, "before": before, "after": after, "effect_estimate": estimate, "CI95_low": low, "CI95_high": high, "raw_p": raw_p, "n_worlds": len(paired), "improved_worlds": n01, "degraded_worlds": n10, "margin": 0.0})
    adjusted = _holm([row["raw_p"] for row in contrasts])
    for row, p_adj in zip(contrasts, adjusted):
        row["Holm_adjusted_p"] = p_adj
        row["effect_size"] = row["effect_estimate"]
        row["decision"] = "positive_supported" if row["CI95_low"] > 0 and p_adj < float(config["statistics"]["alpha"]) else ("negative_supported" if row["CI95_high"] < 0 and p_adj < float(config["statistics"]["alpha"]) else "inconclusive_or_null")
    contrast_frame = pd.DataFrame(contrasts)
    contrast_frame.to_csv(root / "statistics" / "paired_contrasts_holm.csv", index=False)
    contrast_frame.to_parquet(root / "statistics" / "paired_contrasts_holm.parquet", index=False)
    failures = frame.groupby(["scenario_family", "stage", "failure_code"], as_index=False).size().rename(columns={"size": "count"})
    failures.to_csv(root / "statistics" / "failure_registry.csv", index=False)
    manifest = {"status": "analysis_complete", "rows": len(frame), "families": int(frame["scenario_family"].nunique()), "contrasts": len(contrast_frame), "holm_applied": True, "numerical_errors": int((frame["failure_code"] == FailureCode.NUMERICAL_ERROR.value).sum())}
    (root / "statistics" / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    _write_report(config, frame, summary, contrast_frame)
    return manifest


def render_figures(config_path: str | Path) -> dict[str, Any]:
    import matplotlib.pyplot as plt

    # Embed TrueType outlines in PDF/PS outputs; Type-3 fonts are unsuitable for deposit.
    plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42})

    config = load_config(config_path)
    root = output_root(config)
    figures = root / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    summary = pd.read_parquet(root / "statistics" / "summary.parquet")
    frame = pd.read_parquet(root / "campaign" / "runs.parquet")
    produced: list[str] = []

    def save(fig: Any, name: str) -> None:
        for suffix in ("png", "pdf", "svg"):
            path = figures / f"{name}.{suffix}"
            fig.savefig(path, dpi=220, bbox_inches="tight")
            produced.append(str(path.relative_to(root)))
        plt.close(fig)

    for metric, title, name in (
        ("success_rate", "Éxito físico final", "certificate_success_heatmap"),
        ("physical_false_positive_rate", "Falsos positivos físicos", "physical_false_positive_heatmap"),
    ):
        matrix = summary.pivot(index="scenario_family", columns="stage", values=metric).reindex(index=config["scenario_families"], columns=STAGES)
        fig, ax = plt.subplots(figsize=(10.2, 3.7))
        image = ax.imshow(matrix.to_numpy(), vmin=0, vmax=1, cmap="viridis" if metric == "success_rate" else "magma_r")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix.iloc[i,j]:.2f}", ha="center", va="center", color="white" if matrix.iloc[i,j] < 0.35 or matrix.iloc[i,j] > 0.75 else "black", fontsize=8)
        ax.set_xticks(range(len(STAGES)), [stage.replace("_", "\n") for stage in STAGES], fontsize=7)
        ax.set_yticks(range(len(config["scenario_families"])), config["scenario_families"], fontsize=8)
        ax.set_title(title)
        fig.colorbar(image, ax=ax, fraction=0.025)
        save(fig, name)

    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    for family in config["scenario_families"]:
        data = summary.loc[summary["scenario_family"] == family].set_index("stage").reindex(STAGES)
        ax.plot(range(len(STAGES)), data["success_rate"], marker="o", label=family)
    ax.set_xticks(range(len(STAGES)), [stage.split("_")[0] for stage in STAGES])
    ax.set_ylim(-0.03, 1.03)
    ax.set_ylabel("Proporción de éxito físico")
    ax.set_xlabel("Escalón acumulativo")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    save(fig, "cumulative_certificate_ladder")

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for stage in STAGES:
        data = summary.loc[summary["stage"] == stage]
        ax.scatter(data["mean_messages"], 1.0 - data["success_rate"], label=stage, s=45)
    ax.set_xlabel("Mensajes medios")
    ax.set_ylabel("Tasa de fallo físico")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=6, ncol=2)
    save(fig, "quality_messages_pareto")

    trajectories: list[dict[str, Any]] = []
    fig, ax = plt.subplots(figsize=(7.0, 5.4))
    for family_index, family in enumerate(config["scenario_families"]):
        seed = _seed_for(config, family_index, 0)
        world = make_world(family=family, seed=seed, ordinal=0)
        row, trajectory = run_variant(world, CertificateStage.ROBUST_LOCAL, retain_trajectory=True)
        for point in trajectory:
            trajectories.append({"run_id": row["run_id"], "scenario_family": family, **point})
        ax.plot([point["x"] for point in trajectory], [point["y"] for point in trajectory], label=family)
        if family == "obstacle_network_dropout":
            circle = plt.Circle(world.obstacle_center, world.obstacle_radius + 0.82, color="red", alpha=0.18)
            ax.add_patch(circle)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    save(fig, "representative_full_trajectories")
    pd.DataFrame(trajectories).to_parquet(root / "campaign" / "representative_trajectories.parquet", index=False)
    manifest = {"status": "figures_complete", "files": produced, "formats": ["PNG", "PDF", "SVG"]}
    (figures / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def _write_report(config: dict[str, Any], frame: pd.DataFrame, summary: pd.DataFrame, contrasts: pd.DataFrame) -> None:
    root = output_root(config)
    final_sizes = frame.groupby("scenario_family")["world_ordinal"].nunique().astype(int).to_dict()
    full = summary.loc[summary["stage"] == CertificateStage.ROBUST_LOCAL.value, ["scenario_family", "success_rate", "physical_false_positive_rate", "mean_messages", "mean_runtime_wall_s"]]
    lines = [
        "# Physical-coalition certificate campaign — final report",
        "",
        f"Protocol: `{config['protocol_id']}`. CPU-only reduced-order Python simulation; no GPU, MARL training, CoppeliaSim, replacement seeds or synthetic rows.",
        "",
        "## Execution gate",
        "",
        f"- Retained rows: {len(frame)}; unique run IDs: {frame['run_id'].nunique()}.",
        f"- Numerical errors: {(frame['failure_code'] == FailureCode.NUMERICAL_ERROR.value).sum()}.",
        f"- Final paired worlds by family: `{json.dumps(final_sizes, sort_keys=True)}`.",
        "- Confirmatory seeds were opened only after `frozen_manifest.json` recorded `frozen_ready_for_execution`.",
        "- Precision extensions used CI-width only; Holm was applied at final sample sizes.",
        "",
        "## FULL robust-local stage",
        "",
        full.to_markdown(index=False),
        "",
        "## Confirmatory paired contrasts",
        "",
        contrasts.to_markdown(index=False),
        "",
        "## Interpretation boundary",
        "",
        "The ladder isolates which certificate removes which physical false positive inside the specified deterministic model. Static acceptance is never reported as dynamic convergence. The mechanics claim assumes an established rigid grasp with bounded signed traction; safety requires feasible HOCBF actuation. The empirical rates are not universal theoretical bounds.",
    ]
    (root / "FINAL_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def finalize_manifest(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    root = output_root(config)
    frame = pd.read_parquet(root / "campaign" / "runs.parquet")
    expected_base = len(config["scenario_families"]) * 40 * len(config["certificate_stages"])
    base_rows = int((frame["world_ordinal"] < 40).sum())
    required = [root / "protocol/frozen_manifest.json", root / "campaign/precision_manifest.json", root / "statistics/manifest.json", root / "figures/manifest.json", root / "FINAL_REPORT.md"]
    gates = {
        "freeze_valid": json.loads(required[0].read_text(encoding="utf-8")).get("status") == "frozen_ready_for_execution",
        "base_count_960": base_rows == expected_base == 960,
        "unique_rows": frame["run_id"].nunique() == len(frame),
        "all_failures_preserved": not frame["failure_code"].isna().any(),
        "no_numerical_errors": not (frame["failure_code"] == FailureCode.NUMERICAL_ERROR.value).any(),
        "cpu_only": bool(config["cpu_only"]),
        "precision_manifest": required[1].exists(),
        "statistics_complete": required[2].exists(),
        "figures_complete": required[3].exists(),
        "report_complete": required[4].exists(),
    }
    manifest = {
        "protocol_id": config["protocol_id"],
        "status": "campaign_closed" if all(gates.values()) else "campaign_incomplete",
        "gates": gates,
        "base_rows": base_rows,
        "total_rows": len(frame),
        "final_worlds_by_family": frame.groupby("scenario_family")["world_ordinal"].nunique().astype(int).to_dict(),
        "runs_sha256": sha256_path(root / "campaign/runs.parquet"),
        "report_sha256": sha256_path(root / "FINAL_REPORT.md") if (root / "FINAL_REPORT.md").exists() else None,
    }
    (root / "FINAL_RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (root / "GATE_STATUS.json").write_text(json.dumps({"status": manifest["status"], "gates": gates}, indent=2, sort_keys=True), encoding="utf-8")
    return manifest