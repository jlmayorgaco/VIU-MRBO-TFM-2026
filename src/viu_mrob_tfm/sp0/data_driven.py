"""Real checkpoint-backed IPPO/MAPPO-GNN utilities for SP0.

The module deliberately avoids Hungarian/oracle data. Rewards are computed from
the current assignment objective only, and inference receives a public world
view with costs, masks and communication graph data.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical

from viu_mrob_tfm.sp0.methods import SP0MethodResult, assignment_objective, assignment_valid, greedy_assignment, repair_assignment
from viu_mrob_tfm.sp0.scenario import SP0World, make_sp0_world, public_world_view
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


POLICY_VERSION = "sp0_gnn_ppo_v1_2_cpu_batched"


@dataclass(frozen=True, slots=True)
class SP0PolicyBatch:
    robot_features: torch.Tensor
    action_features: torch.Tensor
    adjacency: torch.Tensor
    action_mask: torch.Tensor
    global_features: torch.Tensor


@dataclass(slots=True)
class PPOTransition:
    world: Any
    previous_actions: np.ndarray
    actions: np.ndarray
    old_log_probs: np.ndarray
    old_values: np.ndarray
    reward: float
    return_value: float = 0.0
    advantages: np.ndarray | None = None


class SP0GNNActorCritic(nn.Module):
    """Shared local GNN actor with IPPO-local or MAPPO-centralized value head."""

    def __init__(self, hidden_dim: int = 64, critic_global: bool = False, gnn_layers: int = 2) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.critic_global = bool(critic_global)
        self.gnn_layers = int(gnn_layers)
        self.robot_encoder = nn.Sequential(nn.Linear(6, self.hidden_dim), nn.Tanh())
        self.self_layers = nn.ModuleList(nn.Linear(self.hidden_dim, self.hidden_dim) for _ in range(self.gnn_layers))
        self.neighbor_layers = nn.ModuleList(nn.Linear(self.hidden_dim, self.hidden_dim) for _ in range(self.gnn_layers))
        self.action_encoder = nn.Sequential(nn.Linear(7, self.hidden_dim), nn.Tanh())
        self.actor = nn.Sequential(
            nn.Linear(2 * self.hidden_dim, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, 1),
        )
        self.local_value = nn.Sequential(
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, 1),
        )
        self.global_value = nn.Sequential(
            nn.Linear(self.hidden_dim + 6, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, 1),
        )

    def encode_robots(self, batch: SP0PolicyBatch) -> torch.Tensor:
        h = self.robot_encoder(batch.robot_features)
        adjacency = batch.adjacency
        degree = adjacency.sum(dim=-1, keepdim=True).clamp_min(1.0)
        for self_layer, neighbor_layer in zip(self.self_layers, self.neighbor_layers):
            neighbor_h = adjacency @ h / degree
            h = torch.tanh(self_layer(h) + neighbor_layer(neighbor_h))
        return h

    def _actor_from_encoded(self, batch: SP0PolicyBatch, h: torch.Tensor) -> torch.Tensor:
        action_h = self.action_encoder(batch.action_features)
        robot_h = h.unsqueeze(-2).expand(*h.shape[:-1], action_h.shape[-2], h.shape[-1])
        logits = self.actor(torch.cat([robot_h, action_h], dim=-1)).squeeze(-1)
        return logits.masked_fill(~batch.action_mask, -1.0e9)

    def _critic_from_encoded(self, batch: SP0PolicyBatch, h: torch.Tensor) -> torch.Tensor:
        if self.critic_global:
            pooled = h.mean(dim=-2)
            scalar = self.global_value(torch.cat([pooled, batch.global_features], dim=-1)).squeeze(-1)
            return scalar.unsqueeze(-1).expand(*h.shape[:-1]) if h.ndim == 3 else scalar.expand(h.shape[0])
        return self.local_value(h).squeeze(-1)

    def actor_logits(self, batch: SP0PolicyBatch) -> torch.Tensor:
        """Decentralized actor path; it never consumes batch.global_features."""

        return self._actor_from_encoded(batch, self.encode_robots(batch))

    def critic_values(self, batch: SP0PolicyBatch) -> torch.Tensor:
        return self._critic_from_encoded(batch, self.encode_robots(batch))

    def forward(self, batch: SP0PolicyBatch) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.encode_robots(batch)
        return self._actor_from_encoded(batch, h), self._critic_from_encoded(batch, h)

def build_policy_batch(
    world: Any,
    *,
    previous_actions: np.ndarray | None = None,
    device: str | torch.device = "cpu",
) -> SP0PolicyBatch:
    """Build graph-local actor inputs; global features are consumed only by MAPPO's critic."""

    n, k = world.n_robots, world.n_loads
    previous = (
        np.zeros(n, dtype=int)
        if previous_actions is None
        else np.asarray(previous_actions, dtype=int).copy()
    )
    if previous.shape != (n,) or np.any(previous < 0) or np.any(previous > k):
        raise ValueError("previous_actions must contain one valid action per robot")
    cost = np.concatenate([np.zeros((n, 1), dtype=float), np.asarray(world.cost, dtype=float)], axis=1)
    adjacency = np.asarray(world.adjacency, dtype=float)
    degree = np.sum(adjacency, axis=1, keepdims=True)
    neighbor_denom = np.maximum(degree, 1.0)
    neighbor_cost = (adjacency @ cost) / neighbor_denom

    one_hot = np.eye(k + 1, dtype=float)[previous]
    closed_neighborhood = adjacency + np.eye(n, dtype=float)
    neighborhood_size = np.sum(closed_neighborhood, axis=1, keepdims=True)
    local_occupancy = (closed_neighborhood @ one_hot) / np.maximum(neighborhood_size, 1.0)

    robot_features = np.stack(
        [
            np.mean(cost[:, 1:], axis=1),
            np.min(cost[:, 1:], axis=1),
            np.std(cost[:, 1:], axis=1),
            degree[:, 0] / max(n - 1, 1),
            np.full(n, n / 64.0, dtype=float),
            np.full(n, k / 96.0, dtype=float),
        ],
        axis=-1,
    )
    load_index = np.repeat((np.arange(k + 1, dtype=float)[None, :] / max(k, 1)), n, axis=0)
    idle = np.zeros((n, k + 1), dtype=float)
    idle[:, 0] = 1.0
    action_features = np.stack(
        [
            cost,
            neighbor_cost,
            local_occupancy,
            one_hot,
            load_index,
            idle,
            np.repeat(degree / max(n - 1, 1), k + 1, axis=1),
        ],
        axis=-1,
    )
    positive = previous[previous > 0]
    unique_coverage = np.unique(positive).size / max(min(n, k), 1)
    duplicate_fraction = (positive.size - np.unique(positive).size) / max(n, 1)
    global_features = np.asarray(
        [
            n / 64.0,
            k / 96.0,
            float(np.mean(cost[:, 1:])),
            float(np.mean(degree) / max(n - 1, 1)),
            float(unique_coverage),
            float(duplicate_fraction),
        ],
        dtype=float,
    )
    return SP0PolicyBatch(
        robot_features=torch.as_tensor(robot_features, dtype=torch.float32, device=device),
        action_features=torch.as_tensor(action_features, dtype=torch.float32, device=device),
        adjacency=torch.as_tensor(adjacency, dtype=torch.float32, device=device),
        action_mask=torch.ones((n, k + 1), dtype=torch.bool, device=device),
        global_features=torch.as_tensor(global_features, dtype=torch.float32, device=device),
    )


