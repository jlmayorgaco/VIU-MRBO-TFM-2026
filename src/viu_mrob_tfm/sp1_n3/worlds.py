"""N3 worlds are N2 worlds, with the positions N2 computed and discarded.

``sp1_n2_confirmatory.make_world`` returns ``(capacities, masses, distance)``
and drops the robot positions, which N3 needs to build an R-disk graph. It is
deterministic in ``seed``, so this module replays the identical RNG stream and
keeps the positions.

Nothing in ``n2_v1`` or ``scripts/sp1_n2_*.py`` is imported for its side
effects and nothing there is modified. The regression test in
``tests/test_sp1_n3_invariants.py`` asserts that the tuple this module derives
is bit-identical to the one N2's own function returns, so a drift in either
direction fails loudly instead of quietly producing different worlds.
"""

from __future__ import annotations

import hashlib
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = REPOSITORY_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import sp1_a1_hungarian as homogeneous  # noqa: E402


@dataclass(frozen=True, slots=True)
class World:
    """One N2 instance plus the geometry N3 needs for the graph."""

    world_id: str
    seed: int
    scenario: str
    capacity_cv: float
    pressure: float
    robot_positions: np.ndarray  # (N, 2)
    load_positions: np.ndarray  # (K, 2)
    capacities: np.ndarray  # (N,)
    demands: np.ndarray  # (K,)
    distances: np.ndarray  # (N, K)

    @property
    def n_robots(self) -> int:
        return len(self.capacities)

    @property
    def n_loads(self) -> int:
        return len(self.demands)

    @property
    def realized_cv(self) -> float:
        mean = float(self.capacities.mean())
        if mean == 0.0:
            return 0.0
        return float(self.capacities.std(ddof=0) / mean)

    def digest(self) -> str:
        """Content hash, so a stored world can be proved to be this world."""

        parts = [
            self.robot_positions.astype("<f8").tobytes(),
            self.load_positions.astype("<f8").tobytes(),
            self.capacities.astype("<f8").tobytes(),
            self.demands.astype("<f8").tobytes(),
        ]
        hasher = hashlib.sha256()
        for part in parts:
            hasher.update(part)
        return hasher.hexdigest()


def capacity_vector(
    robot_count: int, q_bar: float, cv: float, rng: np.random.Generator
) -> np.ndarray:
    """Byte-identical to N2's ``capacity_vector``.

    Lognormal capacities renormalized so total supply is exactly ``N * q_bar``
    at every CV, which is what makes CV the only thing that changes between
    heterogeneity levels.
    """

    supply = robot_count * q_bar
    if cv <= 0.0:
        return np.full(robot_count, q_bar, dtype=float)
    sigma = math.sqrt(math.log1p(cv * cv))
    raw = rng.lognormal(mean=0.0, sigma=sigma, size=robot_count)
    return raw * (supply / float(raw.sum()))


def make_world(
    *,
    world_id: str,
    robot_count: int,
    load_count: int,
    q_bar: float,
    cv: float,
    pressure: float,
    scenario: str,
    workspace: tuple[float, float],
    seed: int,
    alpha: float,
) -> World:
    """Replay N2's generator and keep the positions.

    The order of the draws matters: robot positions, then load positions, then
    the Dirichlet demand split, all from the spatial stream keyed by ``seed``;
    capacities come from their own stream keyed by ``(seed, cv)`` so geometry
    and masses stay identical across heterogeneity levels.
    """

    width, height = workspace
    spatial_rng = np.random.default_rng(seed)
    robot_positions = homogeneous.generate_positions(
        robot_count,
        role="robot",
        spatial_mode=scenario,
        workspace_width=width,
        workspace_height=height,
        rng=spatial_rng,
    )
    load_positions = homogeneous.generate_positions(
        load_count,
        role="load",
        spatial_mode=scenario,
        workspace_width=width,
        workspace_height=height,
        rng=spatial_rng,
    )
    supply = robot_count * q_bar
    masses = pressure * supply * spatial_rng.dirichlet(
        np.full(load_count, alpha)
    )
    capacity_rng = np.random.default_rng(
        homogeneous.stable_seed(seed, "n2-capacity", cv)
    )
    capacities = capacity_vector(robot_count, q_bar, cv, capacity_rng)
    distances = np.linalg.norm(
        robot_positions[:, None, :] - load_positions[None, :, :], axis=2
    )
    return World(
        world_id=world_id,
        seed=int(seed),
        scenario=scenario,
        capacity_cv=float(cv),
        pressure=float(pressure),
        robot_positions=robot_positions,
        load_positions=load_positions,
        capacities=capacities,
        demands=masses,
        distances=distances,
    )


def n2_reference(
    *,
    robot_count: int,
    load_count: int,
    q_bar: float,
    cv: float,
    pressure: float,
    scenario: str,
    workspace: tuple[float, float],
    seed: int,
    alpha: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Call N2's own frozen generator, for the regression test to compare against."""

    import sp1_n2_confirmatory as n2  # imported lazily; never modified

    return n2.make_world(
        robot_count=robot_count,
        load_count=load_count,
        q_bar=q_bar,
        cv=cv,
        pressure=pressure,
        scenario=scenario,
        workspace=workspace,
        seed=seed,
        alpha=alpha,
    )


def load_count_for(robot_count: int) -> int:
    """``K = round(0.3 N)``, frozen here so E4 cannot reinterpret it.

    ``3N/10`` is not an integer for the E4 sizes, and leaving the rounding
    implicit would let two scripts disagree about what ``N = 50`` means.
    """

    return max(1, int(round(0.3 * float(robot_count))))


__all__ = [
    "World",
    "capacity_vector",
    "load_count_for",
    "make_world",
    "n2_reference",
]
