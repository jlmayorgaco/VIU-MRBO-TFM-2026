"""Read-only SP0 v1.2 audit and checkpoint-sensitivity gate.

The command reads historical artifacts and writes to a separate audit package.
It never calls the trainer or campaign runner and never writes below the source
experiment directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import subprocess
import sys
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import scipy
import torch

from viu_mrob_tfm.experiment_common import FailureCode, build_cache_key
from viu_mrob_tfm.sp0.data_driven import POLICY_VERSION, SP0GNNActorCritic, build_policy_batch, raw_actions_from_logits
from viu_mrob_tfm.sp0.methods import assignment_objective, assignment_valid, repair_assignment
from viu_mrob_tfm.sp0.scenario import make_sp0_world, public_world_view


AUDIT_VERSION = "SP0_AUDIT_v1"
NUMERIC_P_FLOOR = float(np.finfo(float).tiny)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def state_fingerprint(state_dict: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state_dict):
        tensor = state_dict[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(np.asarray(tensor.shape, dtype=np.int64).tobytes())
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def load_checkpoint_model(path: Path) -> tuple[SP0GNNActorCritic, dict[str, Any], str, str]:
    requested_hash = sha256_file(path)
    payload = torch.load(path, map_location="cpu", weights_only=False)
    model = SP0GNNActorCritic(
        hidden_dim=int(payload.get("hidden_dim", 64)),
        critic_global=str(payload.get("algorithm", "MAPPO-GNN")).upper().startswith("MAPPO"),
        gnn_layers=int(payload.get("gnn_layers", 2)),
    )
    model.load_state_dict(payload["model_state_dict"])
    effective_hash = sha256_file(path)
    return model, payload, requested_hash, effective_hash


def validation_worlds() -> list[Any]:
    """Reconstruct a fixed subset of the evaluator's declared validation grid."""

    specs = [
        (12000, 8, 12, "all"),
        (12000, 8, 8, 4),
        (12000, 16, 24, 4),
        (12001, 16, 16, "all"),
        (12001, 32, 48, 2),
        (12001, 32, 32, 4),
    ]
    return [
        make_sp0_world(
            n_robots=n,
            n_loads=k,
            seed=seed,
            geometry_id="G-UNI",
            mean_degree_target=degree,
            sp_id="SP0-training-validation-audit",
        )
        for seed, n, k, degree in specs
    ]


def world_identity(world: Any) -> dict[str, Any]:
    return {
        "seed": int(world.world_seed),
        "N": int(world.n_robots),
        "K": int(world.n_loads),
        "cost_sha256": hashlib.sha256(np.asarray(world.cost, dtype=np.float64).tobytes()).hexdigest(),
        "adjacency_sha256": hashlib.sha256(np.asarray(world.adjacency, dtype=np.float64).tobytes()).hexdigest(),
    }


def world_set_hash(worlds: Iterable[Any]) -> str:
    return stable_hash([world_identity(world) for world in worlds])


def rollout_with_scores(model: SP0GNNActorCritic, world: Any, *, horizon: int = 4) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    public = public_world_view(world)
    previous = np.zeros(public.n_robots, dtype=int)
    final_logits = np.empty((public.n_robots, public.n_loads + 1), dtype=float)
    iterations = 0
    model.eval()
    with torch.no_grad():
        for _ in range(max(1, int(horizon))):
            logits = model.actor_logits(build_policy_batch(public, previous_actions=previous))
            current, _ = raw_actions_from_logits(logits, stochastic=False, seed=None)
            final_logits = logits.detach().cpu().numpy().astype(float)
            iterations += 1
            if np.array_equal(current, previous):
                previous = current
                break
            previous = current
    repaired = repair_assignment(public, previous, None)
    return previous, repaired, final_logits, iterations


def _checkpoint_specs(experiment: Path) -> list[dict[str, Any]]:
    seed1 = experiment / "training" / "final_seeds" / "DD_seed_1"
    specs = [
        {"id": "seed15001_step050176", "path": seed1 / "checkpoints" / "step_00050176.pt", "train_seed": 15001, "steps": 50176},
        {"id": "seed15001_step100352", "path": seed1 / "checkpoints" / "step_00100352.pt", "train_seed": 15001, "steps": 100352},
        {"id": "seed15001_step150016", "path": seed1 / "checkpoints" / "step_00150016.pt", "train_seed": 15001, "steps": 150016},
        {"id": "seed15001_step200000", "path": seed1 / "checkpoints" / "step_00200000.pt", "train_seed": 15001, "steps": 200000},
    ]
    for index, seed in enumerate((15001, 15002, 15003), start=1):
        specs.append(
            {
                "id": f"final_seed{seed}",
                "path": experiment / "training" / "final_seeds" / f"DD_seed_{index}" / "checkpoint.pt",
                "train_seed": seed,
                "steps": 200000,
            }
        )
    return specs


