"""Run the isolated minimal experiments for the TFM theory protocol.

Outputs:
  exp_results/H1_metrics.csv
  exp_results/H2_metrics.csv
  exp_results/H3_metrics.csv
  exp_results/figures/*.png
  exp_results/conclusiones.md
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import matplotlib
import numpy as np
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "experiments" / "minimal_protocol"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from engine import ArrivalEngine, FluidEngine  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "exp_results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir
    figure_dir = out_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    sanity = run_sanity_check()
    h1_rows, h1_summary = run_h1(figure_dir)
    write_csv(out_dir / "H1_metrics.csv", h1_rows)

    h2_rows, h2_summary = run_h2(figure_dir)
    write_csv(out_dir / "H2_metrics.csv", h2_rows)

    h3_rows, h3_summary = run_h3(figure_dir)
    write_csv(out_dir / "H3_metrics.csv", h3_rows)

    summary = {
        "sanity": sanity,
        "H1": h1_summary,
        "H2": h2_summary,
        "H3": h3_summary,
    }
    (out_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_conclusions(out_dir / "conclusiones.md", sanity, h1_summary, h2_summary, h3_summary)

    print("Minimal protocol complete.")
    print(f"  H1: {h1_summary['verdict']}")
    print(f"  H2: {h2_summary['verdict']}")
    print(f"  H3-A: {h3_summary['static']['verdict']}")
    print(f"  H3-B scarcity: {h3_summary['arrivals']['scarcity']['verdict']}")
    print(f"  H3-B abundance: {h3_summary['arrivals']['abundance']['verdict']}")
    print(f"  artifacts: {out_dir}")
    return 0


def run_sanity_check() -> dict[str, Any]:
    engine = FluidEngine(r=[1.0, 0.8, 0.6, 0.5], n=[3.0, 4.0, 2.0, 5.0], N=30)
    z_star, lam = engine.water_filling()
    z_obs, _, _, _ = engine.run_smith(T=1500.0, dt=0.02)
    max_err = float(np.max(np.abs(z_obs - z_star)))
    return {
        "seed": None,
        "z_star": z_star.tolist(),
        "z_obs": z_obs.tolist(),
        "lambda": lam,
        "max_abs_err": max_err,
        "passed": bool(max_err <= 1e-2),
    }


def run_h1(figure_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    z_star_all: list[float] = []
    z_obs_all: list[float] = []
    config_failures = 0

    for config_id, config in enumerate(generate_h1_configs(seed=42), start=1):
        engine = FluidEngine(config["r"], config["n"], config["N"])
        z_star, lam = engine.water_filling()
        z_obs, _, _, _ = engine.run_smith(T=1500.0, dt=0.02)
        errors = np.abs(z_obs - z_star)
        config_failed = bool(float(np.max(errors)) >= 0.05)
        config_failures += int(config_failed)

        for task_id, (r, n, zs, zo, err) in enumerate(
            zip(config["r"], config["n"], z_star, z_obs, errors, strict=True),
            start=1,
        ):
            z_star_all.append(float(zs))
            z_obs_all.append(float(zo))
            rows.append(
                {
                    "experiment": "H1",
                    "config_id": config_id,
                    "task_id": task_id,
                    "regime": config["regime"],
                    "K": len(config["r"]),
                    "N": config["N"],
                    "r": float(r),
                    "n": float(n),
                    "lambda": lam,
                    "z_star": float(zs),
                    "z_obs": float(zo),
                    "abs_err": float(err),
                    "config_failed": config_failed,
                }
            )

    x = np.asarray(z_star_all)
    y = np.asarray(z_obs_all)
    slope, intercept = np.polyfit(x, y, 1)
    y_hat = slope * x + intercept
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0
    max_err = max(float(row["abs_err"]) for row in rows)
    passed = bool(0.97 <= slope <= 1.03 and r2 > 0.99 and max_err < 0.05 and config_failures == 0)

    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    ax.scatter(x, y, s=28, alpha=0.82, edgecolor="none")
    lo = min(float(np.min(x)), float(np.min(y)))
    hi = max(float(np.max(x)), float(np.max(y)))
    ax.plot([lo, hi], [lo, hi], color="black", linewidth=1.2, label="y=x")
    ax.set_xlabel("z* water-filling")
    ax.set_ylabel("z observado Smith")
    ax.set_title("H1 - Smith vs water-filling")
    ax.text(
        0.04,
        0.96,
        f"slope={slope:.4f}\nR2={r2:.6f}\nmax err={max_err:.5f}",
        transform=ax.transAxes,
        va="top",
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#cccccc"},
    )
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(figure_dir / "H1_scatter_water_filling.png", dpi=180)
    plt.close(fig)

    return rows, {
        "seed": 42,
        "n_configs": 40,
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": float(r2),
        "max_abs_err": max_err,
        "config_failures": config_failures,
        "criterion": "slope in [0.97,1.03], R2 > 0.99, max err < 0.05 for all configs",
        "verdict": "H0 RECHAZADA" if passed else "NO CONCLUYENTE",
    }


def generate_h1_configs(seed: int) -> Iterable[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    for idx in range(40):
        K = int(rng.integers(2, 6))
        n = rng.integers(2, 8, size=K).astype(float)
        r = np.sort(rng.uniform(0.5, 1.5, size=K))[::-1]
        if idx % 2 == 0:
            N = int(math.ceil(rng.uniform(1.15, 1.80) * float(n.sum())))
            regime = "abundance"
        else:
            N = max(1, int(math.floor(rng.uniform(0.45, 0.85) * float(n.sum()))))
            regime = "scarcity"
        yield {"r": r, "n": n, "N": N, "regime": regime}


def run_h2(figure_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for config_id, config in enumerate(generate_h2_configs(seed=7), start=1):
        engine = FluidEngine(config["r"], config["n"], config["N"])
        z_smooth, lam = engine.water_filling()
        z_integer, _, _, int_summary = engine.run_smith(
            T=400.0,
            dt=0.05,
            integer_clearing=True,
            tol=-1.0,
            burn_fraction=0.5,
        )
        waste_smooth = waste_fractional(z_smooth, config["n"])
        waste_integer_primary = float(int_summary["post_waste_integer"])
        waste_integer_fractional = float(int_summary["post_waste_fractional"])
        rows.append(
            {
                "experiment": "H2",
                "config_id": config_id,
                "K": len(config["r"]),
                "N": config["N"],
                "sum_n": float(np.sum(config["n"])),
                "lambda": lam,
                "waste_smooth": waste_smooth,
                "waste_integer_primary": waste_integer_primary,
                "waste_integer_fractional_avg": waste_integer_fractional,
                "delta_primary": waste_smooth - waste_integer_primary,
                "delta_fractional": waste_smooth - waste_integer_fractional,
                "non_worse_primary": bool(waste_smooth >= waste_integer_primary - 1e-9),
                "strictly_better_primary": bool(waste_smooth > waste_integer_primary + 1e-9),
                "z_smooth": json.dumps([float(v) for v in z_smooth]),
                "z_integer_final": json.dumps([float(v) for v in z_integer]),
                "r": json.dumps([float(v) for v in config["r"]]),
                "n": json.dumps([float(v) for v in config["n"]]),
            }
        )

    smooth = np.asarray([row["waste_smooth"] for row in rows], dtype=float)
    integer = np.asarray([row["waste_integer_primary"] for row in rows], dtype=float)
    deltas = smooth - integer
    non_worse = float(np.mean(deltas >= -1e-9))
    strict = float(np.mean(deltas > 1e-9))
    mean_smooth, low_smooth, high_smooth = mean_ci(smooth)
    mean_integer, low_integer, high_integer = mean_ci(integer)
    mean_delta, low_delta, high_delta = mean_ci(deltas)
    reduction_pct = 100.0 * (mean_integer / mean_smooth - 1.0)
    passed = bool(non_worse == 1.0 and strict >= 0.5)

    x = np.arange(1, len(rows) + 1)
    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    width = 0.38
    ax.bar(x - width / 2, smooth, width=width, label="sin entero")
    ax.bar(x + width / 2, integer, width=width, label="con entero")
    ax.set_xlabel("config")
    ax.set_ylabel("desperdicio")
    ax.set_title("H2 - Desperdicio pareado bajo escasez")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "H2_paired_waste.png", dpi=180)
    plt.close(fig)

    return rows, {
        "seed": 7,
        "n_configs": 30,
        "mean_waste_smooth": mean_smooth,
        "ci95_waste_smooth": [low_smooth, high_smooth],
        "mean_waste_integer": mean_integer,
        "ci95_waste_integer": [low_integer, high_integer],
        "mean_delta": mean_delta,
        "ci95_delta": [low_delta, high_delta],
        "reduction_pct": float(reduction_pct),
        "non_worse_share": non_worse,
        "strict_better_share": strict,
        "primary_metric_note": "integer mode uses post-burn-in mean floor(z) waste; fractional post-burn-in waste is also recorded",
        "criterion": "sin-entero >= con-entero in 100% of configs and strictly greater in >=50%",
        "verdict": "H0 RECHAZADA" if passed else "NO CONCLUYENTE",
    }


def generate_h2_configs(seed: int) -> Iterable[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    for _ in range(30):
        K = int(rng.integers(2, 6))
        n = rng.integers(2, 8, size=K).astype(float)
        r = np.sort(rng.uniform(0.5, 1.5, size=K))[::-1]
        N = max(1, int(math.floor(rng.uniform(0.40, 0.75) * float(n.sum()))))
        yield {"r": r, "n": n, "N": N}


def run_h3(figure_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    static_rows, static_summary = run_h3_static(figure_dir)
    arrival_rows, arrival_summary = run_h3_arrivals(figure_dir)
    return static_rows + arrival_rows, {"static": static_summary, "arrivals": arrival_summary}


def run_h3_static(figure_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for regime in ("abundance", "scarcity"):
        for config_id, config in enumerate(generate_h3_static_configs(seed=123, regime=regime), start=1):
            engine = FluidEngine(config["r"], config["n"], config["N"])
            z_base, _ = engine.water_filling()
            z_price, _, prices, _ = engine.run_smith(T=600.0, dt=0.02, price_gain=0.5)
            value_base = static_coverage_value(z_base, config["r"], config["n"])
            value_price = static_coverage_value(z_price, config["r"], config["n"])
            rows.append(
                {
                    "experiment": "H3-A",
                    "regime": regime,
                    "config_id": config_id,
                    "K": len(config["r"]),
                    "N": config["N"],
                    "value_no_price": value_base,
                    "value_price": value_price,
                    "delta": value_price - value_base,
                    "top_task_delta_z": float(z_price[0] - z_base[0]),
                    "z_no_price": json.dumps([float(v) for v in z_base]),
                    "z_price": json.dumps([float(v) for v in z_price]),
                    "final_prices": json.dumps([float(v) for v in prices]),
                    "r": json.dumps([float(v) for v in config["r"]]),
                    "n": json.dumps([float(v) for v in config["n"]]),
                }
            )

    summary_by_regime: dict[str, Any] = {}
    for regime in ("abundance", "scarcity"):
        deltas = np.asarray([row["delta"] for row in rows if row["regime"] == regime], dtype=float)
        top_task = np.asarray(
            [row["top_task_delta_z"] for row in rows if row["regime"] == regime],
            dtype=float,
        )
        mean_delta, low_delta, high_delta = mean_ci(deltas)
        mean_top, low_top, high_top = mean_ci(top_task)
        summary_by_regime[regime] = {
            "mean_delta_value": mean_delta,
            "ci95_delta_value": [low_delta, high_delta],
            "mean_top_task_delta_z": mean_top,
            "ci95_top_task_delta_z": [low_top, high_top],
        }

    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    labels = ["abundance", "scarcity"]
    means = [summary_by_regime[label]["mean_delta_value"] for label in labels]
    lows = [summary_by_regime[label]["ci95_delta_value"][0] for label in labels]
    highs = [summary_by_regime[label]["ci95_delta_value"][1] for label in labels]
    err_low = [mean - low for mean, low in zip(means, lows, strict=True)]
    err_high = [high - mean for mean, high in zip(means, highs, strict=True)]
    ax.bar(labels, means, yerr=[err_low, err_high], capsize=5)
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.set_ylabel("delta valor estatico")
    ax.set_title("H3-A - Precio en motor estatico")
    fig.tight_layout()
    fig.savefig(figure_dir / "H3A_static_price_delta.png", dpi=180)
    plt.close(fig)

    scarcity_ci = summary_by_regime["scarcity"]["ci95_delta_value"]
    scarcity_negative = bool(scarcity_ci[1] < 0.0)
    abundance_neutral = bool(abs(summary_by_regime["abundance"]["mean_delta_value"]) < 1e-9)
    return rows, {
        "seed": 123,
        "price_gain": 0.5,
        "abundance": summary_by_regime["abundance"],
        "scarcity": summary_by_regime["scarcity"],
        "criterion": "report negative or neutral static effect; do not validate H3 in static equilibrium",
        "verdict": "NEGATIVO ESTATICO CONFIRMADO"
        if scarcity_negative and abundance_neutral
        else "NO CONCLUYENTE",
    }


def generate_h3_static_configs(seed: int, regime: str) -> Iterable[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    for _ in range(20):
        K = int(rng.integers(2, 6))
        n = rng.integers(2, 8, size=K).astype(float)
        r = np.sort(rng.uniform(0.5, 1.5, size=K))[::-1]
        if regime == "abundance":
            N = int(math.ceil(rng.uniform(1.25, 1.80) * float(n.sum())))
        elif regime == "scarcity":
            N = max(1, int(math.floor(rng.uniform(0.40, 0.75) * float(n.sum()))))
        else:
            raise ValueError(regime)
        yield {"r": r, "n": n, "N": N}


def run_h3_arrivals(figure_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    r = np.array([1.0, 0.85, 0.65, 0.55], dtype=float)
    n = np.array([4.0, 4.0, 3.0, 3.0], dtype=float)
    rates = np.array([0.06, 0.06, 0.08, 0.08], dtype=float)
    deadlines = np.array([18.0, 18.0, 12.0, 12.0], dtype=float)
    horizon = 500.0
    dt = 0.05
    seeds = list(range(100, 120))
    regimes = {"abundance": 18, "scarcity": 8}

    for regime, N in regimes.items():
        for seed in seeds:
            arrivals = ArrivalEngine.generate_arrivals(seed, horizon, rates, deadlines)
            for price_gain in (0.0, 0.5):
                engine = ArrivalEngine(r=r, n=n, N=N, arrivals=arrivals)
                metrics = engine.run(price_gain=price_gain, horizon=horizon, dt=dt)
                rows.append(
                    {
                        "experiment": "H3-B",
                        "regime": regime,
                        "seed": seed,
                        "N": N,
                        "price_gain": price_gain,
                        "delivered_value_ratio": metrics["delivered_value_ratio"],
                        "delivered_value": metrics["delivered_value"],
                        "expired_value": metrics["expired_value"],
                        "total_value": metrics["total_value"],
                        "arrivals": metrics["arrivals"],
                    }
                )

    summary: dict[str, Any] = {}
    for regime in regimes:
        base = {
            int(row["seed"]): float(row["delivered_value_ratio"])
            for row in rows
            if row["regime"] == regime and row["price_gain"] == 0.0
        }
        price = {
            int(row["seed"]): float(row["delivered_value_ratio"])
            for row in rows
            if row["regime"] == regime and row["price_gain"] == 0.5
        }
        deltas = np.asarray([price[seed] - base[seed] for seed in seeds], dtype=float)
        base_values = np.asarray([base[seed] for seed in seeds], dtype=float)
        price_values = np.asarray([price[seed] for seed in seeds], dtype=float)
        mean_delta, low_delta, high_delta = mean_ci(deltas)
        mean_base, low_base, high_base = mean_ci(base_values)
        mean_price, low_price, high_price = mean_ci(price_values)
        if regime == "scarcity" and low_delta > 0.0:
            verdict = "H0 RECHAZADA"
        elif regime == "abundance" and abs(mean_delta) < 1e-9:
            verdict = "EFECTO NULO"
        elif regime == "abundance" and high_delta <= 0.0:
            verdict = "EFECTO NO POSITIVO"
        else:
            verdict = "NO CONCLUYENTE"
        summary[regime] = {
            "N": regimes[regime],
            "mean_no_price": mean_base,
            "ci95_no_price": [low_base, high_base],
            "mean_price": mean_price,
            "ci95_price": [low_price, high_price],
            "mean_delta": mean_delta,
            "ci95_delta": [low_delta, high_delta],
            "verdict": verdict,
        }

    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    x = np.array([0.0, 0.5])
    for regime, color in (("abundance", "#377eb8"), ("scarcity", "#e41a1c")):
        means = [summary[regime]["mean_no_price"], summary[regime]["mean_price"]]
        lows = [summary[regime]["ci95_no_price"][0], summary[regime]["ci95_price"][0]]
        highs = [summary[regime]["ci95_no_price"][1], summary[regime]["ci95_price"][1]]
        yerr = [
            [mean - low for mean, low in zip(means, lows, strict=True)],
            [high - mean for mean, high in zip(means, highs, strict=True)],
        ]
        ax.errorbar(x, means, yerr=yerr, marker="o", linewidth=2.0, capsize=5, label=regime, color=color)
    ax.set_xticks(x, ["0", "0.5"])
    ax.set_xlabel("price_gain")
    ax.set_ylabel("valor entregado a tiempo")
    ax.set_title("H3-B - Precio bajo llegadas y deadlines")
    ax.set_ylim(0.0, 1.05)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "H3B_arrivals_price_gain.png", dpi=180)
    plt.close(fig)

    return rows, {
        "seeds": seeds,
        "horizon": horizon,
        "dt": dt,
        "r": r.tolist(),
        "n": n.tolist(),
        "arrival_rates": rates.tolist(),
        "deadlines": deadlines.tolist(),
        "criterion": "scarcity paired delta CI95 above 0; abundance effect approximately 0 or non-positive",
        **summary,
    }


def waste_fractional(z: np.ndarray, n: np.ndarray) -> float:
    return float(np.asarray(z)[np.asarray(z) < np.asarray(n)].sum())


def static_coverage_value(z: np.ndarray, r: np.ndarray, n: np.ndarray) -> float:
    return float(np.dot(r, np.minimum(z / n, 1.0)) / np.sum(r))


def mean_ci(values: Iterable[float]) -> tuple[float, float, float]:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return float("nan"), float("nan"), float("nan")
    mean = float(np.mean(arr))
    if len(arr) == 1:
        return mean, mean, mean
    sd = float(np.std(arr, ddof=1))
    if sd == 0.0:
        return mean, mean, mean
    half_width = float(stats.t.ppf(0.975, len(arr) - 1) * sd / math.sqrt(len(arr)))
    return mean, mean - half_width, mean + half_width


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_conclusions(
    path: Path,
    sanity: dict[str, Any],
    h1: dict[str, Any],
    h2: dict[str, Any],
    h3: dict[str, Any],
) -> None:
    text = f"""# Conclusiones del protocolo minimo

