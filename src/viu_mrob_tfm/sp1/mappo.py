"""Minimal real MAPPO trainer and policy for SP1 recruitment."""

from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import torch
from torch import nn
from torch.distributions import Categorical
from scipy.optimize import linear_sum_assignment

from viu_mrob_tfm.allocation import Assignment, BaseAllocator, DecisionContext, timed_allocate
from viu_mrob_tfm.sp1.methods import CentralizedCoalitionOracleAllocator, iter_complete_slot_plans
from viu_mrob_tfm.sp1.metrics import evaluate_assignment, load_diagnostics
from viu_mrob_tfm.sp1.scenario import iter_sp1_worlds
from viu_mrob_tfm.utils.io import ensure_directory, save_json


PAIR_FEATURE_NAMES = [
    "bias",
    "reward_norm",
    "load_demand_ratio",
    "capacity_ratio",
    "distance_norm",
    "visible",
]

GLOBAL_FEATURE_NAMES = [
    "robot_count_norm",
    "load_count_norm",
    "demand_ratio",
    "capacity_ratio",
    "mean_reward_norm",
    "payload_cv",
    "mean_distance_norm",
]


class PairActor(nn.Module):
    """Shared decentralized actor scoring each AMR-load pair plus idle."""

    def __init__(self, feature_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.pair_net = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        self.idle_logit = nn.Parameter(torch.zeros(1))

    def forward(self, pair_features: torch.Tensor, load_mask: torch.Tensor) -> torch.Tensor:
        load_logits = self.pair_net(pair_features).squeeze(-1)
        load_logits = load_logits.masked_fill(~load_mask, -1.0e9)
        idle_logits = self.idle_logit.expand(pair_features.shape[0], 1)
        return torch.cat([idle_logits, load_logits], dim=1)


class CentralCritic(nn.Module):
    """Centralized value function used only during MAPPO training."""

    def __init__(self, feature_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, global_features: torch.Tensor) -> torch.Tensor:
        return self.net(global_features).squeeze(-1)


@dataclass(slots=True)
class MAPPORecruitmentAllocator(BaseAllocator):
    """Frozen MAPPO policy with decentralized execution."""

    name: str = "mappo_recruitment"
    checkpoint: Path | None = None
    deterministic: bool = True
    _actor: PairActor | None = field(default=None, init=False, repr=False)
    _metadata: dict[str, Any] | None = field(default=None, init=False, repr=False)

    def allocate(self, context: DecisionContext) -> Assignment:
        actor, metadata = self._load_actor()
        world = context.world
        robot_count = len(world.robots)
        if robot_count == 0 or not world.loads:
            return Assignment(labels=np.zeros(robot_count, dtype=int), method=self.name)

        radius = float(context.metadata.get("communication_radius", np.inf))
        pair_features, load_mask = pair_features_for_world(world, radius)
        with torch.no_grad():
            logits = actor(
                torch.as_tensor(pair_features, dtype=torch.float32),
                torch.as_tensor(load_mask, dtype=torch.bool),
            )
            if self.deterministic and bool(metadata.get("use_quorum_decoder", True)):
                labels = decode_quorum_assignment(
                    world,
                    logits[:, 1:].detach().cpu().numpy(),
                    load_mask=load_mask,
                    reward_weight=float(metadata.get("decoder_reward_weight", 2.0)),
                    distance_weight=float(metadata.get("decoder_distance_weight", 0.02)),
                    capacity_weight=float(metadata.get("decoder_capacity_weight", 0.02)),
                    actor_weight=float(metadata.get("decoder_actor_weight", 0.05)),
                    demand_weight=float(metadata.get("decoder_demand_weight", 0.8)),
                )
            else:
                if self.deterministic:
                    actions = torch.argmax(logits, dim=1)
                else:
                    actions = Categorical(logits=logits).sample()
                labels = actions.cpu().numpy().astype(int)
        return Assignment(labels=labels, scores=logits[:, 1:].detach().cpu().numpy(), method=self.name)

    def _load_actor(self) -> tuple[PairActor, dict[str, Any]]:
        if self._actor is not None and self._metadata is not None:
            return self._actor, self._metadata

        metadata, state = load_mappo_checkpoint(self.checkpoint)
        hidden_dim = int(metadata.get("hidden_dim", 32))
        actor = PairActor(feature_dim=len(PAIR_FEATURE_NAMES), hidden_dim=hidden_dim)
        if state is not None:
            actor.load_state_dict(state["actor_state_dict"])
        actor.eval()
        self._actor = actor
        self._metadata = metadata
        return actor, metadata


@dataclass(slots=True)
class RolloutSample:
    pair_features: np.ndarray
    load_mask: np.ndarray
    global_features: np.ndarray
    actions: np.ndarray
    old_joint_logprob: float
    reward: float
    value: float
    metrics: dict[str, Any]


def train_mappo_recruitment(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    """Train a compact MAPPO policy for SP1 with disjoint validation seeds."""

    training_id = str(config.get("training_id", config_path.stem))
    algorithm = config.get("algorithm", {}).get("params", {})
    reward_config = dict(config.get("reward", {}))
    output_dir = ensure_directory(config.get("output", {}).get("checkpoint_dir", "outputs/trained_models/SP1/mappo_recruitment/v1"))
    train_seeds = _seed_range(config.get("train_seeds", {"start": 0, "count": 32}))
    validation_seeds = _seed_range(config.get("validation_seeds", {"start": 1000, "count": 8}))
    test_seeds = _seed_range(config.get("test_seeds", {"start": 1200, "count": 0}))
    generators = [str(item.get("param_generator", item.get("generator", "monte_carlo"))) for item in config.get("scenarios", [{"param_generator": "monte_carlo"}])]

    random_seed = int(algorithm.get("random_seed", 1234))
    torch.manual_seed(random_seed)
    np.random.seed(random_seed)
    hidden_dim = int(algorithm.get("hidden_dim", 32))
    total_episodes = int(algorithm.get("total_episodes", min(len(train_seeds), 128)))
    if "total_steps" in algorithm and "total_episodes" not in algorithm:
        horizon = max(1, int(algorithm.get("rollout_horizon", 32)))
        total_episodes = min(len(train_seeds), max(1, int(algorithm["total_steps"]) // horizon))
    rollout_horizon = max(1, int(algorithm.get("rollout_horizon", 16)))
    ppo_epochs = max(1, int(algorithm.get("ppo_epochs", 4)))
    learning_rate = float(algorithm.get("learning_rate", 3.0e-4))
    clip_epsilon = float(algorithm.get("clip_epsilon", 0.2))
    entropy_coef = float(algorithm.get("entropy_coef", 0.01))
    value_coef = float(algorithm.get("value_coef", 0.5))
    bc_pretrain_epochs = max(0, int(algorithm.get("bc_pretrain_epochs", 0)))
    bc_learning_rate = float(algorithm.get("bc_learning_rate", max(learning_rate, 1.0e-3)))
    use_quorum_decoder = bool(algorithm.get("use_quorum_decoder", True))
    rollout_action_mode = str(algorithm.get("rollout_action_mode", "sampled_policy"))
    if rollout_action_mode not in {"sampled_policy", "greedy_policy", "decoder_guided"}:
        raise ValueError(f"Unknown MAPPO rollout_action_mode: {rollout_action_mode}")

    actor = PairActor(feature_dim=len(PAIR_FEATURE_NAMES), hidden_dim=hidden_dim)
    critic = CentralCritic(feature_dim=len(GLOBAL_FEATURE_NAMES), hidden_dim=hidden_dim)

    train_worlds = list(iter_sp1_worlds(generators, train_seeds))
    if not train_worlds:
        raise ValueError("MAPPO training requires at least one training world.")
    bc_history: list[dict[str, Any]] = []
    if bc_pretrain_epochs > 0:
        bc_history = supervised_pretrain_actor(
            actor,
            train_worlds,
            epochs=bc_pretrain_epochs,
            learning_rate=bc_learning_rate,
        )
    optimizer = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=learning_rate)
    selected_worlds = [train_worlds[idx % len(train_worlds)] for idx in range(total_episodes)]

    history: list[dict[str, Any]] = []
    episode_idx = 0
    update_idx = 0
    while episode_idx < total_episodes:
        batch_worlds = selected_worlds[episode_idx : episode_idx + rollout_horizon]
        samples = [
            collect_rollout_sample(
                actor,
                critic,
                world,
                params.communication_radius,
                reward_config,
                use_quorum_decoder=use_quorum_decoder,
                rollout_action_mode=rollout_action_mode,
            )
            for _generator, _variant_id, _seed, params, world in batch_worlds
        ]
        losses = update_mappo(
            actor,
            critic,
            optimizer,
            samples,
            clip_epsilon=clip_epsilon,
            entropy_coef=entropy_coef,
            value_coef=value_coef,
            ppo_epochs=ppo_epochs,
        )
        rewards = [sample.reward for sample in samples]
        satisfactions = [float(sample.metrics["demand_satisfaction_ratio"]) for sample in samples]
        history.append(
            {
                "update": update_idx,
                "episodes_seen": min(episode_idx + len(samples), total_episodes),
                "reward_mean": float(np.mean(rewards)),
                "demand_satisfaction_ratio_mean": float(np.mean(satisfactions)),
                **losses,
            }
        )
        episode_idx += len(samples)
        update_idx += 1

    metadata = {
        "model_version": "sp1-mappo-v5",
        "algorithm": "MAPPO with shared decentralized actor, centralized critic, behavior-cloning warm start, and quorum decoder",
        "training_id": training_id,
        "config_path": str(config_path),
        "pair_feature_names": PAIR_FEATURE_NAMES,
        "global_feature_names": GLOBAL_FEATURE_NAMES,
        "hidden_dim": hidden_dim,
        "train_seed_count": len(train_seeds),
        "validation_seed_count": len(validation_seeds),
        "test_seed_count": len(test_seeds),
        "total_episodes": total_episodes,
        "rollout_horizon": rollout_horizon,
        "ppo_epochs": ppo_epochs,
        "learning_rate": learning_rate,
        "clip_epsilon": clip_epsilon,
        "entropy_coef": entropy_coef,
        "value_coef": value_coef,
        "bc_pretrain_epochs": bc_pretrain_epochs,
        "bc_learning_rate": bc_learning_rate,
        "use_quorum_decoder": use_quorum_decoder,
        "rollout_action_mode": rollout_action_mode,
        "actor_trainable_parameters": _parameter_count(actor),
        "critic_trainable_parameters": _parameter_count(critic),
        "training_trainable_parameters": _parameter_count(actor) + _parameter_count(critic),
        "decoder_reward_weight": float(algorithm.get("decoder_reward_weight", 2.0)),
        "decoder_distance_weight": float(algorithm.get("decoder_distance_weight", 0.02)),
        "decoder_capacity_weight": float(algorithm.get("decoder_capacity_weight", 0.02)),
        "decoder_actor_weight": float(algorithm.get("decoder_actor_weight", 0.05)),
        "decoder_demand_weight": float(algorithm.get("decoder_demand_weight", 0.8)),
    }
    checkpoint_path = output_dir / "model.pt"
    torch.save(
        {
            "actor_state_dict": actor.state_dict(),
            "critic_state_dict": critic.state_dict(),
            "metadata": metadata,
        },
        checkpoint_path,
    )
    metadata["checkpoint_file"] = checkpoint_path.name
    model_path = output_dir / "model.json"
    model_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(output_dir / "training_history.csv", history, _columns(history))
    if bc_history:
        write_csv(output_dir / "bc_pretraining_history.csv", bc_history, _columns(bc_history))

    validation_rows = validate_mappo_checkpoint(
        model_path,
        generators=generators,
        seeds=validation_seeds,
        training_id=training_id,
    )
    write_csv(output_dir / "validation_runs.csv", validation_rows, _columns(validation_rows))
    validation_metrics = _validation_metric_summary(training_id, "validation", validation_rows, len(validation_seeds))
    save_json(output_dir / "validation_metrics.json", validation_metrics)
    metadata["validation"] = validation_metrics
    split_metrics = {"validation": validation_metrics}
    test_rows: list[dict[str, Any]] = []
    if test_seeds:
        test_rows = validate_mappo_checkpoint(
            model_path,
            generators=generators,
            seeds=test_seeds,
            training_id=training_id,
        )
        write_csv(output_dir / "test_runs.csv", test_rows, _columns(test_rows))
        test_metrics = _validation_metric_summary(training_id, "test", test_rows, len(test_seeds))
        save_json(output_dir / "test_metrics.json", test_metrics)
        metadata["test"] = test_metrics
        split_metrics["test"] = test_metrics
    quality_gates = evaluate_quality_gates(split_metrics, dict(config.get("quality_gates", {})))
    if quality_gates:
        save_json(output_dir / "quality_gates.json", {"checks": quality_gates, "passed": all(row["passed"] for row in quality_gates)})
        metadata["quality_gates"] = quality_gates
    model_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_mappo_readme(output_dir / "README.md", metadata)
    failed_gates = [row for row in quality_gates if not bool(row["passed"])]
    if failed_gates:
        names = ", ".join(f"{row['split']}.{row['metric']}" for row in failed_gates)
        raise ValueError(f"MAPPO quality gates failed: {names}")

    return {
        "training_id": training_id,
        "mode": "train_mappo",
        "checkpoint": str(model_path),
        "checkpoint_weights": str(checkpoint_path),
        "train_seed_count": len(train_seeds),
        "validation_seed_count": len(validation_seeds),
        "validation_runs": len(validation_rows),
        "test_seed_count": len(test_seeds),
        "test_runs": len(test_rows),
    }


def supervised_pretrain_actor(
    actor: PairActor,
    train_worlds: list[tuple[str, str, int, Any, Any]],
    *,
    epochs: int,
    learning_rate: float,
) -> list[dict[str, Any]]:
    """Warm-start the decentralized actor from centralized oracle labels."""

    optimizer = torch.optim.Adam(actor.parameters(), lr=learning_rate)
    history: list[dict[str, Any]] = []
    oracle = CentralizedCoalitionOracleAllocator()
    examples = []
    for _generator, _variant_id, _seed, params, world in train_worlds:
        context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius})
        oracle_assignment, _ = timed_allocate(oracle, context)
        pair_features, load_mask = pair_features_for_world(world, params.communication_radius)
        examples.append(
            (
                torch.as_tensor(pair_features, dtype=torch.float32),
                torch.as_tensor(load_mask, dtype=torch.bool),
                torch.as_tensor(oracle_assignment.labels, dtype=torch.long),
            )
        )
    for epoch in range(epochs):
        losses = []
        accuracies = []
        for pair_tensor, mask_tensor, target in examples:
            logits = actor(pair_tensor, mask_tensor)
            loss = nn.functional.cross_entropy(logits, target)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(actor.parameters(), 1.0)
            optimizer.step()
            prediction = torch.argmax(logits.detach(), dim=1)
            losses.append(float(loss.item()))
            accuracies.append(float(torch.mean((prediction == target).float()).item()))
        history.append(
            {
                "epoch": epoch,
                "bc_loss": float(np.mean(losses)),
                "bc_accuracy": float(np.mean(accuracies)),
            }
        )
    return history


def decode_quorum_assignment(
    world: Any,
    load_logits: np.ndarray,
    *,
    load_mask: np.ndarray,
    reward_weight: float = 2.0,
    distance_weight: float = 0.02,
    capacity_weight: float = 0.02,
    actor_weight: float = 0.05,
    demand_weight: float = 0.8,
) -> np.ndarray:
    """Decode actor logits into a complete-coalition SP1 assignment.

    The actor supplies learned pair scores; the decoder enforces executable
    SP1 recruitment semantics: complete load quorums, payload-capacity
    feasibility, and idle robots when demand is lower than fleet size. Extra
    AMRs are allowed only when they improve feasibility or the decoded score.
    """

    robot_count = len(world.robots)
    load_count = len(world.loads)
    labels = np.zeros(robot_count, dtype=int)
    if robot_count == 0 or load_count == 0:
        return labels

    demands = np.asarray([load.min_coalition_size for load in world.loads], dtype=int)
    rewards = np.asarray([load.reward for load in world.loads], dtype=float)
    payloads = np.asarray([robot.spec.capacity.payload_kg for robot in world.robots], dtype=float)
    required_capacity = np.asarray([load.min_capacity_kg for load in world.loads], dtype=float)
    robot_positions = np.vstack([robot.position for robot in world.robots])
    load_positions = np.vstack([load.pickup for load in world.loads])
    distances = np.linalg.norm(robot_positions[:, None, :] - load_positions[None, :, :], axis=2)

    best_score = -np.inf
    best_labels = labels.copy()
    found_candidate = False
    load_indices = range(load_count)
    for subset_size in range(1, load_count + 1):
        for subset in combinations(load_indices, subset_size):
            for slot_plan, extra_robots in iter_complete_slot_plans(demands, subset, robot_count):
                if not slot_plan:
                    continue
                slot_loads = tuple(int(load_idx) for load_idx in slot_plan)
                cost = np.zeros((robot_count, len(slot_loads)), dtype=float)
                for col, load_idx in enumerate(slot_loads):
                    invalid = ~load_mask[:, load_idx]
                    actor_score = load_logits[:, load_idx]
                    capacity_score = np.minimum(payloads, required_capacity[load_idx]) / max(required_capacity[load_idx], 1.0e-9)
                    utility = actor_weight * actor_score + capacity_weight * capacity_score - distance_weight * distances[:, load_idx]
                    utility[invalid] = -1.0e9
                    cost[:, col] = -utility
                rows, cols = linear_sum_assignment(cost)
                if rows.size < len(slot_loads):
                    continue
                assigned_cost = cost[rows, cols]
                if np.any(assigned_cost > 1.0e8):
                    continue
                candidate = np.zeros(robot_count, dtype=int)
                for row, col in zip(rows, cols):
                    candidate[int(row)] = int(slot_loads[int(col)]) + 1
                diagnostics = load_diagnostics(world, Assignment(labels=candidate, method="mappo_decoder"))
                selected_rows = [row for row in diagnostics if int(row["assigned_robots"]) > 0]
                subset_reward = float(np.sum(rewards[list(subset)]))
                served_reward = float(sum(row["reward"] for row in diagnostics if row["status"] in {"OK", "OVER"}))
                selected_under_penalty = float(
                    sum(row["robot_deficit"] for row in selected_rows)
                    + sum(row["capacity_deficit_kg"] for row in selected_rows) / 25.0
                )
                if selected_under_penalty > 1.0e-9:
                    continue
                assignment_distance = float(sum(distances[int(row), int(slot_loads[int(col)])] for row, col in zip(rows, cols)))
                decoder_mean_utility = -float(np.sum(assigned_cost)) / max(len(slot_loads), 1)
                required_slots = int(np.sum(demands[list(subset)]))
                score = (
                    reward_weight * served_reward
                    + 0.3 * subset_reward
                    + demand_weight * float(required_slots)
                    + decoder_mean_utility
                    - distance_weight * assignment_distance
                    - 2.0 * selected_under_penalty
                    - 0.05 * float(extra_robots)
                )
                if score > best_score:
                    best_score = score
                    best_labels = candidate
                    found_candidate = True
    if not found_candidate:
        return labels
    return best_labels


def collect_rollout_sample(
    actor: PairActor,
    critic: CentralCritic,
    world: Any,
    communication_radius: float,
    reward_config: dict[str, Any],
    *,
    use_quorum_decoder: bool,
    rollout_action_mode: str = "sampled_policy",
) -> RolloutSample:
    pair_features, load_mask = pair_features_for_world(world, communication_radius)
    global_features = global_features_for_world(world)
    pair_tensor = torch.as_tensor(pair_features, dtype=torch.float32)
    mask_tensor = torch.as_tensor(load_mask, dtype=torch.bool)
    global_tensor = torch.as_tensor(global_features, dtype=torch.float32)

    with torch.no_grad():
        logits = actor(pair_tensor, mask_tensor)
        distribution = Categorical(logits=logits)
        if rollout_action_mode == "decoder_guided" and use_quorum_decoder:
            decoded = decode_quorum_assignment(world, logits[:, 1:].cpu().numpy(), load_mask=load_mask)
            actions = torch.as_tensor(decoded, dtype=torch.int64)
        elif rollout_action_mode == "greedy_policy":
            actions = torch.argmax(logits, dim=1)
        else:
            actions = distribution.sample()
        joint_logprob = torch.sum(distribution.log_prob(actions))
        value = critic(global_tensor)

    assignment = Assignment(labels=actions.cpu().numpy().astype(int), method="mappo_recruitment")
    metrics = evaluate_assignment(
        world,
        assignment,
        runtime_ms=0.0,
        oracle_assignment=None,
        communication_radius=communication_radius,
    )
    reward = reward_from_metrics(metrics.to_dict(), world, reward_config)
    return RolloutSample(
        pair_features=pair_features,
        load_mask=load_mask,
        global_features=global_features,
        actions=actions.cpu().numpy().astype(int),
        old_joint_logprob=float(joint_logprob.item()),
        reward=float(reward),
        value=float(value.item()),
        metrics=metrics.to_dict(),
    )


def update_mappo(
    actor: PairActor,
    critic: CentralCritic,
    optimizer: torch.optim.Optimizer,
    samples: list[RolloutSample],
    *,
    clip_epsilon: float,
    entropy_coef: float,
    value_coef: float,
    ppo_epochs: int,
) -> dict[str, float]:
    rewards = torch.as_tensor([sample.reward for sample in samples], dtype=torch.float32)
    old_values = torch.as_tensor([sample.value for sample in samples], dtype=torch.float32)
    advantages = rewards - old_values
    if advantages.numel() > 1:
        advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1.0e-8)
    old_logprobs = torch.as_tensor([sample.old_joint_logprob for sample in samples], dtype=torch.float32)

    last_losses: dict[str, float] = {}
    for _ in range(ppo_epochs):
        policy_terms = []
        value_terms = []
        entropy_terms = []
        for idx, sample in enumerate(samples):
            pair_tensor = torch.as_tensor(sample.pair_features, dtype=torch.float32)
            mask_tensor = torch.as_tensor(sample.load_mask, dtype=torch.bool)
            global_tensor = torch.as_tensor(sample.global_features, dtype=torch.float32)
            action_tensor = torch.as_tensor(sample.actions, dtype=torch.int64)

            logits = actor(pair_tensor, mask_tensor)
            distribution = Categorical(logits=logits)
            new_joint_logprob = torch.sum(distribution.log_prob(action_tensor))
            ratio = torch.exp(new_joint_logprob - old_logprobs[idx])
            unclipped = ratio * advantages[idx]
            clipped = torch.clamp(ratio, 1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages[idx]
            policy_terms.append(-torch.minimum(unclipped, clipped))
            value = critic(global_tensor)
            value_terms.append((value - rewards[idx]) ** 2)
            entropy_terms.append(distribution.entropy().mean())

        policy_loss = torch.stack(policy_terms).mean()
        value_loss = torch.stack(value_terms).mean()
        entropy = torch.stack(entropy_terms).mean()
        loss = policy_loss + value_coef * value_loss - entropy_coef * entropy

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(list(actor.parameters()) + list(critic.parameters()), 1.0)
        optimizer.step()
        last_losses = {
            "loss": float(loss.item()),
            "policy_loss": float(policy_loss.item()),
            "value_loss": float(value_loss.item()),
            "entropy": float(entropy.item()),
        }
    return last_losses


def validate_mappo_checkpoint(
    checkpoint: Path,
    *,
    generators: list[str],
    seeds: list[int],
    training_id: str,
) -> list[dict[str, Any]]:
    allocator = MAPPORecruitmentAllocator(checkpoint=Path(checkpoint))
    rows: list[dict[str, Any]] = []
    for generator, variant_id, seed, params, world in iter_sp1_worlds(generators, seeds):
        context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius})
        oracle_assignment, _ = timed_allocate(CentralizedCoalitionOracleAllocator(), context)
        assignment, runtime_ms = timed_allocate(allocator, context)
        metrics = evaluate_assignment(
            world,
            assignment,
            runtime_ms=runtime_ms,
            oracle_assignment=oracle_assignment,
            communication_radius=params.communication_radius,
        )
        rows.append(
            {
                "training_id": training_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "demand_ratio": params.demand_ratio,
                **metrics.to_dict(),
            }
        )
    return rows