def stack_policy_batches(batches: list[SP0PolicyBatch]) -> SP0PolicyBatch:
    """Stack equal-shape worlds for CPU-efficient PPO updates."""

    if not batches:
        raise ValueError("At least one policy batch is required")
    return SP0PolicyBatch(
        robot_features=torch.stack([batch.robot_features for batch in batches]),
        action_features=torch.stack([batch.action_features for batch in batches]),
        adjacency=torch.stack([batch.adjacency for batch in batches]),
        action_mask=torch.stack([batch.action_mask for batch in batches]),
        global_features=torch.stack([batch.global_features for batch in batches]),
    )


def assignment_reward(
    world: Any,
    labels: np.ndarray,
    previous_labels: np.ndarray | None = None,
    *,
    terminal: bool = True,
    switch_penalty: float = 0.001,
    invalid_action_penalty: float = 0.05,
    communication_penalty: float = 0.0,
) -> float:
    """Potential-difference reward computed without Hungarian or any oracle reference."""

    labels = np.asarray(labels, dtype=int)
    previous = np.zeros_like(labels) if previous_labels is None else np.asarray(previous_labels, dtype=int)
    normalization = float((world.s_star + 1.0) * world.s_star + world.s_star)
    current_j = assignment_objective(world, labels)
    previous_j = assignment_objective(world, previous)
    positive = labels[labels > 0]
    duplicates = int(positive.size - np.unique(positive).size)
    reward = -(current_j - previous_j) / max(normalization, 1.0e-12)
    reward -= float(switch_penalty) * float(np.mean(labels != previous))
    reward -= float(invalid_action_penalty) * duplicates / max(world.n_robots, 1)
    reward -= float(communication_penalty) * float(np.sum(world.adjacency)) / max(world.n_robots, 1)
    if terminal:
        reward -= current_j / max(normalization, 1.0e-12)
    return float(reward)


def raw_actions_from_logits(
    logits: torch.Tensor,
    *,
    stochastic: bool,
    seed: int | None,
) -> tuple[np.ndarray, torch.Tensor]:
    if stochastic:
        probabilities = torch.softmax(logits, dim=-1)
        if seed is None:
            actions = torch.multinomial(probabilities, 1).squeeze(-1)
        else:
            generator = torch.Generator(device=logits.device)
            generator.manual_seed(int(seed))
            actions = torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)
        log_probs = Categorical(logits=logits).log_prob(actions)
    else:
        actions = torch.argmax(logits, dim=-1)
        log_probs = torch.zeros(logits.shape[0], dtype=torch.float32, device=logits.device)
    return actions.detach().cpu().numpy().astype(int), log_probs


def policy_labels_from_logits(
    world: Any,
    logits: torch.Tensor,
    *,
    stochastic: bool,
    seed: int | None,
) -> tuple[np.ndarray, torch.Tensor]:
    raw, log_probs = raw_actions_from_logits(logits, stochastic=stochastic, seed=seed)
    repaired = repair_assignment(world, raw, None)
    return repaired.astype(int), log_probs.sum()


def deterministic_policy_rollout(
    model: SP0GNNActorCritic,
    world: Any,
    *,
    horizon: int,
    device: str | torch.device = "cpu",
) -> tuple[np.ndarray, np.ndarray, int, float]:
    previous = np.zeros(world.n_robots, dtype=int)
    iterations = 0
    model.eval()
    with torch.no_grad():
        for _ in range(max(1, int(horizon))):
            logits = model.actor_logits(build_policy_batch(world, previous_actions=previous, device=device))
            current, _log_probs = raw_actions_from_logits(logits, stochastic=False, seed=None)
            iterations += 1
            if np.array_equal(current, previous):
                break
            previous = current
    closure_start = time.perf_counter()
    repaired = repair_assignment(world, previous, None)
    closure_time_s = time.perf_counter() - closure_start
    return previous, repaired, iterations, closure_time_s

def run_checkpoint_policy(world: Any, spec: dict[str, Any]) -> SP0MethodResult:
    """Execute a final IPPO/MAPPO policy using only the public world view."""

    checkpoint_path = Path(str(spec.get("checkpoint_path", "")))
    if not checkpoint_path.exists():
        raise RuntimeError(f"real checkpoint not found: {checkpoint_path}")
    expected_hash = spec.get("checkpoint_hash")
    if expected_hash and sha256_file(checkpoint_path) != str(expected_hash):
        raise RuntimeError(f"checkpoint SHA-256 mismatch: {checkpoint_path}")
    started = time.perf_counter()
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    algorithm = str(payload.get("algorithm", spec.get("id", "IPPO-GNN")))
    hidden_dim = int(payload.get("hidden_dim", 64))
    gnn_layers = int(payload.get("gnn_layers", 2))
    model = SP0GNNActorCritic(
        hidden_dim=hidden_dim,
        critic_global=algorithm.upper().startswith("MAPPO"),
        gnn_layers=gnn_layers,
    )
    model.load_state_dict(payload["model_state_dict"])
    public = public_world_view(world) if isinstance(world, SP0World) else world
    raw, labels, iterations, closure_time_s = deterministic_policy_rollout(
        model,
        public,
        horizon=int(payload.get("inference_horizon", spec.get("inference_horizon", 4))),
    )
    runtime_s = time.perf_counter() - started
    messages_per_round = int(np.sum(public.adjacency))
    messages = messages_per_round * iterations
    matching_valid = assignment_valid(labels, public.n_loads)
    maximum_cardinality = bool(matching_valid and np.sum(labels > 0) == public.s_star)
    return SP0MethodResult(
        method_id=algorithm,
        method_family="data_driven",
        architecture="distributed_local",
        dynamic_id=None,
        fitness_id=None,
        rounding_id="POLICY_REPAIR",
        labels=labels,
        continuous_x=None,
        runtime_ms=runtime_s * 1000.0,
        convergence_time=float(iterations),
        iterations=iterations,
        timeout=False,
        messages=messages,
        bytes_sent=messages * 32,
        fractionality=0.0,
        entropy=0.0,
        switches=int(np.sum(raw != 0)),
        potential_violations=0,
        occupancy_error=math.nan,
        training_steps=int(spec.get("training_steps", payload.get("training_steps", 0)) or 0),
        training_converged=bool(spec.get("training_converged", payload.get("training_converged", False))),
        train_seed=int(spec.get("train_seed", payload.get("train_seed", 0)) or 0),
        method_online_time_ms=max(0.0, (runtime_s - closure_time_s) * 1000.0),
        simulation_end_time_s=float(iterations * 0.1),
        closure_applied=True,
        closure_type="POLICY_REPAIR",
        closure_success=matching_valid,
        maximum_cardinality=maximum_cardinality,
        final_success=maximum_cardinality,
        closure_runtime_ms=closure_time_s * 1000.0,
        closure_messages=0,
        preclosure_labels=raw,
    )