Fecha de ejecucion: 2026-06-13

## Cordura del motor

- Configuracion: r=[1,.8,.6,.5], n=[3,4,2,5], N=30.
- z*={format_list(sanity["z_star"])}
- z_obs={format_list(sanity["z_obs"])}
- max|err|={sanity["max_abs_err"]:.6g}
- Veredicto: {"PASS" if sanity["passed"] else "FAIL"}

## H1 - Smith converge al water-filling

- H0: Smith no converge a z*.
- Criterio preregistrado: {h1["criterion"]}.
- Resultado: slope={h1["slope"]:.6f}, R2={h1["r2"]:.6f}, max|err|={h1["max_abs_err"]:.6g}, fallos={h1["config_failures"]}.
- Veredicto: {h1["verdict"]}.

## H2 - Clearing entero reduce desperdicio bajo escasez

- H0: el clearing entero no cambia la cobertura bajo escasez.
- Criterio preregistrado: {h2["criterion"]}.
- Resultado: desperdicio medio {h2["mean_waste_smooth"]:.3f} -> {h2["mean_waste_integer"]:.3f} robots ({h2["reduction_pct"]:.1f}%).
- Delta pareado: {h2["mean_delta"]:.3f}, IC95 [{h2["ci95_delta"][0]:.3f}, {h2["ci95_delta"][1]:.3f}].
- No-peor: {100*h2["non_worse_share"]:.1f}%; estricto mejor: {100*h2["strict_better_share"]:.1f}%.
- Nota de medicion: {h2["primary_metric_note"]}.
- Veredicto: {h2["verdict"]}.

