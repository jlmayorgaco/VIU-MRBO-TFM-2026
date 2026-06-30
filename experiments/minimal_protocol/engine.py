"""Minimal fluid engines for the isolated TFM validation protocol.

The classes in this module are intentionally independent from the warehouse
benchmark. They keep only the mechanisms needed by H1, H2, and H3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.optimize import brentq
from scipy.special import expit


Array = np.ndarray


class FluidEngine:
    """Population-game Smith dynamics over idle plus K task choices."""

    def __init__(
        self,
        r: Iterable[float],
        n: Iterable[float],
        N: int,
        beta: float = 2.0,
        r0: float = 0.05,
    ) -> None:
        self.r = np.asarray(r, dtype=float)
        self.n = np.asarray(n, dtype=float)
        self.N = int(N)
        self.K = int(len(self.r))
        self.beta = float(beta)
        self.r0 = float(r0)
        if self.r.shape != self.n.shape:
            raise ValueError("r and n must have the same shape")
        if self.K == 0:
            raise ValueError("at least one task is required")
        if self.N <= 0:
            raise ValueError("N must be positive")

    def Phi(self, z: Array) -> Array:
        """Decreasing sigmoid of task surplus."""

        return expit(-self.beta * (np.asarray(z, dtype=float) - self.n))

    def water_filling(self, prices: Array | None = None) -> tuple[Array, float]:
        """Closed-form water-filling prediction for the static game."""

        rv = self.r if prices is None else np.asarray(prices, dtype=float)

        def Wk(lam: float) -> Array:
            with np.errstate(divide="ignore", invalid="ignore"):
                inner = np.where(
                    lam < rv,
                    self.n
                    + np.log(np.clip(rv / lam - 1.0, 1e-12, None)) / self.beta,
                    0.0,
                )
            return np.maximum(inner, 0.0)

        z_abundant = Wk(self.r0)
        if float(z_abundant.sum()) <= self.N + 1e-9:
            return z_abundant, self.r0

        lam = brentq(lambda value: float(Wk(value).sum()) - self.N, 1e-6, float(max(rv)) - 1e-9)
        return Wk(lam), float(lam)

    def run_smith(
        self,
        T: float = 1500.0,
        dt: float = 0.02,
        price_gain: float = 0.0,
        q: Array | None = None,
        integer_clearing: bool = False,
        record: bool = False,
        tol: float = 1e-9,
        burn_fraction: float = 0.5,
    ) -> tuple[Array, Array | None, Array, dict[str, float]]:
        """Integrate Smith dynamics and optionally summarize post-burn-in waste."""

        x = np.ones(self.K + 1, dtype=float) / (self.K + 1)
        p = self.r.copy()
        target = self.n + 1.0 if q is None else np.asarray(q, dtype=float)
        hist: list[Array] = []
        post_waste_fractional: list[float] = []
        post_waste_integer: list[float] = []
        steps = int(T / dt)
        burn_step = int(burn_fraction * steps)

        for step in range(steps):
            z = self.N * x[1:]
            z_eff = np.floor(z + 1e-9) if integer_clearing else z
            rv = p if price_gain > 0.0 else self.r
            F = np.concatenate([[self.r0], rv * self.Phi(z_eff)])
            M = np.maximum(F[:, None] - F[None, :], 0.0)
            dx = M @ x - x * M.sum(0)
            x = np.clip(x + dt * dx, 0.0, None)
            x /= x.sum()

            if price_gain > 0.0:
                p = np.clip(p + dt * price_gain * (target - z), self.r0, 50.0)

            if record and step % max(1, steps // 300) == 0:
                hist.append((self.N * x[1:]).copy())

            if integer_clearing and step >= burn_step:
                z_now = self.N * x[1:]
                z_floor = np.floor(z_now + 1e-9)
                post_waste_fractional.append(float(z_now[z_now < self.n].sum()))
                post_waste_integer.append(float(z_floor[z_floor < self.n].sum()))

            if (
                step > 50
                and np.max(np.abs(dx)) < tol
                and price_gain == 0.0
                and not integer_clearing
            ):
                break

        summary = {
            "post_waste_fractional": float(np.mean(post_waste_fractional))
            if post_waste_fractional
            else float("nan"),
            "post_waste_integer": float(np.mean(post_waste_integer))
            if post_waste_integer
            else float("nan"),
        }
        return self.N * x[1:], (np.array(hist) if record else None), p, summary


@dataclass(frozen=True)
class ArrivalSpec:
    """Typed arrival event for the temporal H3-B engine."""

    time: float
    task_type: int
    deadline: float


class ArrivalEngine:
    """Fluid Smith dynamics with task arrivals, completions, and expirations."""

    def __init__(
        self,
        r: Iterable[float],
        n: Iterable[float],
        N: int,
        arrivals: list[ArrivalSpec],
        beta: float = 2.0,
        r0: float = 0.05,
    ) -> None:
        self.r = np.asarray(r, dtype=float)
        self.n = np.asarray(n, dtype=float)
        self.N = int(N)
        self.arrivals = sorted(arrivals, key=lambda item: item.time)
        self.beta = float(beta)
        self.r0 = float(r0)
        if self.r.shape != self.n.shape:
            raise ValueError("r and n must have the same shape")

    @staticmethod
    def generate_arrivals(
        seed: int,
        horizon: float,
        rates: Iterable[float],
        deadlines: Iterable[float],
    ) -> list[ArrivalSpec]:
        """Generate one paired Poisson arrival sequence for all treatments."""

        rng = np.random.default_rng(seed)
        rates_arr = np.asarray(rates, dtype=float)
        deadlines_arr = np.asarray(deadlines, dtype=float)
        arrivals: list[ArrivalSpec] = []
        for task_type, rate in enumerate(rates_arr):
            if rate <= 0.0:
                continue
            t = float(rng.exponential(1.0 / rate))
            while t < horizon:
                arrivals.append(
                    ArrivalSpec(
                        time=t,
                        task_type=task_type,
                        deadline=t + float(deadlines_arr[task_type]),
                    )
                )
                t += float(rng.exponential(1.0 / rate))
        return sorted(arrivals, key=lambda item: item.time)

    def run(
        self,
        price_gain: float,
        horizon: float = 500.0,
        dt: float = 0.05,
    ) -> dict[str, float]:
        """Run one temporal scenario and return delivered-value metrics."""

        x = np.array([1.0], dtype=float)
        active_types: list[int] = []
        active_deadlines: list[float] = []
        active_prices: list[float] = []
        delivered_value = 0.0
        total_value = float(sum(self.r[event.task_type] for event in self.arrivals))
        expired_value = 0.0
        next_arrival = 0
        steps = int(horizon / dt)

        for step in range(steps):
            t = step * dt
            while next_arrival < len(self.arrivals) and self.arrivals[next_arrival].time <= t + 1e-12:
                event = self.arrivals[next_arrival]
                active_types.append(event.task_type)
                active_deadlines.append(event.deadline)
                active_prices.append(float(self.r[event.task_type]))
                x = np.concatenate([x, [0.0]])
                next_arrival += 1

            if active_types:
                types = np.asarray(active_types, dtype=int)
                z = self.N * x[1:]
                rewards = np.asarray(active_prices, dtype=float) if price_gain > 0.0 else self.r[types]
                task_payoffs = rewards * expit(-self.beta * (z - self.n[types]))
                F = np.concatenate([[self.r0], task_payoffs])
            else:
                F = np.array([self.r0], dtype=float)

            M = np.maximum(F[:, None] - F[None, :], 0.0)
            dx = M @ x - x * M.sum(0)
            x = np.clip(x + dt * dx, 0.0, None)
            x /= x.sum()

            if active_types and price_gain > 0.0:
                z = self.N * x[1:]
                for idx, task_type in enumerate(active_types):
                    deficit = self.n[task_type] - z[idx]
                    active_prices[idx] = float(
                        np.clip(active_prices[idx] + dt * price_gain * deficit, self.r0, 50.0)
                    )

            if active_types:
                z = self.N * x[1:]
                remove: list[int] = []
                for idx, task_type in enumerate(active_types):
                    if z[idx] >= self.n[task_type]:
                        delivered_value += float(self.r[task_type])
                        remove.append(idx)
                    elif t >= active_deadlines[idx]:
                        expired_value += float(self.r[task_type])
                        remove.append(idx)

                if remove:
                    remove_set = set(remove)
                    keep = [idx for idx in range(len(active_types)) if idx not in remove_set]
                    idle_mass = float(x[0] + sum(x[1 + idx] for idx in remove))
                    x = np.concatenate([[idle_mass], [x[1 + idx] for idx in keep]])
                    active_types = [active_types[idx] for idx in keep]
                    active_deadlines = [active_deadlines[idx] for idx in keep]
                    active_prices = [active_prices[idx] for idx in keep]
                    x /= x.sum()

        return {
            "delivered_value_ratio": delivered_value / total_value if total_value > 0.0 else float("nan"),
            "delivered_value": delivered_value,
            "expired_value": expired_value,
            "total_value": total_value,
            "arrivals": float(len(self.arrivals)),
        }