def run_untrained_debug_policy(world: Any, spec: dict[str, Any]) -> SP0MethodResult:
    """B0-only untrained path used to audit oracle isolation and variable-size inference."""

    started = time.perf_counter()
    algorithm = str(spec.get("id", "IPPO-GNN"))
    train_seed = int(spec.get("train_seed", spec.get("method_seed", 0)) or 0)
    torch.manual_seed(train_seed)
    model = SP0GNNActorCritic(
        hidden_dim=int(spec.get("hidden_dim", 64)),
        critic_global=algorithm.upper().startswith("MAPPO"),
        gnn_layers=int(spec.get("gnn_layers", 2)),
    )
    public = public_world_view(world) if isinstance(world, SP0World) else world
    raw, labels, iterations, closure_time_s = deterministic_policy_rollout(
        model,
        public,
        horizon=int(spec.get("inference_horizon", 2)),
    )
    runtime_s = time.perf_counter() - started
    messages = int(np.sum(public.adjacency)) * iterations
    matching_valid = assignment_valid(labels, public.n_loads)
    maximum_cardinality = bool(matching_valid and np.sum(labels > 0) == public.s_star)
    return SP0MethodResult(
        method_id=algorithm,
        method_family="data_driven_debug",
        architecture="distributed_local",
        dynamic_id=None,
        fitness_id=None,
        rounding_id="DEBUG_UNTRAINED_POLICY_REPAIR",
        labels=labels,
        continuous_x=None,
        runtime_ms=runtime_s * 1000.0,
        convergence_time=float(iterations),
        iterations=iterations,
        timeout=False,
        messages=messages,
        bytes_sent=messages * 32,
        fractionality=0.0,
        entropy=0.0,
        switches=int(np.sum(raw != 0)),
        potential_violations=0,
        occupancy_error=math.nan,
        training_steps=0,
        training_converged=False,
        train_seed=train_seed,
        method_online_time_ms=max(0.0, (runtime_s - closure_time_s) * 1000.0),
        simulation_end_time_s=float(iterations * 0.1),
        closure_applied=True,
        closure_type="DEBUG_UNTRAINED_POLICY_REPAIR",
        closure_success=matching_valid,
        maximum_cardinality=maximum_cardinality,
        final_success=maximum_cardinality,
        closure_runtime_ms=closure_time_s * 1000.0,
        closure_messages=0,
        preclosure_labels=raw,
    )


def archive_training_artifacts(output_dir: Path, paths: list[Path]) -> None:
    """Move incompatible training state aside without discarding evidence."""

    existing = [path for path in paths if path.exists()]
    if not existing:
        return
    archive = ensure_directory(output_dir / "archive")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    for path in existing:
        path.replace(archive / f"{path.stem}_{stamp}{path.suffix}")
def upgrade_validation_metric_names(history: list[dict[str, Any]]) -> bool:
    """Add explicit closure baselines to legacy validation metadata without retraining."""

    changed = False
    for point in history:
        validation = point.get("validation")
        if not isinstance(validation, dict):
            continue
        legacy = validation.get("mean_closure_NR_delta")
        if legacy is None:
            continue
        if "mean_closure_vs_raw_decode_NR_delta" not in validation:
            validation["mean_closure_vs_raw_decode_NR_delta"] = float(legacy)
            changed = True
        if "mean_raw_decode_NR" not in validation and validation.get("mean_NR") is not None:
            validation["mean_raw_decode_NR"] = float(validation["mean_NR"]) - float(legacy)
            changed = True
    return changed

def train_one_seed(
    *,
    algorithm: str,
    output_dir: Path,
    train_seed: int,
    total_steps: int,
    hidden_dim: int = 64,
    learning_rate: float = 3.0e-4,
    device: str = "cpu",
    eval_interval: int = 250_000,
    gnn_layers: int = 2,
    ppo_clip: float = 0.2,
    entropy_coefficient: float = 0.01,
    discount_factor: float = 0.99,
    ppo_epochs: int = 4,
    rollout_environment_steps: int = 128,
    episode_horizon: int = 4,
    save_periodic: bool = False,
) -> dict[str, Any]:
    """Train one shared policy with clipped PPO on graph-local SP0 observations."""

    output_dir = ensure_directory(output_dir)
    checkpoint = output_dir / "checkpoint.pt"
    metadata_path = output_dir / "metadata.json"
    progress_path = output_dir / "progress.pt"
    expected_config = {
        "trainer_version": POLICY_VERSION,
        "algorithm": algorithm,
        "train_seed": int(train_seed),
        "training_steps": int(total_steps),
        "hidden_dim": int(hidden_dim),
        "learning_rate": float(learning_rate),
        "gnn_layers": int(gnn_layers),
        "ppo_clip": float(ppo_clip),
        "entropy_coefficient": float(entropy_coefficient),
        "discount_factor": float(discount_factor),
        "ppo_epochs": int(ppo_epochs),
        "rollout_environment_steps": int(rollout_environment_steps),
        "training_step_unit": "joint_environment_transition",
        "episode_horizon": int(episode_horizon),
    }
    if metadata_path.exists() and checkpoint.exists():
        cached = json.loads(metadata_path.read_text(encoding="utf-8"))
        comparable = {key: cached.get(key) for key in expected_config}
        if comparable == expected_config and cached.get("checkpoint_hash") == sha256_file(checkpoint):
            if upgrade_validation_metric_names(cached.get("history", [])):
                save_json(metadata_path, cached)
            return {**cached, "resume_reused": True}
        archive_training_artifacts(output_dir, [metadata_path, checkpoint, progress_path])

    started = time.perf_counter()
    torch.manual_seed(int(train_seed))
    np.random.seed(int(train_seed))
    rng = np.random.default_rng(int(train_seed))
    resolved_device = torch.device(device)
    model = SP0GNNActorCritic(
        hidden_dim=hidden_dim,
        critic_global=algorithm.upper().startswith("MAPPO"),
        gnn_layers=gnn_layers,
    ).to(resolved_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(learning_rate))
    history: list[dict[str, Any]] = []
    steps_done = 0
    update_count = 0
    next_eval = max(1, int(eval_interval))
    resumed_from_step = 0
    if progress_path.exists():
        progress = torch.load(progress_path, map_location=resolved_device, weights_only=False)
        if progress.get("training_config") != expected_config:
            archive_training_artifacts(output_dir, [progress_path])
            progress = None
        if progress is not None:
            model.load_state_dict(progress["model_state_dict"])
            optimizer.load_state_dict(progress["optimizer_state_dict"])
            steps_done = int(progress["steps_done"])
            update_count = int(progress["update_count"])
            history = list(progress.get("history", []))
            upgrade_validation_metric_names(history)
            next_eval = int(progress.get("next_eval", next_eval))
            rng.bit_generator.state = progress["numpy_rng_state"]
            torch.set_rng_state(progress["torch_rng_state"].cpu())
            if resolved_device.type == "cuda" and progress.get("cuda_rng_state") is not None:
                torch.cuda.set_rng_state(progress["cuda_rng_state"].cpu(), device=resolved_device)
            resumed_from_step = steps_done

    while steps_done < int(total_steps):
        transitions: list[PPOTransition] = []
        target = min(int(rollout_environment_steps), int(total_steps) - steps_done)
        collected = 0
        while collected < target and steps_done + collected < int(total_steps):
            remaining = int(total_steps) - steps_done - collected
            world = sample_training_world(rng, step=steps_done + collected)
            episode = collect_ppo_episode(
                model,
                public_world_view(world),
                rng=rng,
                device=resolved_device,
                horizon=min(int(episode_horizon), remaining),
                discount_factor=float(discount_factor),
            )
            episode_steps = len(episode)
            if episode_steps <= 0 or episode_steps > remaining:
                raise RuntimeError("PPO rollout produced an invalid joint environment-step count")
            transitions.extend(episode)
            collected += episode_steps
        loss_stats = ppo_update(
            model,
            optimizer,
            transitions,
            device=resolved_device,
            ppo_clip=float(ppo_clip),
            entropy_coefficient=float(entropy_coefficient),
            ppo_epochs=int(ppo_epochs),
        )
        steps_done += collected
        update_count += 1
        should_evaluate = steps_done >= next_eval or steps_done == int(total_steps)
        if should_evaluate:
            validation = evaluate_policy(model, algorithm=algorithm)
            history.append(
                {
                    "training_steps": int(steps_done),
                    "optimizer_updates": int(update_count),
                    "validation": validation,
                    "loss": loss_stats,
                }
            )
            while next_eval <= steps_done:
                next_eval += max(1, int(eval_interval))
            progress_payload = {
                "training_config": expected_config,
                "steps_done": int(steps_done),
                "update_count": int(update_count),
                "history": history,
                "next_eval": int(next_eval),
                "model_state_dict": {key: value.detach().cpu() for key, value in model.state_dict().items()},
                "optimizer_state_dict": optimizer.state_dict(),
                "numpy_rng_state": rng.bit_generator.state,
                "torch_rng_state": torch.get_rng_state(),
                "cuda_rng_state": torch.cuda.get_rng_state(resolved_device) if resolved_device.type == "cuda" else None,
                "timestamp_utc": datetime.now(UTC).isoformat(),
            }
            temporary_progress = progress_path.with_suffix(".tmp")
            torch.save(progress_payload, temporary_progress)
            temporary_progress.replace(progress_path)
            if save_periodic:
                snapshot_dir = ensure_directory(output_dir / "checkpoints")
                torch.save(
                    {
                        "policy_version": POLICY_VERSION,
                        "algorithm": algorithm,
                        "hidden_dim": int(hidden_dim),
                        "gnn_layers": int(gnn_layers),
                        "training_steps": int(steps_done),
                        "model_state_dict": {key: value.detach().cpu() for key, value in model.state_dict().items()},
                    },
                    snapshot_dir / f"step_{steps_done:08d}.pt",
                )

    if steps_done != int(total_steps):
        raise RuntimeError(f"training step accounting mismatch: {steps_done} != {total_steps}")
    training_converged = operational_training_convergence(history)
    payload = {
        "policy_version": POLICY_VERSION,
        "algorithm": algorithm,
        "hidden_dim": int(hidden_dim),
        "gnn_layers": int(gnn_layers),
        "train_seed": int(train_seed),
        "training_steps": int(steps_done),
        "training_converged": bool(training_converged),
        "inference_horizon": int(episode_horizon),
        "model_state_dict": {key: value.detach().cpu() for key, value in model.state_dict().items()},
        "history": history,
    }
    torch.save(payload, checkpoint)
    checkpoint_hash = sha256_file(checkpoint)
    wall_s = time.perf_counter() - started
    using_cuda = resolved_device.type == "cuda"
    metadata = {
        **expected_config,
        "training_wall_s": float(wall_s),
        "gpu_hours": float(wall_s / 3600.0) if using_cuda else 0.0,
        "device": str(resolved_device),
        "optimizer_updates": int(update_count),
        "training_converged": bool(training_converged),
        "checkpoint_path": str(checkpoint),
        "checkpoint_hash": checkpoint_hash,
        "policy_version": POLICY_VERSION,
        "history": history,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "resume_reused": False,
        "resumed_from_step": int(resumed_from_step),
        "progress_checkpoint_path": str(progress_path),
    }
    save_json(metadata_path, metadata)
    return metadata