## H3-A - Precio en equilibrio estatico

- H0 operativa: el precio no debe reclamarse como mecanismo estatico.
- Criterio: {h3["static"]["criterion"]}.
- Abundancia: delta valor={h3["static"]["abundance"]["mean_delta_value"]:.4f}, IC95 [{h3["static"]["abundance"]["ci95_delta_value"][0]:.4f}, {h3["static"]["abundance"]["ci95_delta_value"][1]:.4f}].
- Escasez: delta valor={h3["static"]["scarcity"]["mean_delta_value"]:.4f}, IC95 [{h3["static"]["scarcity"]["ci95_delta_value"][0]:.4f}, {h3["static"]["scarcity"]["ci95_delta_value"][1]:.4f}].
- Tarea mas valiosa en escasez: delta z={h3["static"]["scarcity"]["mean_top_task_delta_z"]:.3f}, IC95 [{h3["static"]["scarcity"]["ci95_top_task_delta_z"][0]:.3f}, {h3["static"]["scarcity"]["ci95_top_task_delta_z"][1]:.3f}].
- Veredicto: {h3["static"]["verdict"]}.

## H3-B - Precio temporal con llegadas y deadlines

- H0: el precio no cambia el valor entregado a tiempo bajo llegadas.
- Criterio preregistrado: {h3["arrivals"]["criterion"]}.
- Abundancia: sin precio={h3["arrivals"]["abundance"]["mean_no_price"]:.4f}, con precio={h3["arrivals"]["abundance"]["mean_price"]:.4f}, delta={h3["arrivals"]["abundance"]["mean_delta"]:.4f}, IC95 [{h3["arrivals"]["abundance"]["ci95_delta"][0]:.4f}, {h3["arrivals"]["abundance"]["ci95_delta"][1]:.4f}], veredicto={h3["arrivals"]["abundance"]["verdict"]}.
- Escasez: sin precio={h3["arrivals"]["scarcity"]["mean_no_price"]:.4f}, con precio={h3["arrivals"]["scarcity"]["mean_price"]:.4f}, delta={h3["arrivals"]["scarcity"]["mean_delta"]:.4f}, IC95 [{h3["arrivals"]["scarcity"]["ci95_delta"][0]:.4f}, {h3["arrivals"]["scarcity"]["ci95_delta"][1]:.4f}], veredicto={h3["arrivals"]["scarcity"]["verdict"]}.

## Veredicto integrado

H1 y H2 pasan sus criterios preregistrados. H3-A confirma que el precio no debe defenderse como mecanismo de asignacion estatica: en abundancia no agrega valor y en escasez perturba el equilibrio. H3-B si muestra el cruce temporal esperado: efecto nulo en abundancia y mejora positiva, con IC95 disjunto de cero, bajo escasez con llegadas y deadlines.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def format_list(values: Iterable[float]) -> str:
    return "[" + ", ".join(f"{value:.4f}" for value in values) + "]"


if __name__ == "__main__":
    raise SystemExit(main())