def _validation_metric_summary(
    training_id: str,
    split: str,
    rows: list[dict[str, Any]],
    seed_count: int,
) -> dict[str, Any]:
    return {
        "training_id": training_id,
        "split": split,
        f"{split}_seed_count": seed_count,
        f"{split}_runs": len(rows),
        "demand_satisfaction_ratio_mean": _mean(rows, "demand_satisfaction_ratio"),
        "coalition_success_rate_mean": _mean(rows, "coalition_success_rate"),
        "robots_underassigned_mean": _mean(rows, "robots_underassigned"),
        "robots_overassigned_mean": _mean(rows, "robots_overassigned"),
        "captured_reward_mean": _mean(rows, "captured_reward"),
        "optimality_gap_vs_oracle_mean": _mean(rows, "optimality_gap_vs_oracle"),
        "travel_distance_m_mean": _mean(rows, "travel_distance_m"),
        "estimated_arrival_time_s_mean": _mean(rows, "estimated_arrival_time_s"),
        "energy_proxy_wh_mean": _mean(rows, "energy_proxy_wh"),
        "runtime_ms_mean": _mean(rows, "runtime_ms"),
    }


def evaluate_quality_gates(
    split_metrics: dict[str, dict[str, Any]],
    gates: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split, split_gates in gates.items():
        metrics = split_metrics.get(str(split))
        if metrics is None:
            continue
        for name, threshold in dict(split_gates or {}).items():
            metric, direction = _parse_gate_name(str(name))
            value = float(metrics.get(metric, math.nan))
            target = float(threshold)
            passed = value >= target if direction == "min" else value <= target
            rows.append(
                {
                    "split": str(split),
                    "metric": metric,
                    "direction": direction,
                    "value": value,
                    "threshold": target,
                    "passed": bool(passed),
                }
            )
    return rows


def _parse_gate_name(name: str) -> tuple[str, str]:
    if name.endswith("_min"):
        return name[: -len("_min")], "min"
    if name.endswith("_max"):
        return name[: -len("_max")], "max"
    return name, "min"


def reward_from_metrics(metrics: dict[str, Any], world: Any, reward_config: dict[str, Any]) -> float:
    success_weight = float(reward_config.get("success_weight", 10.0))
    demand_weight = float(reward_config.get("demand_weight", 4.0))
    under_penalty = float(reward_config.get("underassigned_penalty", 5.0))
    over_penalty = float(reward_config.get("overassigned_penalty", 2.0))
    distance_penalty = float(reward_config.get("distance_penalty", 0.15))
    energy_penalty = float(reward_config.get("energy_penalty", 0.02))
    communication_penalty = float(reward_config.get("communication_penalty", 0.01))
    max_distance = max(float(world.map.size_m), 1.0) * max(len(world.robots), 1)
    max_energy = max_distance * 500.0 * 0.01
    max_messages = max(len(world.robots) * max(len(world.loads), 1), 1)
    return (
        success_weight * float(metrics["coalition_success_rate"])
        + demand_weight * float(metrics["demand_satisfaction_ratio"])
        + float(metrics["captured_reward"])
        - under_penalty * float(metrics["robots_underassigned"]) / max(len(world.robots), 1)
        - over_penalty * float(metrics["robots_overassigned"]) / max(len(world.robots), 1)
        - distance_penalty * float(metrics["assignment_cost"]) / max_distance
        - energy_penalty * float(metrics["energy_proxy_wh"]) / max(max_energy, 1.0e-9)
        - communication_penalty * float(metrics["communication_messages"]) / max_messages
    )


def pair_features_for_world(world: Any, communication_radius: float = np.inf) -> tuple[np.ndarray, np.ndarray]:
    robot_positions = np.vstack([robot.position for robot in world.robots]).astype(float)
    load_positions = np.vstack([load.pickup for load in world.loads]).astype(float)
    distances = np.linalg.norm(robot_positions[:, None, :] - load_positions[None, :, :], axis=2)
    rewards = np.asarray([load.reward for load in world.loads], dtype=float)
    demands = np.asarray([load.min_coalition_size for load in world.loads], dtype=float)
    required_capacity = np.asarray([load.min_capacity_kg for load in world.loads], dtype=float)
    capacities = np.asarray([robot.spec.capacity.payload_kg for robot in world.robots], dtype=float)
    visible = np.ones_like(distances, dtype=bool)
    if np.isfinite(communication_radius):
        visible = distances <= communication_radius
    load_mask = np.ones_like(visible, dtype=bool)
    features = np.zeros((len(world.robots), len(world.loads), len(PAIR_FEATURE_NAMES)), dtype=float)
    features[:, :, 0] = 1.0
    features[:, :, 1] = rewards[None, :] / 5.0
    features[:, :, 2] = demands[None, :] / max(float(len(world.robots)), 1.0)
    features[:, :, 3] = np.minimum(capacities[:, None], required_capacity[None, :]) / np.maximum(required_capacity[None, :], 1.0e-9)
    features[:, :, 4] = distances / max(float(world.map.size_m), 1.0)
    features[:, :, 5] = visible.astype(float)
    return features, load_mask


def global_features_for_world(world: Any) -> np.ndarray:
    robot_count = len(world.robots)
    load_count = len(world.loads)
    demands = np.asarray([load.min_coalition_size for load in world.loads], dtype=float)
    rewards = np.asarray([load.reward for load in world.loads], dtype=float)
    required = np.asarray([load.min_capacity_kg for load in world.loads], dtype=float)
    payloads = np.asarray([robot.spec.capacity.payload_kg for robot in world.robots], dtype=float)
    if robot_count and load_count:
        robot_positions = np.vstack([robot.position for robot in world.robots])
        load_positions = np.vstack([load.pickup for load in world.loads])
        mean_distance = float(np.mean(np.linalg.norm(robot_positions[:, None, :] - load_positions[None, :, :], axis=2)))
    else:
        mean_distance = 0.0
    return np.asarray(
        [
            robot_count / 12.0,
            load_count / 5.0,
            float(np.sum(demands)) / max(robot_count, 1),
            float(np.sum(payloads)) / max(float(np.sum(required)), 1.0e-9),
            float(np.mean(rewards)) / 5.0 if rewards.size else 0.0,
            float(np.std(payloads) / max(np.mean(payloads), 1.0e-9)) if payloads.size else 0.0,
            mean_distance / max(float(world.map.size_m), 1.0),
        ],
        dtype=float,
    )


def load_mappo_checkpoint(checkpoint: Path | None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if checkpoint is None:
        metadata = {
            "model_version": "sp1-mappo-untrained",
            "hidden_dim": 32,
            "pair_feature_names": PAIR_FEATURE_NAMES,
            "global_feature_names": GLOBAL_FEATURE_NAMES,
        }
        return metadata, None
    path = Path(checkpoint)
    if path.is_dir():
        metadata_path = path / "model.json"
    else:
        metadata_path = path
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    checkpoint_file = metadata.get("checkpoint_file", "model.pt")
    weights_path = metadata_path.parent / checkpoint_file
    state = torch.load(weights_path, map_location="cpu", weights_only=False)
    return metadata, state


def write_mappo_readme(path: Path, metadata: dict[str, Any]) -> None:
    validation = metadata.get("validation", {})
    test = metadata.get("test", {})
    lines = [
        f"# {metadata['training_id']}",
        "",
        "MAPPO-style CTDE checkpoint for SP1 recruitment.",
        "- Actor: shared decentralized AMR-load pair scorer.",
        "- Critic: centralized state-value network used only during training.",
        f"- PPO rollout action mode: `{metadata.get('rollout_action_mode', 'unknown')}`",
        f"- Execution quorum decoder: `{metadata.get('use_quorum_decoder', False)}`",
        f"- Actor parameters: `{metadata.get('actor_trainable_parameters', 0)}`",
        f"- Training parameters actor+critic: `{metadata.get('training_trainable_parameters', 0)}`",
        f"- Training episodes: `{metadata['total_episodes']}`",
        f"- Validation runs: `{validation.get('validation_runs', 0)}`",
        f"- Validation demand satisfaction: `{validation.get('demand_satisfaction_ratio_mean', math.nan):.4f}`",
        f"- Test runs: `{test.get('test_runs', 0)}`",
        f"- Test demand satisfaction: `{test.get('demand_satisfaction_ratio_mean', math.nan):.4f}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _seed_range(config: Any) -> list[int]:
    if isinstance(config, list):
        return [int(seed) for seed in config]
    start = int(config.get("start", 0))
    count = int(config.get("count", 1))
    return list(range(start, start + count))


def _columns(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({key for row in rows for key in row})


def _mean(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([float(row[metric]) for row in rows], dtype=float)
    return float(np.nanmean(values)) if values.size else math.nan


def _parameter_count(module: nn.Module) -> int:
    return int(sum(parameter.numel() for parameter in module.parameters() if parameter.requires_grad))