def collect_ppo_episode(
    model: SP0GNNActorCritic,
    world: Any,
    *,
    rng: np.random.Generator,
    device: torch.device,
    horizon: int,
    discount_factor: float,
) -> list[PPOTransition]:
    if horizon <= 0:
        return []
    previous = np.zeros(world.n_robots, dtype=int)
    transitions: list[PPOTransition] = []
    model.eval()
    for step in range(int(horizon)):
        batch = build_policy_batch(world, previous_actions=previous, device=device)
        with torch.no_grad():
            logits, values = model(batch)
            actions, log_probs = raw_actions_from_logits(
                logits,
                stochastic=True,
                seed=int(rng.integers(0, 2**31 - 1)),
            )
        terminal = step == int(horizon) - 1
        reward = assignment_reward(world, actions, previous, terminal=terminal)
        transitions.append(
            PPOTransition(
                world=world,
                previous_actions=previous.copy(),
                actions=actions.copy(),
                old_log_probs=log_probs.detach().cpu().numpy().astype(float),
                old_values=values.detach().cpu().numpy().astype(float),
                reward=float(reward),
            )
        )
        previous = actions
    running_return = 0.0
    for transition in reversed(transitions):
        running_return = transition.reward + float(discount_factor) * running_return
        transition.return_value = float(running_return)
        transition.advantages = np.full_like(
            transition.old_values,
            running_return,
            dtype=float,
        ) - transition.old_values
    return transitions


