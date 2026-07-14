"""Scenario generation for SP0 homogeneous one-to-one assignment."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass(frozen=True, slots=True)
class SP0World:
    """One SP0 world with cached graph and oracle data."""

    sp_id: str
    world_seed: int
    geometry_id: str
    n_robots: int
    n_loads: int
    side_length: float
    robot_xy: np.ndarray
    load_xy: np.ndarray
    cost: np.ndarray
    adjacency: np.ndarray
    radius: float
    mean_degree: float
    min_degree: int
    lambda2: float
    num_components: int
    diameter: float
    initial_x: np.ndarray
    oracle_labels: np.ndarray
    oracle_social_cost: float
    oracle_j: float
    world_hash: str

    @property
    def s_star(self) -> int:
        return min(self.n_robots, self.n_loads)

    @property
    def load_ratio(self) -> float:
        return float(self.n_loads / max(self.n_robots, 1))


@dataclass(frozen=True, slots=True)
class WorldPublicView:
    """Read-only world data available to every non-oracle method."""

    sp_id: str
    world_seed: int
    geometry_id: str
    n_robots: int
    n_loads: int
    side_length: float
    robot_xy: np.ndarray
    load_xy: np.ndarray
    cost: np.ndarray
    adjacency: np.ndarray
    radius: float
    mean_degree: float
    min_degree: int
    lambda2: float
    num_components: int
    diameter: float
    initial_x: np.ndarray
    world_hash: str

    @property
    def s_star(self) -> int:
        return min(self.n_robots, self.n_loads)

    @property
    def load_ratio(self) -> float:
        return float(self.n_loads / max(self.n_robots, 1))


WorldOracleView = SP0World


def public_world_view(world: SP0World) -> WorldPublicView:
    """Create an immutable view without oracle labels, costs, or regret references."""

    def readonly(array: np.ndarray) -> np.ndarray:
        view = np.asarray(array).view()
        view.flags.writeable = False
        return view

    return WorldPublicView(
        sp_id=world.sp_id,
        world_seed=world.world_seed,
        geometry_id=world.geometry_id,
        n_robots=world.n_robots,
        n_loads=world.n_loads,
        side_length=world.side_length,
        robot_xy=readonly(world.robot_xy),
        load_xy=readonly(world.load_xy),
        cost=readonly(world.cost),
        adjacency=readonly(world.adjacency),
        radius=world.radius,
        mean_degree=world.mean_degree,
        min_degree=world.min_degree,
        lambda2=world.lambda2,
        num_components=world.num_components,
        diameter=world.diameter,
        initial_x=readonly(world.initial_x),
        world_hash=world.world_hash,
    )


def make_sp0_world(
    *,
    n_robots: int,
    n_loads: int,
    seed: int,
    geometry_id: str = "G-UNI",
    mean_degree_target: float | str | None = None,
    sp_id: str = "SP0-v1.0",
) -> SP0World:
    """Build a deterministic SP0 world."""

    if n_robots <= 0:
        raise ValueError("SP0 requires at least one robot.")
    if n_loads <= 0:
        raise ValueError("SP0 requires at least one load.")

    geometry = str(geometry_id).upper()
    rng = np.random.default_rng(int(seed))
    side = 10.0 * math.sqrt(n_robots / 16.0)
    robot_xy, load_xy = _positions_for_geometry(rng, geometry, n_robots, n_loads, side)
    cost = np.linalg.norm(robot_xy[:, None, :] - load_xy[None, :, :], axis=2) / (math.sqrt(2.0) * side)
    cost = np.clip(cost, 0.0, 1.0)
    adjacency, radius = _rdisk_graph(robot_xy, mean_degree_target)
    mean_degree, min_degree, lambda2, num_components, diameter = _graph_stats(adjacency)
    initial_x = _initial_state(cost, geometry)
    oracle_labels, oracle_social_cost, oracle_j = _oracle_assignment(cost)
    world_hash = _world_hash(
        {
            "sp_id": sp_id,
            "seed": int(seed),
            "geometry": geometry,
            "n_robots": int(n_robots),
            "n_loads": int(n_loads),
            "side_length": round(float(side), 10),
            "robot_xy": np.round(robot_xy, 10).tolist(),
            "load_xy": np.round(load_xy, 10).tolist(),
            "adjacency": adjacency.astype(int).tolist(),
        }
    )
    return SP0World(
        sp_id=sp_id,
        world_seed=int(seed),
        geometry_id=geometry,
        n_robots=int(n_robots),
        n_loads=int(n_loads),
        side_length=float(side),
        robot_xy=robot_xy,
        load_xy=load_xy,
        cost=cost,
        adjacency=adjacency,
        radius=float(radius),
        mean_degree=float(mean_degree),
        min_degree=int(min_degree),
        lambda2=float(lambda2),
        num_components=int(num_components),
        diameter=float(diameter),
        initial_x=initial_x,
        oracle_labels=oracle_labels,
        oracle_social_cost=float(oracle_social_cost),
        oracle_j=float(oracle_j),
        world_hash=world_hash,
    )


def _positions_for_geometry(
    rng: np.random.Generator,
    geometry: str,
    n_robots: int,
    n_loads: int,
    side: float,
) -> tuple[np.ndarray, np.ndarray]:
    if geometry == "G-CLU":
        return _clustered_positions(rng, n_robots, n_loads, side)
    if geometry == "G-TIE":
        return _tie_positions(rng, n_robots, n_loads, side)
    if geometry == "G-X":
        return _cross_positions(rng, n_robots, n_loads, side)
    robot_xy = rng.uniform(0.0, side, size=(n_robots, 2))
    load_xy = rng.uniform(0.0, side, size=(n_loads, 2))
    return robot_xy, load_xy


def _clustered_positions(
    rng: np.random.Generator,
    n_robots: int,
    n_loads: int,
    side: float,
) -> tuple[np.ndarray, np.ndarray]:
    centers = rng.uniform(0.18 * side, 0.82 * side, size=(3, 2))
    robot_centers = centers[rng.integers(0, centers.shape[0], size=n_robots)]
    load_centers = centers[rng.integers(0, centers.shape[0], size=n_loads)]
    sigma = 0.08 * side
    robot_xy = np.clip(robot_centers + rng.normal(0.0, sigma, size=(n_robots, 2)), 0.0, side)
    load_xy = np.clip(load_centers + rng.normal(0.0, sigma, size=(n_loads, 2)), 0.0, side)
    return robot_xy, load_xy


def _tie_positions(
    rng: np.random.Generator,
    n_robots: int,
    n_loads: int,
    side: float,
) -> tuple[np.ndarray, np.ndarray]:
    center = np.array([0.5 * side, 0.5 * side])
    robot_angles = np.linspace(0.0, 2.0 * math.pi, n_robots, endpoint=False)
    load_angles = np.linspace(math.pi / max(n_loads, 1), 2.0 * math.pi + math.pi / max(n_loads, 1), n_loads, endpoint=False)
    radius = 0.24 * side
    robot_xy = center + radius * np.column_stack([np.cos(robot_angles), np.sin(robot_angles)])
    load_xy = center + radius * np.column_stack([np.cos(load_angles), np.sin(load_angles)])
    robot_xy += rng.normal(0.0, 0.01 * side, size=robot_xy.shape)
    load_xy += rng.normal(0.0, 0.01 * side, size=load_xy.shape)
    return np.clip(robot_xy, 0.0, side), np.clip(load_xy, 0.0, side)


def _cross_positions(
    rng: np.random.Generator,
    n_robots: int,
    n_loads: int,
    side: float,
) -> tuple[np.ndarray, np.ndarray]:
    robot_xy = rng.uniform(0.0, side, size=(n_robots, 2))
    load_xy = rng.uniform(0.0, side, size=(n_loads, 2))
    if n_robots >= 2 and n_loads >= 2:
        robot_xy[0] = [0.20 * side, 0.20 * side]
        robot_xy[1] = [0.80 * side, 0.80 * side]
        load_xy[0] = [0.82 * side, 0.24 * side]
        load_xy[1] = [0.24 * side, 0.82 * side]
    return robot_xy, load_xy


def _initial_state(cost: np.ndarray, geometry: str) -> np.ndarray:
    n_robots, n_loads = cost.shape
    x = np.full((n_robots, n_loads + 1), 1.0 / (n_loads + 1.0), dtype=float)
    if geometry == "G-BIAS":
        x.fill(0.25 / max(n_loads, 1))
        x[:, 0] = 0.05
        nearest = np.argmin(cost, axis=1)
        x[np.arange(n_robots), nearest + 1] = 0.70
        x /= np.sum(x, axis=1, keepdims=True)
    elif geometry == "G-ZERO" and n_loads >= 1:
        x[:, 1] = 0.0
        x /= np.sum(x, axis=1, keepdims=True)
    return x


def _rdisk_graph(robot_xy: np.ndarray, mean_degree_target: float | str | None) -> tuple[np.ndarray, float]:
    n_robots = int(robot_xy.shape[0])
    if n_robots <= 1:
        return np.zeros((n_robots, n_robots), dtype=bool), 0.0
    distances = np.linalg.norm(robot_xy[:, None, :] - robot_xy[None, :, :], axis=2)
    off_diag = distances[~np.eye(n_robots, dtype=bool)]
    if mean_degree_target is None or str(mean_degree_target).lower() in {"all", "global", "complete"}:
        radius = float(np.max(off_diag) + 1.0e-9)
        adjacency = (distances <= radius) & (~np.eye(n_robots, dtype=bool))
        return adjacency, radius
    target = float(mean_degree_target)
    target = min(max(target, 0.0), float(n_robots - 1))
    lo, hi = 0.0, float(np.max(off_diag) + 1.0e-9)
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        mean_degree = float(np.sum((distances <= mid) & (~np.eye(n_robots, dtype=bool))) / n_robots)
        if mean_degree < target:
            lo = mid
        else:
            hi = mid
    radius = hi
    adjacency = (distances <= radius) & (~np.eye(n_robots, dtype=bool))
    return adjacency, float(radius)


def _graph_stats(adjacency: np.ndarray) -> tuple[float, int, float, int, float]:
    n_robots = int(adjacency.shape[0])
    if n_robots == 0:
        return 0.0, 0, 0.0, 0, math.nan
    degrees = np.sum(adjacency, axis=1)
    laplacian = np.diag(degrees.astype(float)) - adjacency.astype(float)
    eigenvalues = np.linalg.eigvalsh(laplacian)
    lambda2 = float(eigenvalues[1]) if n_robots > 1 else 0.0
    components = _components(adjacency)
    diameter = _diameter(adjacency) if components == 1 else math.nan
    return float(np.mean(degrees)), int(np.min(degrees)), lambda2, int(components), float(diameter)


def _components(adjacency: np.ndarray) -> int:
    n_robots = int(adjacency.shape[0])
    visited = np.zeros(n_robots, dtype=bool)
    count = 0
    for start in range(n_robots):
        if visited[start]:
            continue
        count += 1
        stack = [start]
        visited[start] = True
        while stack:
            node = stack.pop()
            for nxt in np.flatnonzero(adjacency[node]):
                if not visited[int(nxt)]:
                    visited[int(nxt)] = True
                    stack.append(int(nxt))
    return count


def _diameter(adjacency: np.ndarray) -> float:
    n_robots = int(adjacency.shape[0])
    best = 0
    for start in range(n_robots):
        dist = np.full(n_robots, -1, dtype=int)
        dist[start] = 0
        queue = [start]
        head = 0
        while head < len(queue):
            node = queue[head]
            head += 1
            for nxt in np.flatnonzero(adjacency[node]):
                if dist[int(nxt)] < 0:
                    dist[int(nxt)] = dist[node] + 1
                    queue.append(int(nxt))
        best = max(best, int(np.max(dist)))
    return float(best)


def _oracle_assignment(cost: np.ndarray) -> tuple[np.ndarray, float, float]:
    n_robots, n_loads = cost.shape
    labels = np.zeros(n_robots, dtype=int)
    row_ind, col_ind = linear_sum_assignment(cost)
    for row, col in zip(row_ind, col_ind):
        labels[int(row)] = int(col) + 1
    social_cost = float(np.sum(cost[np.arange(n_robots)[labels > 0], labels[labels > 0] - 1]))
    s_star = min(n_robots, n_loads)
    j_value = float((s_star + 1.0) * (s_star - np.sum(labels > 0)) + social_cost)
    return labels, social_cost, j_value


def _world_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