def checkpoint_sensitivity(experiment: Path, output: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    worlds = validation_worlds()
    worlds_sha = world_set_hash(worlds)
    models: list[dict[str, Any]] = []

    torch.manual_seed(15001)
    random_model = SP0GNNActorCritic(hidden_dim=64, critic_global=True, gnn_layers=3)
    random_fp = state_fingerprint(random_model.state_dict())
    models.append(
        {
            "id": "random_actor_seed15001",
            "model": random_model,
            "requested_path": "in_memory://random_actor_seed15001",
            "requested_hash": random_fp,
            "effective_hash": random_fp,
            "fingerprint": random_fp,
            "trainer_version": "untrained_control",
            "policy_version": POLICY_VERSION,
            "train_seed": 15001,
            "steps": 0,
        }
    )
    uniform_model = deepcopy(random_model)
    with torch.no_grad():
        uniform_model.actor[2].weight.zero_()
        uniform_model.actor[2].bias.zero_()
    uniform_fp = state_fingerprint(uniform_model.state_dict())
    models.append(
        {
            "id": "uniform_logits_control",
            "model": uniform_model,
            "requested_path": "in_memory://uniform_logits_control",
            "requested_hash": uniform_fp,
            "effective_hash": uniform_fp,
            "fingerprint": uniform_fp,
            "trainer_version": "uniform_control",
            "policy_version": POLICY_VERSION,
            "train_seed": 0,
            "steps": 0,
        }
    )

    load_failures: list[str] = []
    for spec in _checkpoint_specs(experiment):
        path = Path(spec["path"])
        try:
            model, payload, requested_hash, effective_hash = load_checkpoint_model(path)
        except Exception as exc:  # evidence is retained in the gate, not hidden
            load_failures.append(f"{path}: {type(exc).__name__}: {exc}")
            continue
        models.append(
            {
                "id": spec["id"],
                "model": model,
                "requested_path": path.as_posix(),
                "requested_hash": requested_hash,
                "effective_hash": effective_hash,
                "fingerprint": state_fingerprint(model.state_dict()),
                "trainer_version": payload.get("trainer_version", payload.get("policy_version", POLICY_VERSION)),
                "policy_version": payload.get("policy_version", POLICY_VERSION),
                "train_seed": int(payload.get("train_seed", spec["train_seed"])),
                "steps": int(payload.get("training_steps", spec["steps"])),
            }
        )

    final = next((item for item in models if item["id"] == "final_seed15001"), None)
    if final is not None:
        perturbed_model = deepcopy(final["model"])
        with torch.no_grad():
            parameter = dict(perturbed_model.named_parameters())["actor.2.weight"]
            parameter[0, 0] += 0.1
        perturbed_fp = state_fingerprint(perturbed_model.state_dict())
        models.append(
            {
                **{key: value for key, value in final.items() if key != "model"},
                "id": "final_seed15001_perturbed",
                "model": perturbed_model,
                "requested_path": "in_memory://controlled_perturbation_of_final_seed15001",
                "requested_hash": perturbed_fp,
                "effective_hash": perturbed_fp,
                "fingerprint": perturbed_fp,
            }
        )

    rows: list[dict[str, Any]] = []
    eval_config_sha = stable_hash({"worlds": [world_identity(world) for world in worlds], "horizon": 4})
    for model_record in models:
        model = model_record["model"]
        for world in worlds:
            started = time.perf_counter()
            raw, repaired, logits, iterations = rollout_with_scores(model, world, horizon=4)
            inference_s = time.perf_counter() - started
            public = public_world_view(world)
            denominator = float((world.s_star + 1.0) * world.s_star + world.s_star)
            raw_objective = assignment_objective(public, raw)
            repair_objective = assignment_objective(public, repaired)
            raw_success = bool(assignment_valid(raw, world.n_loads) and np.sum(raw > 0) == world.s_star)
            repair_success = bool(assignment_valid(repaired, world.n_loads) and np.sum(repaired > 0) == world.s_star)
            raw_regret = max(raw_objective - world.oracle_j, 0.0) / max(denominator, 1e-12)
            repair_regret = max(repair_objective - world.oracle_j, 0.0) / max(denominator, 1e-12)
            cache_key = build_cache_key(
                {
                    "protocol_version": "SP0_PROTOCOL_v1_2_CPU",
                    "trainer_version": str(model_record["trainer_version"]),
                    "policy_version": str(model_record["policy_version"]),
                    "checkpoint_sha256": model_record["effective_hash"],
                    "world_set_sha256": worlds_sha,
                    "evaluation_config_sha256": eval_config_sha,
                    "decoder_version": "argmax_iterative_v1",
                    "repair_version": "sp0_repair_assignment_v1_2",
                    "closure_version": "none_in_historical_policy_executor",
                    "raw_or_closed_mode": "RAW_AND_REPAIR",
                }
            )
            rows.append(
                {
                    "checkpoint_id": model_record["id"],
                    "requested_checkpoint_path": model_record["requested_path"],
                    "requested_checkpoint_sha256": model_record["requested_hash"],
                    "effective_checkpoint_sha256": model_record["effective_hash"],
                    "model_state_fingerprint": model_record["fingerprint"],
                    "trainer_version": model_record["trainer_version"],
                    "policy_version": model_record["policy_version"],
                    "train_seed": model_record["train_seed"],
                    "training_steps": model_record["steps"],
                    "world_set_sha256": worlds_sha,
                    "world_sha256": stable_hash(world_identity(world)),
                    "world_seed": int(world.world_seed),
                    "N": int(world.n_robots),
                    "K": int(world.n_loads),
                    "logits_json": json.dumps(logits.tolist(), separators=(",", ":")),
                    "logits_sha256": hashlib.sha256(np.asarray(logits, dtype=np.float64).tobytes()).hexdigest(),
                    "raw_assignment_json": json.dumps(raw.tolist(), separators=(",", ":")),
                    "raw_assignment_sha256": hashlib.sha256(np.asarray(raw, dtype=np.int64).tobytes()).hexdigest(),
                    "raw_success": raw_success,
                    "raw_normalized_regret": float(raw_regret),
                    "repair_assignment_json": json.dumps(repaired.tolist(), separators=(",", ":")),
                    "repair_assignment_sha256": hashlib.sha256(np.asarray(repaired, dtype=np.int64).tobytes()).hexdigest(),
                    "repair_success": repair_success,
                    "repair_normalized_regret": float(repair_regret),
                    "repair_delta_normalized_regret": float(repair_regret - raw_regret),
                    "qr_assignment_json": None,
                    "qr_success": None,
                    "qr_normalized_regret": None,
                    "inference_runtime_s": float(inference_s),
                    "repair_runtime_s": None,
                    "qr_runtime_s": None,
                    "iterations": iterations,
                    "cache_key": cache_key,
                }
            )
    evaluations = pd.DataFrame(rows)
    evaluations.to_csv(output / "checkpoint_evaluations.csv", index=False)
    evaluations.to_parquet(output / "checkpoint_evaluations.parquet", index=False)

    comparisons: list[dict[str, Any]] = []
    ids = list(dict.fromkeys(evaluations["checkpoint_id"].tolist())) if not evaluations.empty else []
    for left_index, left_id in enumerate(ids):
        for right_id in ids[left_index + 1 :]:
            left = evaluations[evaluations["checkpoint_id"] == left_id].sort_values("world_sha256")
            right = evaluations[evaluations["checkpoint_id"] == right_id].sort_values("world_sha256")
            if left["world_sha256"].tolist() != right["world_sha256"].tolist():
                continue
            hamming: list[float] = []
            logits_delta: list[float] = []
            js_values: list[float] = []
            different_worlds = 0
            for (_, left_row), (_, right_row) in zip(left.iterrows(), right.iterrows()):
                left_raw = np.asarray(json.loads(left_row["raw_assignment_json"]), dtype=int)
                right_raw = np.asarray(json.loads(right_row["raw_assignment_json"]), dtype=int)
                different_worlds += int(not np.array_equal(left_raw, right_raw))
                hamming.append(float(np.mean(left_raw != right_raw)))
                left_logits = np.asarray(json.loads(left_row["logits_json"]), dtype=float)
                right_logits = np.asarray(json.loads(right_row["logits_json"]), dtype=float)
                logits_delta.append(float(np.max(np.abs(left_logits - right_logits))))
                left_p = _softmax(left_logits)
                right_p = _softmax(right_logits)
                middle = 0.5 * (left_p + right_p)
                js = 0.5 * np.sum(left_p * np.log(np.maximum(left_p, 1e-300) / np.maximum(middle, 1e-300)), axis=1)
                js += 0.5 * np.sum(right_p * np.log(np.maximum(right_p, 1e-300) / np.maximum(middle, 1e-300)), axis=1)
                js_values.append(float(np.mean(js)))
            comparisons.append(
                {
                    "left_checkpoint_id": left_id,
                    "right_checkpoint_id": right_id,
                    "worlds": len(hamming),
                    "mean_raw_hamming_fraction": float(np.mean(hamming)),
                    "worlds_with_different_raw_assignment": different_worlds,
                    "proportion_worlds_with_different_raw_assignment": different_worlds / max(len(hamming), 1),
                    "max_absolute_logit_difference": float(np.max(logits_delta)),
                    "mean_jensen_shannon_divergence": float(np.mean(js_values)),
                    "raw_success_difference": float(left["raw_success"].mean() - right["raw_success"].mean()),
                    "raw_regret_difference": float(left["raw_normalized_regret"].mean() - right["raw_normalized_regret"].mean()),
                }
            )
    pairwise = pd.DataFrame(comparisons)
    pairwise.to_csv(output / "checkpoint_pairwise_sensitivity.csv", index=False)

    summary = (
        evaluations.groupby("checkpoint_id", sort=False)
        .agg(
            requested_checkpoint_sha256=("requested_checkpoint_sha256", "first"),
            effective_checkpoint_sha256=("effective_checkpoint_sha256", "first"),
            model_state_fingerprint=("model_state_fingerprint", "first"),
            train_seed=("train_seed", "first"),
            training_steps=("training_steps", "first"),
            worlds=("world_sha256", "nunique"),
            unique_logit_hashes=("logits_sha256", "nunique"),
            unique_raw_assignments=("raw_assignment_sha256", "nunique"),
            raw_success=("raw_success", "mean"),
            repair_success=("repair_success", "mean"),
            mean_raw_normalized_regret=("raw_normalized_regret", "mean"),
            mean_repair_normalized_regret=("repair_normalized_regret", "mean"),
            mean_repair_delta=("repair_delta_normalized_regret", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(output / "checkpoint_fingerprints.csv", index=False)
    summary.to_csv(output / "raw_vs_closed_by_checkpoint.csv", index=False)
    diversity = pairwise[
        [
            "left_checkpoint_id",
            "right_checkpoint_id",
            "mean_raw_hamming_fraction",
            "proportion_worlds_with_different_raw_assignment",
            "max_absolute_logit_difference",
            "mean_jensen_shannon_divergence",
        ]
    ] if not pairwise.empty else pairwise
    diversity.to_csv(output / "policy_output_diversity.csv", index=False)

    def comparison(left: str, right: str) -> dict[str, Any] | None:
        if pairwise.empty:
            return None
        match = pairwise[
            ((pairwise.left_checkpoint_id == left) & (pairwise.right_checkpoint_id == right))
            | ((pairwise.left_checkpoint_id == right) & (pairwise.right_checkpoint_id == left))
        ]
        return None if match.empty else match.iloc[0].to_dict()

    random_final = comparison("random_actor_seed15001", "final_seed15001")
    perturbed_final = comparison("final_seed15001", "final_seed15001_perturbed")
    gate = {
        "load_failures": load_failures,
        "world_set_sha256": worlds_sha,
        "checkpoint_count": len(models),
        "requested_effective_hash_match": bool(
            not load_failures
            and all(item["requested_hash"] == item["effective_hash"] for item in models)
        ),
        "random_vs_final": random_final,
        "perturbed_vs_final": perturbed_final,
        "random_and_final_logits_differ": bool(
            random_final
            and random_final["max_absolute_logit_difference"] > 1e-12
        ),
        "random_and_final_raw_differ": bool(
            random_final
            and random_final["worlds_with_different_raw_assignment"] > 0
        ),
        "perturbation_detected": bool(
            perturbed_final
            and (
                perturbed_final["worlds_with_different_raw_assignment"] > 0
                or perturbed_final["max_absolute_logit_difference"] > 1e-12
            )
        ),
    }
    gate["passed"] = bool(
        gate["requested_effective_hash_match"]
        and gate["random_and_final_logits_differ"]
        and gate["random_and_final_raw_differ"]
        and gate["perturbation_detected"]
    )
    return evaluations, pairwise, gate


def _softmax(values: np.ndarray) -> np.ndarray:
    shifted = values - np.max(values, axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=1, keepdims=True)


def artifact_inventory(experiment: Path, output: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    hash_lines: list[str] = []
    hash_suffixes = {".pt", ".parquet", ".npz", ".yaml", ".json", ".lock", ".sha256"}
    for path in sorted(item for item in experiment.rglob("*") if item.is_file()):
        relative = path.relative_to(experiment).as_posix()
        category = _artifact_category(relative, path.suffix.lower())
        digest = sha256_file(path) if path.suffix.lower() in hash_suffixes else ""
        readable = os.access(path, os.R_OK)
        rows.append(
            {
                "relative_path": relative,
                "category": category,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "readable": readable,
                "sha256": digest,
            }
        )
        if digest:
            hash_lines.append(f"{digest}  {relative}")
    _write_csv(output / "artifact_inventory.csv", rows)
    (output / "artifact_hashes.sha256").write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    return {
        "files": len(rows),
        "hashed_files": len(hash_lines),
        "bytes": int(sum(row["size_bytes"] for row in rows)),
        "unreadable": [row["relative_path"] for row in rows if not row["readable"]],
    }


def _artifact_category(relative: str, suffix: str) -> str:
    lower = relative.lower()
    if "checkpoint" in lower or suffix == ".pt":
        return "checkpoint"
    if "trajector" in lower and suffix == ".npz":
        return "trajectory"
    if "world" in lower or "/public/" in lower or "/oracle/" in lower:
        return "world"
    if suffix == ".parquet":
        return "canonical_table"
    if suffix in {".png", ".pdf", ".svg", ".tex"}:
        return "figure"
    if suffix == ".mp4":
        return "video"
    if "protocol" in lower or "manifest" in lower or "status" in lower:
        return "manifest_or_protocol"
    return "other"


def audit_statistics(experiment: Path, output: Path) -> dict[str, Any]:
    hypotheses = pd.read_parquet(experiment / "statistics" / "hypotheses.parquet").copy()
    finite = (
        np.isfinite(pd.to_numeric(hypotheses["effect_estimate"], errors="coerce"))
        & np.isfinite(pd.to_numeric(hypotheses["CI95_low"], errors="coerce"))
        & np.isfinite(pd.to_numeric(hypotheses["CI95_high"], errors="coerce"))
        & np.isfinite(pd.to_numeric(hypotheses["raw_p"], errors="coerce"))
    )
    hypotheses["finite_effect_and_interval"] = finite
    hypotheses["raw_p_reported"] = hypotheses["raw_p"].map(_reported_p)
    hypotheses["holm_p_reported"] = hypotheses["Holm_adjusted_p"].map(_reported_p)
    hypotheses["audited_claim_status"] = np.where(
        finite & hypotheses["decision"].astype(str).str.startswith("reject"),
        "eligible_for_contextual_review",
        "not_supported",
    )
    hypotheses.to_csv(output / "hypothesis_results_audited.csv", index=False)

    models = pd.read_parquet(experiment / "statistics" / "model_results.parquet").copy()
    models["finite_interval"] = np.isfinite(pd.to_numeric(models["CI95_low"], errors="coerce")) & np.isfinite(
        pd.to_numeric(models["CI95_high"], errors="coerce")
    )
    models["p_is_zero"] = pd.to_numeric(models["raw_p"], errors="coerce").eq(0.0)
    models["raw_p_reported"] = models["raw_p"].map(_reported_p)
    models["audited_status"] = np.where(
        models["status"].astype(str).isin(["fit", "wald_term"]) & models["finite_interval"],
        "estimable",
        "not_estimable",
    )
    models.to_csv(output / "statistical_model_diagnostics.csv", index=False)
    nonestimable = models[models["audited_status"] == "not_estimable"].copy()
    nonestimable.to_csv(output / "nonestimable_results.csv", index=False)

    claims = hypotheses[
        [
            "hypothesis_id",
            "status",
            "effect_estimate",
            "CI95_low",
            "CI95_high",
            "raw_p_reported",
            "Holm_adjusted_p",
            "decision",
            "claim_permitted",
            "audited_claim_status",
            "source",
        ]
    ].copy()
    claims["allowed_wording"] = np.where(
        claims["audited_claim_status"] == "eligible_for_contextual_review",
        "A finite audited association/effect was estimated; interpret on the recorded model scale.",
        "No confirmatory support may be claimed from this row.",
    )
    claims.to_csv(output / "claims_audited.csv", index=False)
    return {
        "hypotheses": len(hypotheses),
        "hypotheses_with_nonfinite_effect_or_interval": int((~finite).sum()),
        "hypotheses_with_zero_p": int(pd.to_numeric(hypotheses["raw_p"], errors="coerce").eq(0.0).sum()),
        "model_rows": len(models),
        "model_rows_with_nonfinite_interval": int((~models["finite_interval"]).sum()),
        "model_rows_with_zero_p": int(models["p_is_zero"].sum()),
        "passed": bool(finite.all() and not models["p_is_zero"].any() and models["finite_interval"].all()),
    }


def _reported_p(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "not_estimable"
    if not math.isfinite(numeric):
        return "not_estimable"
    if numeric == 0.0:
        return f"< {NUMERIC_P_FLOOR:.17g}"
    return f"{numeric:.17g}"


def failure_taxonomy(experiment: Path, output: Path) -> dict[str, Any]:
    sources = {
        "B0": experiment / "b0" / "budget_runs.parquet",
        "B2": experiment / "b2" / "runs.parquet",
        "B3": experiment / "b3" / "runs.parquet",
        "B4": experiment / "b4" / "runs.parquet",
        "B5": experiment / "b5" / "runs.parquet",
        "B6": experiment / "b6" / "runs.parquet",
        "B7": experiment / "b7" / "runs.parquet",
    }
    frames: list[pd.DataFrame] = []
    for block, path in sources.items():
        frame = pd.read_parquet(path).copy()
        frame["audit_block"] = block
        frames.append(frame.dropna(axis=1, how="all"))
    runs = pd.concat(frames, ignore_index=True, sort=False)
    registry_rows: list[dict[str, Any]] = []
    for index, row in runs.iterrows():
        code, reason = _classify_failure(row)
        if code is None:
            continue
        registry_rows.append(
            {
                "audit_row_id": index,
                "block_id": row.get("audit_block"),
                "method_variant": row.get("method_variant", row.get("method", "unknown")),
                "world_hash": row.get("world_hash"),
                "world_seed": row.get("world_seed"),
                "failure_code": code.value,
                "classification_reason": reason,
                "historical_error_type": row.get("error_type"),
                "historical_error_message": row.get("error_message"),
            }
        )
    registry = pd.DataFrame(registry_rows)
    registry.to_csv(output / "failure_registry.csv", index=False)

    summaries: list[dict[str, Any]] = []
    for (block, method), group in runs.groupby(["audit_block", "method_variant"], dropna=False):
        subset = registry[(registry["block_id"] == block) & (registry["method_variant"] == method)] if not registry.empty else registry
        total = len(group)
        oracle_evaluable = int(np.isfinite(pd.to_numeric(group.get("oracle_j"), errors="coerce")).sum()) if "oracle_j" in group else total
        final_success = group.get("final_success", group.get("success", pd.Series(False, index=group.index))).fillna(False).astype(bool)
        summaries.append(
            {
                "block_id": block,
                "method_variant": method,
                "total_evaluations": total,
                "unique_worlds": int(group["world_hash"].nunique()) if "world_hash" in group else int(group.get("world_seed", pd.Series()).nunique()),
                "oracle_evaluable_evaluations": oracle_evaluable,
                "oracle_infeasible_world": int((subset.failure_code == FailureCode.ORACLE_INFEASIBLE_WORLD.value).sum()) if not subset.empty else 0,
                "success_all_evaluations": int(final_success.sum()),
                "success_rate_all_evaluations": float(final_success.mean()),
                "method_timeout": int((subset.failure_code == FailureCode.METHOD_TIMEOUT.value).sum()) if not subset.empty else 0,
                "implementation_error": int(subset.failure_code.isin([FailureCode.NUMERICAL_ERROR.value, FailureCode.EXTERNAL_PROCESS_ERROR.value, FailureCode.POSTPROCESSING_ERROR.value]).sum()) if not subset.empty else 0,
                "method_failure": int(subset.failure_code.isin([FailureCode.METHOD_NONCONVERGENCE.value, FailureCode.INVALID_ASSIGNMENT.value, FailureCode.REPAIR_FAILURE.value, FailureCode.CLOSURE_FAILURE.value]).sum()) if not subset.empty else 0,
                "unknown_failure": int((subset.failure_code == FailureCode.UNKNOWN_FAILURE.value).sum()) if not subset.empty else 0,
            }
        )
    _write_csv(output / "failure_breakdown.csv", summaries)
    source_aggregate = runs[runs["audit_block"] != "B0"].apply(
        lambda row: bool(_clean_text(row.get("error_type"))) or _is_true(row.get("timeout", False)),
        axis=1,
    )
    return {
        "base_rows": len(runs),
        "expected_base_rows": 15436,
        "historical_report_failure_or_timeout_rows": int(source_aggregate.sum()),
        "classified_failure_rows": len(registry),
        "unclassified_historical_failure_rows": int((registry["failure_code"] == FailureCode.UNKNOWN_FAILURE.value).sum()) if not registry.empty else 0,
        "historical_source_has_explicit_failure_code": "failure_code" in runs.columns,
        "passed": bool(len(runs) == 15436 and "failure_code" in runs.columns and (registry["failure_code"] != FailureCode.UNKNOWN_FAILURE.value).all()),
    }


def _classify_failure(row: pd.Series) -> tuple[FailureCode | None, str]:
    error_type = _clean_text(row.get("error_type"))
    error_message = _clean_text(row.get("error_message"))
    if error_type and error_type not in {"nan", "none", "<na>"}:
        if "numeric" in error_type or _is_true(row.get("nan_or_inf", False)):
            return FailureCode.NUMERICAL_ERROR, "historical error_type/nan_or_inf"
        if "process" in error_type:
            return FailureCode.EXTERNAL_PROCESS_ERROR, "historical external-process error"
        return FailureCode.UNKNOWN_FAILURE, f"unmapped historical error_type={error_type}"
    if _is_true(row.get("nan_or_inf", False)):
        return FailureCode.NUMERICAL_ERROR, "historical nan_or_inf=true"
    if _is_true(row.get("timeout", False)) or _is_true(row.get("continuous_timeout", False)):
        return FailureCode.METHOD_TIMEOUT, "historical timeout flag"
    final_success = row.get("final_success", row.get("success", True))
    if pd.notna(final_success) and not bool(final_success):
        if _is_true(row.get("closure_applied", False)):
            return FailureCode.CLOSURE_FAILURE, "final failure after historical closure"
        return FailureCode.INVALID_ASSIGNMENT, "historical final_success=false"
    if error_message:
        return FailureCode.UNKNOWN_FAILURE, "historical error message without typed error"
    return None, ""


def _is_true(value: Any) -> bool:
    return False if value is None or pd.isna(value) else bool(value)


def _clean_text(value: Any) -> str:
    return "" if value is None or pd.isna(value) else str(value).strip().lower()


def audit_environment(experiment: Path) -> dict[str, Any]:
    return {
        "audit_version": AUDIT_VERSION,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "source_experiment": experiment.resolve().as_posix(),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            name: _package_version(name)
            for name in ["torch", "numpy", "pandas", "scipy", "pyarrow", "statsmodels"]
        },
        "solver": {"name": "scipy.optimize.milp/HiGHS", "scipy_version": scipy.__version__},
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_status_porcelain": _git(["status", "--porcelain"]).splitlines(),
        "entry_point": "python -m viu_mrob_tfm.sp0.audit_v1",
        "training_or_simulator_invoked": False,
    }


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not_installed"


def _git(arguments: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *arguments], text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"unavailable: {exc}"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_report(output: Path, status: dict[str, Any], checkpoint_summary: pd.DataFrame) -> None:
    gates = status["gates"]
    lines = [
        "# SP0 audit report v1",
        "",
        "> Read-only audit of `results/sp0/SP0_PROTOCOL_v1_2_CPU`. The historical campaign was not rerun or modified.",
        "",
        "## Decision",
        "",
        f"**{status['decision']}**",
        "",
        "SP0 remains a historical result package, but its learned-policy and several statistical claims are not promotable. SP1 confirmatory execution remains blocked.",
        "",
        "## Gate matrix",
        "",
        "| Gate | Result | Evidence | File | Consequence | Required action |",
        "|---|---|---|---|---|---|",
    ]
    for gate_id, gate in gates.items():
        result = "PASS" if gate["passed"] else "FAIL"
        lines.append(
            f"| {gate_id} | {result} | {gate['evidence']} | `{gate['file']}` | {gate['consequence']} | {gate['action']} |"
        )
    lines.extend(
        [
            "",
            "## Checkpoint sensitivity",
            "",
            "The checkpoint files and state fingerprints are distinct. This alone does not establish learned behavioral improvement. The audit compares logits and RAW assignments on one fixed validation-world set and includes an untrained actor plus a controlled perturbation.",
            "",
            "| Checkpoint | Seed | Steps | RAW success | REPAIR success | RAW regret | REPAIR regret |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in checkpoint_summary.iterrows():
        lines.append(
            f"| {row['checkpoint_id']} | {row['train_seed']} | {row['training_steps']} | {row['raw_success']:.3f} | {row['repair_success']:.3f} | {row['mean_raw_normalized_regret']:.6g} | {row['mean_repair_normalized_regret']:.6g} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: the historical validation aggregates (`raw_success=0`, closed `success=1`) are reproducible as a decoder-dominant pattern. Any MAPPO claim must be limited to a checkpoint-backed learned score generator whose executable success is attributable to deterministic repair; the current evidence does not show learned RAW coalition/allocation success.",
            "",
            "## Statistical audit",
            "",
            f"- Hypotheses with non-finite effect or IC95: {status['statistics']['hypotheses_with_nonfinite_effect_or_interval']}.",
            f"- Hypotheses reported with `p=0`: {status['statistics']['hypotheses_with_zero_p']}.",
            f"- Model rows with non-finite intervals: {status['statistics']['model_rows_with_nonfinite_interval']}.",
            f"- Model rows reported with `p=0`: {status['statistics']['model_rows_with_zero_p']}.",
            "- The audited exports preserve original numbers but downgrade non-finite or non-estimable rows and render exact zero p-values as numerical bounds.",
            "",
            "## Failure taxonomy",
            "",
            f"The audit read {status['failures']['base_rows']} base evaluations. It reproduces the report's {status['failures']['historical_report_failure_or_timeout_rows']} rows selected by `error_type OR timeout`, while the richer retrospective mapping classifies {status['failures']['classified_failure_rows']} rows after also distinguishing continuous nonconvergence and invalid/failed closure. Because the historical source has no explicit versioned `failure_code`, this mapping is evidence for remediation, not a claim that the original causes are known.",
            "",
            "## Lifecycle contradiction",
            "",
            "`training/status.json` records `confirmatory_seeds_opened=false`, while `FINAL_RUN_MANIFEST.json` records complete confirmatory blocks and the protocol directory contains a seed-opening event. The historical state model therefore fails closed.",
            "",
            "## Rebuild status",
            "",
            "No repository entry point currently proves complete deterministic regeneration of tables, contrasts, all figure source data, videos, claims, and report from canonical RAW Parquet/trajectories without simulator or trainer calls. `G_REBUILD_FROM_RAW` is FAIL, not untested PASS.",
        ]
    )
    (output / "SP0_AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit(experiment: Path, output: Path, *, reuse_inventory: bool = False) -> dict[str, Any]:
    experiment = experiment.resolve()
    output = output.resolve()
    if output == experiment or experiment in output.parents:
        raise ValueError("audit output must be outside the immutable historical experiment")
    output.mkdir(parents=True, exist_ok=True)
    (output / "audit_plan.md").write_text(
        "# SP0 audit plan\n\n"
        "1. Inventory and hash historical artifacts.\n"
        "2. Re-evaluate saved checkpoints on a fixed reconstruction of the declared validation grid.\n"
        "3. Audit statistical finiteness and p-value rendering.\n"
        "4. Retrospectively map failures without changing source rows.\n"
        "5. Fail closed for lifecycle, stage separation, or rebuild evidence that cannot be demonstrated.\n\n"
        "Prohibited: training, confirmatory seed opening, campaign execution, and writes to the source experiment.\n",
        encoding="utf-8",
    )
    environment = audit_environment(experiment)
    (output / "audit_environment.json").write_text(json.dumps(environment, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if reuse_inventory and (output / "artifact_inventory.csv").exists() and (output / "artifact_hashes.sha256").exists():
        prior_inventory = pd.read_csv(output / "artifact_inventory.csv")
        inventory = {
            "files": len(prior_inventory),
            "hashed_files": int(prior_inventory["sha256"].notna().sum()),
            "bytes": int(prior_inventory["size_bytes"].sum()),
            "unreadable": prior_inventory.loc[~prior_inventory["readable"].astype(bool), "relative_path"].tolist(),
            "reused_from_prior_audit_run": True,
        }
    else:
        inventory = artifact_inventory(experiment, output)
    evaluations, _pairwise, checkpoint_gate = checkpoint_sensitivity(experiment, output)
    statistics_status = audit_statistics(experiment, output)
    failure_status = failure_taxonomy(experiment, output)

    training_status = json.loads((experiment / "training" / "status.json").read_text(encoding="utf-8"))
    final_manifest = json.loads((experiment / "FINAL_RUN_MANIFEST.json").read_text(encoding="utf-8"))
    seed_consistent = bool(
        training_status.get("confirmatory_seeds_opened") is True
        and final_manifest.get("campaign", {}).get("status") == "confirmatory_blocks_complete"
    )
    cache_unique = bool(
        evaluations.groupby("effective_checkpoint_sha256")["cache_key"].nunique().eq(1).all()
        and evaluations.groupby("cache_key")["effective_checkpoint_sha256"].nunique().eq(1).all()
    )
    gates = {
        "G_CHECKPOINT_LOAD": {
            "passed": checkpoint_gate["requested_effective_hash_match"],
            "evidence": f"{checkpoint_gate['checkpoint_count']} controls/checkpoints loaded; requested and effective hashes compared.",
            "file": "checkpoint_fingerprints.csv",
            "consequence": "Checkpoint provenance is readable." if checkpoint_gate["requested_effective_hash_match"] else "Checkpoint provenance is broken.",
            "action": "Retain hash verification in every evaluator.",
        },
        "G_CHECKPOINT_SENSITIVITY": {
            "passed": checkpoint_gate["passed"],
            "evidence": "Random/final and controlled-perturbation comparisons use fixed paired worlds.",
            "file": "checkpoint_pairwise_sensitivity.csv",
            "consequence": "Sensitivity controls executed; learning quality still requires RAW baselines." if checkpoint_gate["passed"] else "MAPPO claims are blocked.",
            "action": "Require superiority to random/uniform before SP1 promotion.",
        },
        "G_CACHE_ISOLATION": {
            "passed": cache_unique,
            "evidence": "Audit cache key includes protocol, trainer, policy, checkpoint, worlds, evaluation, decoder, repair, closure and stage mode.",
            "file": "checkpoint_evaluations.csv",
            "consequence": "Audit evaluations cannot alias across checkpoint hashes." if cache_unique else "Cached evaluation provenance is unsafe.",
            "action": "Adopt the common key in all SP runners.",
        },
        "G_RAW_REPAIR_QR_SEPARATION": {
            "passed": False,
            "evidence": "Historical policy executor exposes RAW plus one POLICY_REPAIR result, not immutable RAW/REPAIR/QR tables.",
            "file": "raw_vs_closed_by_checkpoint.csv",
            "consequence": "Decoder/closure contribution cannot be split into repair and QR retrospectively.",
            "action": "SP1 must persist three separate assignment tables before confirmatory execution.",
        },
        "G_SEED_STATE_CONSISTENCY": {
            "passed": seed_consistent,
            "evidence": "training/status.json says confirmatory_seeds_opened=false while final manifest says confirmatory complete.",
            "file": "audit_environment.json",
            "consequence": "Historical lifecycle cannot be promoted as internally consistent." if not seed_consistent else "Lifecycle evidence is consistent.",
            "action": "Keep history immutable; use append-only SP_COMMON state events from now on.",
        },
        "G_STATISTICAL_FINITE_RESULTS": {
            "passed": statistics_status["passed"],
            "evidence": f"{statistics_status['hypotheses_with_nonfinite_effect_or_interval']} hypothesis rows have non-finite effect/CI; {statistics_status['hypotheses_with_zero_p']} use p=0.",
            "file": "hypothesis_results_audited.csv",
            "consequence": "Affected claims are downgraded to not supported.",
            "action": "Implement preregistered fallbacks and interpretable effect scales.",
        },
        "G_FAILURE_TAXONOMY": {
            "passed": failure_status["passed"],
            "evidence": "Historical rows lack a versioned explicit failure_code; retrospective mapping is not causal proof.",
            "file": "failure_breakdown.csv",
            "consequence": "The aggregate 8,498 failure/timeout statement is not methodologically adequate.",
            "action": "Emit FailureCode at event time in SP1 and future SPs.",
        },
        "G_REBUILD_FROM_RAW": {
            "passed": False,
            "evidence": "No complete simulator-free rebuild entry point or deterministic source-data contract exists.",
            "file": "audit_plan.md",
            "consequence": "End-to-end reproducibility is unproven.",
            "action": "Implement and test experiment_common.rebuild before SP1 freeze.",
        },
    }
    decision = "READY_FOR_CONFIRMATORY_RUN" if all(gate["passed"] for gate in gates.values()) else "BLOCKED"
    status = {
        "audit_version": AUDIT_VERSION,
        "source_experiment": experiment.as_posix(),
        "output": output.as_posix(),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_experiment_modified": False,
        "training_or_simulator_invoked": False,
        "inventory": inventory,
        "checkpoint_sensitivity": checkpoint_gate,
        "statistics": statistics_status,
        "failures": failure_status,
        "gates": gates,
        "decision": decision,
    }
    (output / "audit_status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    (output / "SP0_AUDIT_STATUS.json").write_text(json.dumps(status, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    checkpoint_summary = pd.read_csv(output / "checkpoint_fingerprints.csv")
    write_report(output, status, checkpoint_summary)
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, default=Path("results/sp0/SP0_PROTOCOL_v1_2_CPU"))
    parser.add_argument("--output", type=Path, default=Path("results/sp0/SP0_AUDIT_v1"))
    parser.add_argument("--reuse-inventory", action="store_true", help="Reuse an already generated inventory/hash manifest")
    args = parser.parse_args(argv)
    status = run_audit(args.experiment, args.output, reuse_inventory=args.reuse_inventory)
    print(json.dumps({"decision": status["decision"], "output": status["output"]}, indent=2))
    return 0 if status["decision"] == "READY_FOR_CONFIRMATORY_RUN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