def ppo_update(
    model: SP0GNNActorCritic,
    optimizer: torch.optim.Optimizer,
    transitions: list[PPOTransition],
    *,
    device: torch.device,
    ppo_clip: float,
    entropy_coefficient: float,
    ppo_epochs: int,
) -> dict[str, float]:
    if not transitions:
        raise RuntimeError("PPO update requires at least one transition")
    all_advantages = np.concatenate([np.asarray(item.advantages, dtype=float) for item in transitions])
    advantage_mean = float(np.mean(all_advantages))
    advantage_std = float(np.std(all_advantages))
    total_agents = float(sum(item.actions.size for item in transitions))
    last_stats = {"policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0, "total_loss": 0.0}
    grouped: dict[tuple[int, int], list[PPOTransition]] = {}
    for transition in transitions:
        key = (int(transition.world.n_robots), int(transition.world.n_loads))
        grouped.setdefault(key, []).append(transition)
    model.train()
    for _epoch in range(max(1, int(ppo_epochs))):
        optimizer.zero_grad(set_to_none=True)
        total_loss = torch.zeros((), dtype=torch.float32, device=device)
        policy_acc = value_acc = entropy_acc = 0.0
        for same_shape in grouped.values():
            batch = stack_policy_batches([
                build_policy_batch(
                    transition.world,
                    previous_actions=transition.previous_actions,
                    device=device,
                )
                for transition in same_shape
            ])
            logits, values = model(batch)
            actions = torch.as_tensor(
                np.stack([transition.actions for transition in same_shape]),
                dtype=torch.long,
                device=device,
            )
            old_log_probs = torch.as_tensor(
                np.stack([transition.old_log_probs for transition in same_shape]),
                dtype=torch.float32,
                device=device,
            )
            advantages = torch.as_tensor(
                np.stack([transition.advantages for transition in same_shape]),
                dtype=torch.float32,
                device=device,
            )
            advantages = (advantages - advantage_mean) / max(advantage_std, 1.0e-8)
            returns = torch.as_tensor(
                np.asarray([transition.return_value for transition in same_shape], dtype=np.float32)[:, None],
                dtype=torch.float32,
                device=device,
            ).expand_as(values)
            distribution = Categorical(logits=logits)
            new_log_probs = distribution.log_prob(actions)
            ratio = torch.exp(new_log_probs - old_log_probs)
            unclipped = ratio * advantages
            clipped = torch.clamp(ratio, 1.0 - ppo_clip, 1.0 + ppo_clip) * advantages
            policy_loss = -torch.minimum(unclipped, clipped).mean()
            value_loss = 0.5 * (values - returns).pow(2).mean()
            entropy = distribution.entropy().mean()
            group_agents = sum(transition.actions.size for transition in same_shape)
            weight = float(group_agents) / total_agents
            transition_loss = policy_loss + value_loss - entropy_coefficient * entropy
            total_loss = total_loss + weight * transition_loss
            policy_acc += weight * float(policy_loss.detach().cpu())
            value_acc += weight * float(value_loss.detach().cpu())
            entropy_acc += weight * float(entropy.detach().cpu())
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        last_stats = {
            "policy_loss": policy_acc,
            "value_loss": value_acc,
            "entropy": entropy_acc,
            "total_loss": float(total_loss.detach().cpu()),
        }
    return last_stats


def sample_training_world(
    rng: np.random.Generator,
    *,
    step: int,
    max_n: int | None = None,
) -> SP0World:
    sizes = [size for size in [8, 16, 32] if max_n is None or size <= max_n]
    if not sizes:
        raise RuntimeError(f"remaining step budget {max_n} cannot fit an SP0 training world")
    n = int(rng.choice(sizes))
    ratio = float(rng.choice([1.5, 1.0, 0.67]))
    degree = rng.choice(["all", 4, 8])
    geometry = str(rng.choice(["G-UNI", "G-CLU", "G-TIE", "G-X"]))
    return make_sp0_world(
        n_robots=n,
        n_loads=max(1, int(math.ceil(n * ratio))),
        seed=int(200000 + step + rng.integers(0, 100000)),
        geometry_id=geometry,
        mean_degree_target=degree,
        sp_id="SP0-training",
    )


def evaluate_policy(
    model: SP0GNNActorCritic,
    *,
    algorithm: str,
    validation_seeds: tuple[int, ...] = (12000, 12001),
) -> dict[str, float]:
    regrets: list[float] = []
    greedy_regrets: list[float] = []
    successes: list[float] = []
    raw_successes: list[float] = []
    raw_regrets: list[float] = []
    closure_deltas: list[float] = []
    inference_times: list[float] = []
    device = next(model.parameters()).device
    for seed in validation_seeds:
        for n in [8, 16, 32]:
            for ratio in [1.5, 1.0, 0.67]:
                for degree in ["all", 4, 2]:
                    world = make_sp0_world(
                        n_robots=n,
                        n_loads=max(1, int(math.ceil(n * ratio))),
                        seed=int(seed),
                        geometry_id="G-UNI",
                        mean_degree_target=degree,
                        sp_id="SP0-training-validation",
                    )
                    public = public_world_view(world)
                    started = time.perf_counter()
                    raw, labels, _iterations, _closure_s = deterministic_policy_rollout(
                        model,
                        public,
                        horizon=4,
                        device=device,
                    )
                    inference_times.append(time.perf_counter() - started)
                    j_value = assignment_objective(public, labels)
                    raw_j = assignment_objective(public, raw)
                    denominator = float((world.s_star + 1.0) * world.s_star + world.s_star)
                    nr = float(max(j_value - world.oracle_j, 0.0) / max(denominator, 1.0e-12))
                    raw_nr = float(max(raw_j - world.oracle_j, 0.0) / max(denominator, 1.0e-12))
                    greedy_labels = greedy_assignment(public)
                    greedy_j = assignment_objective(public, greedy_labels)
                    greedy_nr = float(max(greedy_j - world.oracle_j, 0.0) / max(denominator, 1.0e-12))
                    regrets.append(nr)
                    greedy_regrets.append(greedy_nr)
                    raw_regrets.append(raw_nr)
                    closure_deltas.append(nr - raw_nr)
                    successes.append(float(assignment_valid(labels, world.n_loads) and np.sum(labels > 0) == world.s_star))
                    raw_successes.append(float(assignment_valid(raw, world.n_loads) and np.sum(raw > 0) == world.s_star))
    mean_nr = float(np.mean(regrets))
    greedy_mean_nr = float(np.mean(greedy_regrets))
    return {
        "algorithm": algorithm,
        "mean_NR": mean_nr,
        "CVaR95_NR": cvar95(np.asarray(regrets, dtype=float)),
        "success": float(np.mean(successes)),
        "raw_success": float(np.mean(raw_successes)),
        "greedy_mean_NR": greedy_mean_nr,
        "NR_minus_Greedy": mean_nr - greedy_mean_nr,
        "mean_raw_decode_NR": float(np.mean(raw_regrets)),
        "mean_closure_vs_raw_decode_NR_delta": float(np.mean(closure_deltas)),
        "mean_closure_NR_delta": float(np.mean(closure_deltas)),
        "inference_time_s": float(np.mean(inference_times)),
        "n_validation_worlds": float(len(regrets)),
    }


def operational_training_convergence(
    history: list[dict[str, Any]],
    *,
    success_threshold: float = 0.99,
    greedy_delta: float = 0.05,
    consecutive: int = 3,
    collapse_margin: float = 0.05,
) -> bool:
    validations = [dict(item.get("validation", {})) for item in history]
    if len(validations) < consecutive:
        return False
    for end in range(consecutive - 1, len(validations)):
        window = validations[end - consecutive + 1 : end + 1]
        qualifies = all(
            float(item.get("success", 0.0)) >= success_threshold
            and float(item.get("NR_minus_Greedy", math.inf)) < greedy_delta
            for item in window
        )
        if not qualifies:
            continue
        reference = window[-1]
        later = validations[end + 1 :]
        collapsed = any(
            float(item.get("success", 0.0)) < float(reference.get("success", 0.0)) - collapse_margin
            or float(item.get("mean_NR", math.inf)) > float(reference.get("mean_NR", math.inf)) + collapse_margin
            for item in later
        )
        if not collapsed:
            return True
    return False


def cvar95(values: np.ndarray) -> float:
    if values.size == 0:
        return math.nan
    threshold = float(np.quantile(values, 0.95))
    tail = values[values >= threshold]
    return float(np.mean(tail if tail.size else values))

def write_executor_metadata(training_dir: Path) -> dict[str, Any]:
    metadata = {
        "executor_module": "viu_mrob_tfm.sp0.data_driven",
        "executor_function": "run_checkpoint_policy",
        "backend": "torch_checkpoint_gnn_actor",
        "backend_sha256": sha256_file(Path(__file__)),
        "policy_version": POLICY_VERSION,
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    save_json(training_dir / "dd_executor.json", metadata)
    return metadata


def training_candidate_configs(algorithm: str) -> list[dict[str, Any]]:
    base = algorithm.replace("-", "_")
    variants = [
        (1.0e-4, 64, 2, 0.1, 0.001, 0.95),
        (3.0e-4, 64, 2, 0.2, 0.010, 0.99),
        (1.0e-3, 64, 3, 0.2, 0.001, 0.95),
        (1.0e-4, 128, 3, 0.1, 0.010, 0.99),
        (3.0e-4, 128, 2, 0.2, 0.001, 0.99),
        (1.0e-3, 128, 3, 0.1, 0.010, 0.95),
    ]
    return [
        {
            "config_id": f"{base}_cfg{index + 1:02d}",
            "algorithm": algorithm,
            "learning_rate": learning_rate,
            "hidden_dim": hidden_dim,
            "gnn_layers": gnn_layers,
            "ppo_clip": ppo_clip,
            "entropy_coefficient": entropy,
            "discount_factor": discount,
        }
        for index, (learning_rate, hidden_dim, gnn_layers, ppo_clip, entropy, discount) in enumerate(variants)
    ]


def score_training_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["config_id"]), []).append(row)
    scored: list[dict[str, Any]] = []
    for config_id, selected in grouped.items():
        nr = np.asarray([float(row.get("validation_NR", 1.0)) for row in selected], dtype=float)
        fail = np.asarray([not bool(row.get("training_converged", False)) for row in selected], dtype=bool)
        cvar = float(np.mean(nr[nr >= np.quantile(nr, 0.95)])) if nr.size else 1.0
        score = float(np.mean(nr) + np.mean(fail) + 0.25 * cvar)
        scored.append(
            {
                "config_id": config_id,
                "algorithm": selected[0].get("algorithm"),
                "S_val": score,
                "mean_NR": float(np.mean(nr)) if nr.size else 1.0,
                "failure_rate": float(np.mean(fail)) if fail.size else 1.0,
                "CVaR95_NR": cvar,
                "inference_cost": float(np.mean([float(row.get("inference_time_s", 0.0)) for row in selected])),
                "n": len(selected),
            }
        )
    return sorted(
        scored,
        key=lambda item: (item["S_val"], item["CVaR95_NR"], item["inference_cost"], item["config_id"]),
    )


def flatten_training_metadata(config: dict[str, Any], metadata: dict[str, Any], *, round_id: str) -> dict[str, Any]:
    validation = dict((metadata.get("history") or [{"validation": {}}])[-1].get("validation", {}))
    return {
        "round_id": round_id,
        "config_id": config["config_id"],
        "algorithm": config["algorithm"],
        "learning_rate": config["learning_rate"],
        "hidden_dim": config["hidden_dim"],
        "gnn_layers": config["gnn_layers"],
        "ppo_clip": config["ppo_clip"],
        "entropy_coefficient": config["entropy_coefficient"],
        "discount_factor": config["discount_factor"],
        "train_seed": metadata.get("train_seed"),
        "training_steps": metadata.get("training_steps"),
        "training_wall_s": metadata.get("training_wall_s"),
        "gpu_hours": metadata.get("gpu_hours"),
        "training_converged": metadata.get("training_converged"),
        "validation_success": validation.get("success"),
        "validation_raw_success": validation.get("raw_success"),
        "validation_NR": validation.get("mean_NR"),
        "validation_CVaR95_NR": validation.get("CVaR95_NR"),
        "validation_NR_minus_Greedy": validation.get("NR_minus_Greedy"),
        "validation_raw_decode_NR": validation.get("mean_raw_decode_NR"),
        "validation_closure_vs_raw_decode_NR_delta": validation.get("mean_closure_vs_raw_decode_NR_delta"),
        "checkpoint_hash": metadata.get("checkpoint_hash"),
        "checkpoint_path": metadata.get("checkpoint_path"),
        "inference_time_s": validation.get("inference_time_s"),
    }


def train_with_config(
    *,
    config: dict[str, Any],
    output_dir: Path,
    train_seed: int,
    total_steps: int,
    device: str,
    eval_interval: int,
    ppo_epochs: int = 4,
    rollout_environment_steps: int = 128,
    episode_horizon: int = 4,
    save_periodic: bool = False,
) -> dict[str, Any]:
    return train_one_seed(
        algorithm=str(config["algorithm"]),
        output_dir=output_dir,
        train_seed=int(train_seed),
        total_steps=int(total_steps),
        hidden_dim=int(config["hidden_dim"]),
        learning_rate=float(config["learning_rate"]),
        device=device,
        eval_interval=int(eval_interval),
        gnn_layers=int(config["gnn_layers"]),
        ppo_clip=float(config["ppo_clip"]),
        entropy_coefficient=float(config["entropy_coefficient"]),
        discount_factor=float(config["discount_factor"]),
        ppo_epochs=int(ppo_epochs),
        rollout_environment_steps=int(rollout_environment_steps),
        episode_horizon=int(episode_horizon),
        save_periodic=save_periodic,
    )


def run_data_driven_tuning(
    training_dir: Path,
    *,
    full_budget: bool,
    device: str,
    training_protocol: dict[str, Any],
) -> dict[str, Any]:
    dd1_steps = int(training_protocol.get("DD_1", {}).get("environment_steps", 250_000)) if full_budget else 16
    dd2_steps = int(training_protocol.get("DD_2", {}).get("environment_steps", 1_000_000)) if full_budget else 32
    ppo_epochs = int(training_protocol.get("ppo_epochs", 4))
    rollout_environment_steps = int(training_protocol.get("rollout_environment_steps", 128))
    episode_horizon = int(training_protocol.get("episode_horizon", 4))
    rows: list[dict[str, Any]] = []
    champion_by_algorithm: dict[str, dict[str, Any]] = {}
    for algorithm in ["IPPO-GNN", "MAPPO-GNN"]:
        configs = training_candidate_configs(algorithm)
        round1_rows: list[dict[str, Any]] = []
        for cfg in configs:
            metadata = train_with_config(
                config=cfg,
                output_dir=training_dir / algorithm.replace("-", "_") / "DD1" / cfg["config_id"],
                train_seed=14101,
                total_steps=dd1_steps,
                device=device,
                eval_interval=max(dd1_steps // 3, 1),
                ppo_epochs=ppo_epochs,
                rollout_environment_steps=rollout_environment_steps,
                episode_horizon=episode_horizon,
            )
            row = flatten_training_metadata(cfg, metadata, round_id="DD-1")
            round1_rows.append(row)
            rows.append(row)
        top2_ids = {row["config_id"] for row in score_training_runs(round1_rows)[:2]}
        round2_rows: list[dict[str, Any]] = []
        for cfg in [item for item in configs if item["config_id"] in top2_ids]:
            for seed in [14201, 14202]:
                metadata = train_with_config(
                    config=cfg,
                    output_dir=training_dir / algorithm.replace("-", "_") / "DD2" / cfg["config_id"] / str(seed),
                    train_seed=seed,
                    total_steps=dd2_steps,
                    device=device,
                    eval_interval=max(dd2_steps // 3, 1),
                    ppo_epochs=ppo_epochs,
                    rollout_environment_steps=rollout_environment_steps,
                    episode_horizon=episode_horizon,
                )
                row = flatten_training_metadata(cfg, metadata, round_id="DD-2")
                round2_rows.append(row)
                rows.append(row)
        best = score_training_runs(round2_rows)[0]
        best_cfg = next(cfg for cfg in configs if cfg["config_id"] == best["config_id"])
        champion_by_algorithm[algorithm] = {**best_cfg, **best}
    selected = sorted(
        champion_by_algorithm.values(),
        key=lambda item: (item["S_val"], item["CVaR95_NR"], item["inference_cost"], item["algorithm"]),
    )[0]
    selection = {
        "selection_rule": "validation_between_IPPO_GNN_and_MAPPO_GNN",
        "rounds": {"DD-1_steps": dd1_steps, "DD-2_steps": dd2_steps},
        "training_contract": {
            "ppo_epochs": ppo_epochs,
            "rollout_environment_steps": rollout_environment_steps,
            "episode_horizon": episode_horizon,
        },
        "champion_id": selected["algorithm"],
        "champion_config": selected,
        "algorithm_champions": champion_by_algorithm,
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    selection_dir = ensure_directory(training_dir / "champion_selection")
    write_yaml(selection_dir / "champion_selection.yaml", selection)
    write_parquet(selection_dir / "champion_selection.parquet", rows)
    return selection

SP0_V1_1_TRAINING_BUDGET = {
    "algorithms": 2,
    "DD_1_configurations_per_algorithm": 6,
    "DD_1_train_seeds_per_configuration": 1,
    "DD_1_environment_steps": 250_000,
    "DD_2_retained_configurations_per_algorithm": 2,
    "DD_2_train_seeds_per_configuration": 2,
    "DD_2_environment_steps": 1_000_000,
    "final_independent_train_seeds": 3,
    "final_environment_steps_per_seed": 5_000_000,
    "total_environment_steps": 26_000_000,
}


def validate_sp0_v1_1_training_budget(config: dict[str, Any]) -> list[str]:
    """Reject any resource-driven reduction of the canonical v1.1 MARL budget."""

    training = dict(config.get("data_driven_training", config))
    algorithms = list(training.get("algorithms", []))
    dd1 = dict(training.get("DD_1", {}))
    dd2 = dict(training.get("DD_2", {}))
    final = dict(training.get("final", {}))
    observed = {
        "algorithms": len(algorithms),
        "DD_1_configurations_per_algorithm": int(dd1.get("configurations_per_algorithm", 0)),
        "DD_1_train_seeds_per_configuration": int(dd1.get("train_seeds_per_configuration", 0)),
        "DD_1_environment_steps": int(dd1.get("environment_steps", 0)),
        "DD_2_retained_configurations_per_algorithm": int(dd2.get("retained_configurations_per_algorithm", 0)),
        "DD_2_train_seeds_per_configuration": int(dd2.get("train_seeds_per_configuration", 0)),
        "DD_2_environment_steps": int(dd2.get("environment_steps", 0)),
        "final_independent_train_seeds": int(final.get("independent_train_seeds", 0)),
        "final_environment_steps_per_seed": int(final.get("environment_steps_per_seed", 0)),
    }
    errors = [
        f"{field}={observed[field]} but SP0 v1.1 requires {expected}"
        for field, expected in SP0_V1_1_TRAINING_BUDGET.items()
        if field != "total_environment_steps" and observed.get(field) != expected
    ]
    if not errors:
        total = expected_training_environment_steps({"data_driven_training": training})
        if total != SP0_V1_1_TRAINING_BUDGET["total_environment_steps"]:
            errors.append(
                f"total_environment_steps={total} but SP0 v1.1 requires "
                f"{SP0_V1_1_TRAINING_BUDGET['total_environment_steps']}"
            )
    return errors


def expected_training_environment_steps(config: dict[str, Any]) -> int:
    training = dict(config.get("data_driven_training", {}))
    algorithms = len(training.get("algorithms", ["IPPO-GNN", "MAPPO-GNN"]))
    dd1 = dict(training.get("DD_1", {}))
    dd2 = dict(training.get("DD_2", {}))
    final = dict(training.get("final", {}))
    return int(
        algorithms
        * int(dd1.get("configurations_per_algorithm", 6))
        * int(dd1.get("train_seeds_per_configuration", 1))
        * int(dd1.get("environment_steps", 250_000))
        + algorithms
        * int(dd2.get("retained_configurations_per_algorithm", 2))
        * int(dd2.get("train_seeds_per_configuration", 2))
        * int(dd2.get("environment_steps", 1_000_000))
        + int(final.get("independent_train_seeds", 3))
        * int(final.get("environment_steps_per_seed", 5_000_000))
    )


def run_cpu_hardware_preflight(config: dict[str, Any], root: Path) -> dict[str, Any]:
    """Measure or reuse CPU throughput without consuming official training seeds."""

    from viu_mrob_tfm.sp0.audit import hardware_info

    training = dict(config.get("data_driven_training", {}))
    preflight = dict(training.get("hardware_preflight", {}))
    benchmark_steps = int(preflight.get("benchmark_environment_steps", 10_000))
    expected_steps = expected_training_environment_steps(config)
    declared_steps = int(training.get("expected_total_environment_steps", expected_steps))
    if declared_steps != expected_steps:
        raise RuntimeError(
            f"Declared training total {declared_steps} does not match round formula {expected_steps}"
        )
    ppo_epochs = int(training.get("ppo_epochs", 4))
    rollout_environment_steps = int(training.get("rollout_environment_steps", 128))
    episode_horizon = int(training.get("episode_horizon", 4))
    benchmark_path = root / "training" / "hardware_benchmark.json"
    hardware = hardware_info()
    if benchmark_path.exists():
        cached = json.loads(benchmark_path.read_text(encoding="utf-8"))
        same_contract = (
            cached.get("policy_version") == POLICY_VERSION
            and cached.get("training_step_unit") == "joint_environment_transition"
            and int(cached.get("benchmark_steps", -1)) == benchmark_steps
            and int(cached.get("ppo_epochs", -1)) == ppo_epochs
            and int(cached.get("rollout_environment_steps", -1)) == rollout_environment_steps
            and int(cached.get("episode_horizon", -1)) == episode_horizon
            and cached.get("hardware", {}).get("cpu_model") == hardware.get("cpu_model")
            and cached.get("hardware", {}).get("torch_version") == hardware.get("torch_version")
            and float(cached.get("measured_environment_steps_per_s", 0.0)) > 0.0
        )
        if same_contract:
            return {**cached, "resume_reused": True}

    metadata = train_one_seed(
        algorithm="IPPO-GNN",
        output_dir=ensure_directory(root / "training" / "hardware_preflight" / "IPPO_GNN"),
        train_seed=int(preflight.get("benchmark_seed", 777001)),
        total_steps=benchmark_steps,
        hidden_dim=64,
        learning_rate=3.0e-4,
        device="cpu",
        eval_interval=benchmark_steps,
        gnn_layers=2,
        ppo_clip=0.2,
        entropy_coefficient=0.01,
        discount_factor=0.99,
        ppo_epochs=ppo_epochs,
        rollout_environment_steps=rollout_environment_steps,
        episode_horizon=episode_horizon,
    )
    rate = float(benchmark_steps / max(float(metadata["training_wall_s"]), 1.0e-12))
    estimate_s = float(expected_steps / rate)
    benchmark = {
        "status": "complete",
        "scope": str(preflight.get("benchmark_scope", "prefreeze_engineering_only")),
        "policy_version": POLICY_VERSION,
        "training_step_unit": "joint_environment_transition",
        "benchmark_steps": benchmark_steps,
        "ppo_epochs": ppo_epochs,
        "rollout_environment_steps": rollout_environment_steps,
        "episode_horizon": episode_horizon,
        "benchmark_wall_s": float(metadata["training_wall_s"]),
        "measured_environment_steps_per_s": rate,
        "expected_full_training_environment_steps": expected_steps,
        "estimated_training_wall_s_lower_bound": estimate_s,
        "estimated_training_wall_hours_lower_bound": estimate_s / 3600.0,
        "validation_and_campaign_time_excluded": True,
        "hardware": hardware,
        "benchmark_checkpoint_sha256": metadata["checkpoint_hash"],
        "confirmatory_seeds_opened": False,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "resume_reused": bool(metadata.get("resume_reused", False)),
    }
    save_json(benchmark_path, benchmark)
    return benchmark


def cpu_hardware_block_status(
    config: dict[str, Any],
    root: Path,
    *,
    allow_long_cpu_training: bool,
) -> dict[str, Any] | None:
    if allow_long_cpu_training:
        return None
    training = dict(config.get("data_driven_training", {}))
    preflight = dict(training.get("hardware_preflight", {}))
    benchmark = run_cpu_hardware_preflight(config, root)
    maximum_hours = float(preflight.get("maximum_estimated_training_wall_hours", 24.0))
    estimated_hours = float(benchmark["estimated_training_wall_hours_lower_bound"])
    if estimated_hours <= maximum_hours:
        return None
    return {
        "status": "HARDWARE_BLOCKED",
        "reason": (
            f"CPU preflight estimates at least {estimated_hours:.1f} hours for the frozen "
            f"{int(benchmark['expected_full_training_environment_steps'])} environment-step budget; "
            f"the configured operational limit is {maximum_hours:.1f} hours."
        ),
        "artifact_scope": "confirmatory_training_not_started",
        "training_step_unit": "joint_environment_transition",
        "budget_reduced": False,
        "failed_seed_replaced": False,
        "confirmatory_seeds_opened": False,
        "hardware_benchmark_path": str(root / "training" / "hardware_benchmark.json"),
        "estimated_training_wall_hours_lower_bound": estimated_hours,
        "maximum_estimated_training_wall_hours": maximum_hours,
        "required_action": (
            "resume unchanged full budget on suitable CUDA hardware, a durable worker, "
            "or pass --allow-long-cpu-training explicitly"
        ),
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }

def resolve_training_device(requested: str) -> str:
    normalized = str(requested or "auto").lower()
    if normalized == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if normalized.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"Requested device {requested!r}, but torch.cuda.is_available() is false.")
    return str(requested)


def train_data_driven_from_config(
    config_path: str | Path,
    *,
    full_budget: bool = True,
    device: str = "auto",
    allow_long_cpu_training: bool = False,
) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    root = ensure_directory(config.get("output_dir", "results/sp0/SP0_PROTOCOL_v1_1"))
    canonical_training_dir = ensure_directory(root / "training")
    training_dir = canonical_training_dir if full_budget else ensure_directory(canonical_training_dir / "dry_run")
    budget_errors = validate_sp0_v1_1_training_budget(config) if full_budget else []
    if budget_errors:
        status = {
            "status": "INVALID_TRAINING_BUDGET",
            "reason": "Reduced training budgets cannot satisfy SP0_PROTOCOL_v1_1.",
            "budget_errors": budget_errors,
            "budget_reduced": True,
            "confirmatory_seeds_opened": False,
            "artifact_scope": "noncanonical_preserved_evidence_only",
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        save_json(training_dir / "status.json", status)
        write_executor_metadata(canonical_training_dir)
        return status
    try:
        resolved_device = resolve_training_device(device)
    except RuntimeError as exc:
        status = {
            "status": "HARDWARE_BLOCKED",
            "reason": str(exc),
            "confirmatory_seeds_opened": False,
            "artifact_scope": "confirmatory" if full_budget else "dry_run_only",
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        save_json(training_dir / "status.json", status)
        write_executor_metadata(canonical_training_dir)
        return status

    if full_budget and resolved_device == "cpu":
        blocked = cpu_hardware_block_status(
            config,
            root,
            allow_long_cpu_training=allow_long_cpu_training,
        )
        if blocked is not None:
            save_json(training_dir / "status.json", blocked)
            write_executor_metadata(canonical_training_dir)
            return blocked
    running_status = {
        "status": "RUNNING",
        "device": resolved_device,
        "artifact_scope": "confirmatory" if full_budget else "dry_run_only",
        "expected_total_environment_steps": (
            expected_training_environment_steps(config) if full_budget else 640
        ),
        "training_step_unit": "joint_environment_transition",
        "confirmatory_seeds_opened": False,
        "allow_long_cpu_training": bool(allow_long_cpu_training),
        "started_or_resumed_at_utc": datetime.now(UTC).isoformat(),
    }
    save_json(training_dir / "status.json", running_status)
    training_protocol = dict(config.get("data_driven_training", {}))
    selection = run_data_driven_tuning(
        training_dir,
        full_budget=full_budget,
        device=resolved_device,
        training_protocol=training_protocol,
    )
    final_steps = (
        int(training_protocol.get("final", {}).get("environment_steps_per_seed", 5_000_000))
        if full_budget else 64
    )
    algorithm = str(selection["champion_id"])
    champion_cfg = dict(selection["champion_config"])
    final_seed_dir = ensure_directory(training_dir / "final_seeds")
    seeds = [15001, 15002, 15003]
    final: list[dict[str, Any]] = []
    for idx, seed in enumerate(seeds, start=1):
        final.append(
            train_with_config(
                config=champion_cfg,
                output_dir=final_seed_dir / f"DD_seed_{idx}",
                train_seed=seed,
                total_steps=final_steps,
                device=resolved_device,
                eval_interval=max(final_steps // 4, 1),
                ppo_epochs=int(training_protocol.get("ppo_epochs", 4)),
                rollout_environment_steps=int(training_protocol.get("rollout_environment_steps", 128)),
                episode_horizon=int(training_protocol.get("episode_horizon", 4)),
                save_periodic=full_budget,
            )
        )
    champion = {
        "champion_id": algorithm,
        "selection_rule": "validation_between_IPPO_GNN_and_MAPPO_GNN",
        "champion_config": champion_cfg,
        "training_budget_contract": {
            "DD_1_steps": int(training_protocol.get("DD_1", {}).get("environment_steps", 250_000)),
            "DD_2_steps": int(training_protocol.get("DD_2", {}).get("environment_steps", 1_000_000)),
            "final_steps_per_seed": final_steps,
            "expected_total_environment_steps": expected_training_environment_steps(config),
            "ppo_epochs": int(training_protocol.get("ppo_epochs", 4)),
            "rollout_environment_steps": int(training_protocol.get("rollout_environment_steps", 128)),
            "episode_horizon": int(training_protocol.get("episode_horizon", 4)),
            "claim_scope": config.get("revision", {}).get("confirmatory_claim_scope", "original_protocol"),
        },
        "final_checkpoint_rule": (
            f"use_exact_final_checkpoint_at_{final_steps}_steps_no_best_seed_selection"
            if full_budget
            else "dry_run_not_confirmatory"
        ),
        "did_not_converge_under_preregistered_budget": bool(
            full_budget and not any(bool(seed.get("training_converged")) for seed in final)
        ),
        "final_seeds": final,
    }
    write_yaml(training_dir / "champion.yaml", champion)
    write_executor_metadata(canonical_training_dir)
    status = {
        "status": "complete" if full_budget else "dry_run_complete",
        "champion_id": algorithm,
        "final_seeds": final,
        "device": resolved_device,
        "artifact_scope": "confirmatory" if full_budget else "dry_run_only",
        "confirmatory_seeds_opened": False,
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    save_json(training_dir / "status.json", status)
    return status

def write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    import pandas as pd

    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)

def write_yaml(path: Path, data: Any) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=True, allow_unicode=False), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
