"""Consolidate existing validated results into PDF-ready figures and text.

This script does not rerun experiments. It reads the v2.7 benchmark outputs,
the v2.7 postprocess tables, and the minimal H1-H3 protocol artifacts.
"""

from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.animation as animation  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results" / "benchmark-v27-full"
OUT_DIR = ROOT / "results" / "figures_pdf"
SCRIPT_ID = "scripts/consolidate_pdf_figures.py"

METHOD_ORDER = [
    "smith",
    "classic_centralized_mincost",
    "classic_greedy_nearest",
    "classic_auction_cbba",
    "oracle_clairvoyant",
]

METHOD_LABELS = {
    "smith": "Smith",
    "classic_centralized_mincost": "Centralized",
    "classic_greedy_nearest": "Greedy",
    "classic_auction_cbba": "Auction",
    "oracle_clairvoyant": "Oracle",
    "smith_no_prices": "Smith no prices",
    "smith_no_integer": "Smith no integer",
    "response_threshold": "Threshold",
}

METHOD_COLORS = {
    "smith": "#1b9e77",
    "classic_centralized_mincost": "#377eb8",
    "classic_greedy_nearest": "#ff7f00",
    "classic_auction_cbba": "#984ea3",
    "oracle_clairvoyant": "#4daf4a",
    "smith_no_prices": "#a65628",
    "smith_no_integer": "#f781bf",
    "response_threshold": "#999999",
}

SCENARIOS = [
    {
        "key": "abundance",
        "title": "Abundancia",
        "scenario": "nominal_flow",
        "case": "rho0.7",
        "seed": 2026,
        "caption": "Regimen base con carga ofrecida baja: Smith conserva entregas altas y la teoria sirve como control de sanidad.",
    },
    {
        "key": "scarcity_priority",
        "title": "Escasez con prioridad",
        "scenario": "scarcity_priority",
        "case": "triage_forced",
        "seed": 2026,
        "caption": "Escenario estrella de triage: bajo escasez, la comparacion debe leerse con IC95 y no solo con medias.",
    },
    {
        "key": "robot_failure",
        "title": "Fallo de robot",
        "scenario": "robot_failures",
        "case": "fail4",
        "seed": 2026,
        "caption": "Robustez ante perdida de robots: la metrica clave es recuperacion sin coordinador central.",
    },
    {
        "key": "comm_degradation",
        "title": "Degradacion de comunicacion",
        "scenario": "comm_degradation",
        "case": "R3_p0",
        "seed": 2026,
        "caption": "Frontera de comunicacion reducida: muestra donde el mecanismo distribuido deja de dominar y pasa a paridad o perdida.",
    },
]


def main() -> int:
    if not RUN_DIR.exists():
        raise FileNotFoundError(RUN_DIR)

    for subdir in [
        OUT_DIR / "scenarios",
        OUT_DIR / "sweeps",
        OUT_DIR / "animations",
        OUT_DIR / "animations" / "frames",
        OUT_DIR / "diagrams",
    ]:
        subdir.mkdir(parents=True, exist_ok=True)

    summary_rows = read_csv(RUN_DIR / "summary.csv")
    significance_rows = read_csv(ROOT / "results" / "v2_7_significance.csv")
    manifest: list[dict[str, Any]] = []

    for spec in SCENARIOS:
        plot_final_state(spec, manifest)
        plot_temporal_metrics(spec, summary_rows, manifest)
        plot_method_comparison(spec, significance_rows, manifest)
        make_scenario_animation(spec, manifest)

    plot_load_sweep(significance_rows, manifest)
    plot_comm_sweep(significance_rows, manifest)
    plot_price_regime(manifest)
    plot_h3b_existing(manifest)
    plot_theory_closure(manifest)

    plot_stack_diagram(manifest)
    plot_single_clock_diagram(manifest)
    plot_market_diagram(manifest)

    write_manifest(OUT_DIR / "manifest.csv", manifest)
    write_results_draft(ROOT / "docs" / "resultados_tfm.md", manifest, significance_rows)

    print(f"PDF-ready consolidation complete: {OUT_DIR}")
    print(f"Manifest rows: {len(manifest)}")
    print("Draft: docs/resultados_tfm.md")
    return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def scenario_file(spec: dict[str, Any], suffix: str = "", method: str = "smith") -> Path:
    return RUN_DIR / spec["scenario"] / f"{spec['case']}_{method}_{spec['seed']}{suffix}.csv"


def add_manifest(
    manifest: list[dict[str, Any]],
    figure: Path,
    source_data: str,
    caption: str,
    seed: int | str = "",
    notes: str = "",
) -> None:
    manifest.append(
        {
            "figure": rel(figure),
            "source_data": source_data,
            "script": SCRIPT_ID,
            "seed": seed,
            "caption": caption,
            "notes": notes,
        }
    )


def save_figure(
    fig: plt.Figure,
    base_path: Path,
    manifest: list[dict[str, Any]],
    source_data: str,
    caption: str,
    seed: int | str = "",
    notes: str = "",
    svg: bool = False,
) -> None:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = base_path.with_suffix(".pdf")
    png_path = base_path.with_suffix(".png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    add_manifest(manifest, pdf_path, source_data, caption, seed, notes)
    add_manifest(manifest, png_path, source_data, caption, seed, notes)
    if svg:
        svg_path = base_path.with_suffix(".svg")
        fig.savefig(svg_path, bbox_inches="tight")
        add_manifest(manifest, svg_path, source_data, caption, seed, notes)
    plt.close(fig)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def plot_final_state(spec: dict[str, Any], manifest: list[dict[str, Any]]) -> None:
    theory_path = scenario_file(spec, suffix="_theory")
    rows = read_csv(theory_path)
    by_load: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_load[row["load"]].append(row)

    latest = []
    for load_id, series in by_load.items():
        row = max(series, key=lambda item: f(item["time"], -1.0))
        latest.append(
            {
                "load": load_id,
                "z_observed": f(row["z_observed"]),
                "z_theory": f(row["z_theory"]),
                "price": f(row.get("price")),
            }
        )
    latest = sorted(latest, key=lambda item: max(item["z_observed"], item["z_theory"]), reverse=True)[:14]
    latest = list(reversed(latest))

    labels = [item["load"].replace("load-", "L") for item in latest]
    observed = np.array([item["z_observed"] for item in latest], dtype=float)
    theory = np.array([item["z_theory"] for item in latest], dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    y = np.arange(len(labels))
    ax.barh(y - 0.18, theory, height=0.34, color="#d9d9d9", label="z* teoria")
    ax.barh(y + 0.18, observed, height=0.34, color=METHOD_COLORS["smith"], label="z observado")
    ax.set_yticks(y, labels)
    ax.set_xlabel("robots asignados / ocupacion")
    ax.set_title(f"{spec['title']} - estado final registrado")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.25)
    caption = (
        f"Estado final de ocupacion para {spec['title']} con Smith, semilla {spec['seed']}. "
        "La figura usa ocupaciones registradas; las coordenadas geometricas no estan en los logs v2.7."
    )
    save_figure(
        fig,
        OUT_DIR / "scenarios" / spec["key"] / "final_state",
        manifest,
        rel(theory_path),
        caption,
        seed=spec["seed"],
        notes="No geometric robot coordinates are stored in v2.7 logs.",
    )


def plot_temporal_metrics(
    spec: dict[str, Any],
    summary_rows: list[dict[str, str]],
    manifest: list[dict[str, Any]],
) -> None:
    main_path = scenario_file(spec)
    theory_path = scenario_file(spec, suffix="_theory")
    main_rows = read_csv(main_path)
    theory_rows = read_csv(theory_path)
    summary = find_summary(summary_rows, spec, "smith", spec["seed"])
    loads_offered = max(1.0, f(summary.get("loads_offered"), default=f(summary.get("loads_spawned"), 1.0)))

    time = np.array([f(row["time"]) for row in main_rows], dtype=float)
    delivered = np.array([f(row["delivered_count"]) for row in main_rows], dtype=float)
    active = np.array([f(row["active_count"]) for row in main_rows], dtype=float)
    deficit = np.array([f(row["mean_contact_deficit"]) for row in main_rows], dtype=float)
    delivery_fraction = delivered / loads_offered
    throughput = delivered / np.maximum(time, 1.0)

    by_load: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in theory_rows:
        by_load[row["load"]].append(row)
    ranked = sorted(
        by_load,
        key=lambda load: max(f(row["z_observed"], 0.0) for row in by_load[load]),
        reverse=True,
    )[:5]

    fig, axes = plt.subplots(3, 1, figsize=(8.0, 7.8), sharex=True)
    axes[0].plot(time, delivery_fraction, color=METHOD_COLORS["smith"], label="entregas/ofrecidas")
    axes[0].plot(time, active / max(float(np.nanmax(active)), 1.0), color="#666666", label="activos normalizados")
    axes[0].set_ylabel("fraccion")
    axes[0].legend(loc="lower right")
    axes[0].grid(alpha=0.25)

    axes[1].plot(time, throughput, color="#377eb8", label="throughput acumulado")
    axes[1].plot(time, deficit, color="#e41a1c", alpha=0.8, label="deficit contacto medio")
    axes[1].set_ylabel("valor")
    axes[1].legend(loc="upper right")
    axes[1].grid(alpha=0.25)

    colors = plt.cm.tab10(np.linspace(0, 1, len(ranked)))
    for color, load in zip(colors, ranked, strict=True):
        series = sorted(by_load[load], key=lambda row: f(row["time"]))
        t_load = np.array([f(row["time"]) for row in series], dtype=float)
        z_obs = np.array([f(row["z_observed"]) for row in series], dtype=float)
        z_star = np.array([f(row["z_theory"]) for row in series], dtype=float)
        label = load.replace("load-", "L")
        axes[2].plot(t_load, z_obs, color=color, linewidth=1.4, label=f"{label} obs")
        axes[2].plot(t_load, z_star, color=color, linewidth=1.1, linestyle="--", alpha=0.75)
    axes[2].set_xlabel("tiempo simulado (s)")
    axes[2].set_ylabel("z_k(t)")
    axes[2].grid(alpha=0.25)
    axes[2].legend(ncol=2, fontsize=8)
    fig.suptitle(f"{spec['title']} - evolucion temporal", y=0.995)
    caption = (
        f"Evolucion temporal en {spec['title']} para Smith, semilla {spec['seed']}: "
        "entregas acumuladas, throughput, deficit medio y ocupacion observada frente a z*."
    )
    save_figure(
        fig,
        OUT_DIR / "scenarios" / spec["key"] / "temporal_metrics",
        manifest,
        f"{rel(main_path)}; {rel(theory_path)}",
        caption,
        seed=spec["seed"],
    )


def find_summary(
    rows: list[dict[str, str]],
    spec: dict[str, Any],
    method: str,
    seed: int,
) -> dict[str, str]:
    for row in rows:
        if (
            row.get("scenario") == spec["scenario"]
            and row.get("scenario_case") == spec["case"]
            and row.get("method") == method
            and int(float(row.get("seed", -1))) == seed
        ):
            return row
    return {}


def plot_method_comparison(
    spec: dict[str, Any],
    significance_rows: list[dict[str, str]],
    manifest: list[dict[str, Any]],
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    for ax, metric, ylabel in zip(
        axes,
        ["capture", "throughput"],
        ["reward capture ratio", "throughput steady"],
        strict=True,
    ):
        rows = [
            row
            for row in significance_rows
            if row["scenario"] == spec["scenario"]
            and row["scenario_case"] == spec["case"]
            and row["metric"] == metric
            and row["method"] in METHOD_ORDER
            and math.isfinite(f(row["mean"]))
        ]
        rows = sorted(rows, key=lambda row: METHOD_ORDER.index(row["method"]))
        x = np.arange(len(rows))
        means = np.array([f(row["mean"]) for row in rows], dtype=float)
        lows = np.array([f(row["ci95_low"]) for row in rows], dtype=float)
        highs = np.array([f(row["ci95_high"]) for row in rows], dtype=float)
        colors = [METHOD_COLORS[row["method"]] for row in rows]
        labels = [METHOD_LABELS[row["method"]] for row in rows]
        ax.bar(x, means, color=colors)
        ax.errorbar(x, means, yerr=[means - lows, highs - means], fmt="none", ecolor="black", capsize=3)
        ax.set_xticks(x, labels, rotation=35, ha="right")
        ax.set_ylabel(ylabel)
        ax.set_title(metric)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(f"{spec['title']} - comparacion de metodos", y=1.03)
    caption = (
        f"Comparacion de metodos para {spec['title']} con medias e IC95 del benchmark v2.7. "
        "Intervalos solapados se interpretan como paridad, no como victoria."
    )
    save_figure(
        fig,
        OUT_DIR / "scenarios" / spec["key"] / "method_comparison",
        manifest,
        "results/v2_7_significance.csv",
        caption,
    )


def make_scenario_animation(spec: dict[str, Any], manifest: list[dict[str, Any]]) -> None:
    theory_path = scenario_file(spec, suffix="_theory")
    rows = read_csv(theory_path)
    by_load: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_load[row["load"]].append(row)
    ranked = sorted(
        by_load,
        key=lambda load: max(f(row["z_observed"], 0.0) for row in by_load[load]),
        reverse=True,
    )[:8]
    if not ranked:
        return

    series_by_load = {}
    max_time = 0.0
    for load in ranked:
        series = sorted(by_load[load], key=lambda row: f(row["time"]))
        times = np.array([f(row["time"]) for row in series], dtype=float)
        observed = np.array([f(row["z_observed"]) for row in series], dtype=float)
        theory = np.array([f(row["z_theory"]) for row in series], dtype=float)
        series_by_load[load] = (times, observed, theory)
        max_time = max(max_time, float(np.nanmax(times)))

    frame_times = np.linspace(0.0, max_time, min(220, max(30, int(max_time / 0.5))))
    labels = [load.replace("load-", "L") for load in ranked]
    y = np.arange(len(ranked))
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    obs_bars = ax.barh(y + 0.18, np.zeros(len(ranked)), height=0.34, color=METHOD_COLORS["smith"], label="z observado")
    theory_bars = ax.barh(y - 0.18, np.zeros(len(ranked)), height=0.34, color="#d9d9d9", label="z* teoria")
    ax.set_yticks(y, labels)
    ax.set_xlim(0.0, max(1.0, max(np.nanmax(series_by_load[load][2]) for load in ranked) * 1.1))
    ax.set_xlabel("ocupacion")
    ax.set_title(f"{spec['title']} - coaliciones en el tiempo")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.25)
    time_text = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top")

    def values_at(load: str, t: float) -> tuple[float, float]:
        times, observed, theory = series_by_load[load]
        idx = int(np.searchsorted(times, t, side="right") - 1)
        if idx < 0:
            return 0.0, 0.0
        return float(observed[idx]), float(theory[idx])

    def update(frame_idx: int) -> list[Any]:
        t = float(frame_times[frame_idx])
        for idx, load in enumerate(ranked):
            obs, th = values_at(load, t)
            obs_bars[idx].set_width(obs)
            theory_bars[idx].set_width(th)
        time_text.set_text(f"t={t:.1f}s")
        return [*obs_bars, *theory_bars, time_text]

    anim = animation.FuncAnimation(fig, update, frames=len(frame_times), interval=100, blit=False)
    out_base = OUT_DIR / "animations" / spec["key"] / "occupancy_animation"
    out_base.parent.mkdir(parents=True, exist_ok=True)
    gif_path = out_base.with_suffix(".gif")
    mp4_path = out_base.with_suffix(".mp4")
    anim.save(gif_path, writer=animation.PillowWriter(fps=8))
    anim.save(mp4_path, writer=animation.FFMpegWriter(fps=8, bitrate=1800))

    frame_dir = OUT_DIR / "animations" / "frames" / spec["key"]
    frame_dir.mkdir(parents=True, exist_ok=True)
    for frame_idx in sorted({0, len(frame_times) // 4, len(frame_times) // 2, 3 * len(frame_times) // 4, len(frame_times) - 1}):
        update(frame_idx)
        fig.savefig(frame_dir / f"frame_{frame_idx:03d}.png", dpi=180, bbox_inches="tight")

    plt.close(fig)
    caption = (
        f"Animacion diagnostica de ocupaciones para {spec['title']} con Smith, semilla {spec['seed']}. "
        "Representa coaliciones y prediccion teorica; no reconstruye posiciones fisicas."
    )
    add_manifest(manifest, gif_path, rel(theory_path), caption, seed=spec["seed"], notes="Downsampled to <=220 frames.")
    add_manifest(manifest, mp4_path, rel(theory_path), caption, seed=spec["seed"], notes="Downsampled to <=220 frames.")


def plot_load_sweep(significance_rows: list[dict[str, str]], manifest: list[dict[str, Any]]) -> None:
    cases = {"rho0.5": 0.5, "rho1.0": 1.0, "rho1.7": 1.7}
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for method in METHOD_ORDER:
        xs: list[float] = []
        means: list[float] = []
        lows: list[float] = []
        highs: list[float] = []
        for case, rho in cases.items():
            row = find_sig(significance_rows, "load_sweep", case, method, "capture")
            if row:
                xs.append(rho)
                means.append(f(row["mean"]))
                lows.append(f(row["ci95_low"]))
                highs.append(f(row["ci95_high"]))
        if xs:
            ax.plot(xs, means, marker="o", label=METHOD_LABELS[method], color=METHOD_COLORS[method])
            ax.fill_between(xs, lows, highs, color=METHOD_COLORS[method], alpha=0.14)
    ax.set_xlabel("rho ofrecido")
    ax.set_ylabel("reward capture ratio")
    ax.set_title("Load sweep - captura vs carga")
    ax.set_ylim(0.0, 1.05)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    save_figure(
        fig,
        OUT_DIR / "sweeps" / "load_sweep_capture",
        manifest,
        "results/v2_7_significance.csv",
        "Captura media e IC95 frente a carga ofrecida rho para los metodos principales.",
    )


def plot_comm_sweep(significance_rows: list[dict[str, str]], manifest: list[dict[str, Any]]) -> None:
    cases = {"R1.5_p0": 1.5, "R3_p0": 3.0, "R4_p0": 4.0, "R6_p0": 6.0, "R12_p0": 12.0}
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for method in METHOD_ORDER:
        xs: list[float] = []
        means: list[float] = []
        lows: list[float] = []
        highs: list[float] = []
        for case, radius in cases.items():
            row = find_sig(significance_rows, "comm_degradation", case, method, "capture")
            if row:
                xs.append(radius)
                means.append(f(row["mean"]))
                lows.append(f(row["ci95_low"]))
                highs.append(f(row["ci95_high"]))
        if xs:
            ax.plot(xs, means, marker="o", label=METHOD_LABELS[method], color=METHOD_COLORS[method])
            ax.fill_between(xs, lows, highs, color=METHOD_COLORS[method], alpha=0.14)
    ax.set_xlabel("radio de comunicacion R")
    ax.set_ylabel("reward capture ratio")
    ax.set_title("Communication sweep - frontera de conectividad")
    ax.set_ylim(0.0, 1.05)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    save_figure(
        fig,
        OUT_DIR / "sweeps" / "comm_sweep_capture",
        manifest,
        "results/v2_7_significance.csv",
        "Captura media e IC95 frente al radio de comunicacion; la caida en R bajo delimita la frontera operacional.",
    )


def find_sig(
    rows: list[dict[str, str]],
    scenario: str,
    case: str,
    method: str,
    metric: str,
) -> dict[str, str] | None:
    for row in rows:
        if (
            row["scenario"] == scenario
            and row["scenario_case"] == case
            and row["method"] == method
            and row["metric"] == metric
        ):
            return row
    return None


def plot_price_regime(manifest: list[dict[str, Any]]) -> None:
    path = ROOT / "results" / "v2_7_price_regime.csv"
    rows = sorted(read_csv(path), key=lambda row: (f(row["rho"]), row["scenario_case"]))
    x = np.arange(len(rows))
    means = np.array([f(row["delta_raw_minus_no_prices"]) for row in rows], dtype=float)
    lows = np.array([f(row["delta_ci95_low"]) for row in rows], dtype=float)
    highs = np.array([f(row["delta_ci95_high"]) for row in rows], dtype=float)
    labels = [row["scenario_case"] for row in rows]
    colors = ["#1b9e77" if mean >= 0 else "#d95f02" for mean in means]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.bar(x, means, color=colors)
    ax.errorbar(x, means, yerr=[means - lows, highs - means], fmt="none", ecolor="black", capsize=4)
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.set_xticks(x, labels, rotation=35, ha="right")
    ax.set_ylabel("delta capture: raw - no_prices")
    ax.set_title("Regimen de precios - cruce de signo")
    ax.grid(axis="y", alpha=0.25)
    save_figure(
        fig,
        OUT_DIR / "sweeps" / "price_regime_delta",
        manifest,
        rel(path),
        "Delta pareado de captura al activar precios; el signo cambia entre flujo nominal y escasez priorizada.",
    )


def plot_h3b_existing(manifest: list[dict[str, Any]]) -> None:
    path = ROOT / "exp_results" / "H3_metrics.csv"
    rows = [row for row in read_csv(path) if row.get("experiment") == "H3-B"]
    grouped: dict[str, dict[int, dict[float, float]]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        grouped[row["regime"]][int(float(row["seed"]))][f(row["price_gain"])] = f(row["delivered_value_ratio"])

    regimes = ["abundance", "scarcity"]
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    x = np.arange(len(regimes))
    means = []
    lows = []
    highs = []
    for regime in regimes:
        deltas = np.array(
            [
                vals.get(0.5, math.nan) - vals.get(0.0, math.nan)
                for vals in grouped[regime].values()
            ],
            dtype=float,
        )
        deltas = deltas[np.isfinite(deltas)]
        mean, low, high = mean_ci(deltas)
        means.append(mean)
        lows.append(low)
        highs.append(high)
        ax.scatter(np.full_like(deltas, x[len(means) - 1], dtype=float), deltas, color="#666666", s=18, alpha=0.45)
    means_arr = np.array(means)
    ax.bar(x, means, color=["#377eb8", "#e41a1c"], alpha=0.75)
    ax.errorbar(x, means, yerr=[means_arr - np.array(lows), np.array(highs) - means_arr], fmt="none", ecolor="black", capsize=5)
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.set_xticks(x, regimes)
    ax.set_ylabel("delta valor entregado")
    ax.set_title("H3-B existente - efecto temporal del precio")
    ax.grid(axis="y", alpha=0.25)
    save_figure(
        fig,
        OUT_DIR / "sweeps" / "h3b_existing_delta_by_regime",
        manifest,
        rel(path),
        "Resultado H3-B disponible: delta pareado de valor entregado con precio frente a sin precio por regimen.",
        notes="No deadline-sensitivity sweep exists in current artifacts; no new experiment was run.",
    )
    note = OUT_DIR / "sweeps" / "H3B_sensitivity_not_available.md"
    note.write_text(
        "# H3-B sensitivity not generated\n\n"
        "The requested deadline/rate sensitivity sweep is marked as Phase 2 in the protocol, "
        "but no pre-existing artifact contains deadline-sweep data. Because this consolidation "
        "pass must not run new experiments, the script emits the existing paired H3-B result instead.\n",
        encoding="utf-8",
    )
    add_manifest(
        manifest,
        note,
        rel(path),
        "Trazabilidad de la sensibilidad H3-B no generada por ausencia de datos existentes.",
        notes="No new experiments rule.",
    )


def mean_ci(values: Iterable[float]) -> tuple[float, float, float]:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return math.nan, math.nan, math.nan
    mean = float(np.mean(arr))
    if len(arr) < 2:
        return mean, mean, mean
    sd = float(np.std(arr, ddof=1))
    if sd == 0.0:
        return mean, mean, mean
    half = float(stats.t.ppf(0.975, len(arr) - 1) * sd / math.sqrt(len(arr)))
    return mean, mean - half, mean + half


def plot_theory_closure(manifest: list[dict[str, Any]]) -> None:
    path = ROOT / "results" / "v2_7_scatter_closure_metrics.csv"
    rows = sorted(read_csv(path), key=lambda row: f(row["r2"]), reverse=True)
    labels = [row["regime"] for row in rows]
    r2 = np.array([f(row["r2"]) for row in rows], dtype=float)
    colors = ["#1b9e77" if row.get("sample_ok") == "True" else "#d95f02" for row in rows]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.bar(np.arange(len(rows)), r2, color=colors)
    ax.set_xticks(np.arange(len(rows)), labels, rotation=35, ha="right")
    ax.set_ylabel("R2 teoria-realidad")
    ax.set_ylim(0.0, 1.0)
    ax.set_title("Cierre teoria-realidad por regimen")
    ax.grid(axis="y", alpha=0.25)
    save_figure(
        fig,
        OUT_DIR / "sweeps" / "theory_reality_r2_by_regime",
        manifest,
        rel(path),
        "R2 consolidado por regimen usando ventana post-contacto y z* capado al peso de la carga.",
    )


def plot_stack_diagram(manifest: list[dict[str, Any]]) -> None:
    layers = ["percibir", "fusionar", "valorar", "revisar", "precio", "clearing", "campo", "ruedas"]
    fig, ax = plt.subplots(figsize=(5.8, 7.2))
    ax.axis("off")
    for idx, layer in enumerate(layers):
        y = len(layers) - idx - 1
        rect = plt.Rectangle((0.18, y), 0.64, 0.7, facecolor="#e8f4f0", edgecolor="#1b9e77", linewidth=1.4)
        ax.add_patch(rect)
        ax.text(0.5, y + 0.35, layer, ha="center", va="center", fontsize=11)
        if idx < len(layers) - 1:
            ax.annotate("", xy=(0.5, y - 0.03), xytext=(0.5, y - 0.28), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, len(layers))
    ax.set_title("Stack de control en 7 capas")
    save_figure(
        fig,
        OUT_DIR / "diagrams" / "stack_7_layers",
        manifest,
        "conceptual diagram",
        "Diagrama de bloques del bucle percibir-fusionar-valorar-revisar-precio-clearing-campo-ruedas.",
        svg=True,
    )


def plot_single_clock_diagram(manifest: list[dict[str, Any]]) -> None:
    stages = ["sensado", "payoff", "Smith", "precio", "clearing", "campo", "integracion"]
    angles = np.linspace(0, 2 * np.pi, len(stages), endpoint=False)
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    ax.axis("off")
    center = np.array([0.0, 0.0])
    radius = 1.0
    ax.add_patch(plt.Circle(center, radius, fill=False, edgecolor="#377eb8", linewidth=1.5))
    for angle, stage in zip(angles, stages, strict=True):
        pos = np.array([math.cos(angle), math.sin(angle)]) * radius
        ax.add_patch(plt.Circle(pos, 0.16, color="#e6f0fa", ec="#377eb8", lw=1.2))
        ax.text(pos[0], pos[1], stage, ha="center", va="center", fontsize=9)
    for a0, a1 in zip(angles, np.roll(angles, -1), strict=True):
        p0 = np.array([math.cos(a0), math.sin(a0)]) * radius
        p1 = np.array([math.cos(a1), math.sin(a1)]) * radius
        ax.annotate("", xy=p1 * 0.88, xytext=p0 * 0.88, arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#555555"})
    ax.text(0, 0, "un tick\ndt", ha="center", va="center", fontsize=14, weight="bold")
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.set_title("El reloj unico")
    save_figure(
        fig,
        OUT_DIR / "diagrams" / "single_clock",
        manifest,
        "conceptual diagram",
        "Todo el sistema se actualiza en el mismo tick: percepcion, valoracion, revision, clearing y dinamica fisica.",
        svg=True,
    )


def plot_market_diagram(manifest: list[dict[str, Any]]) -> None:
    lam = np.linspace(0.05, 1.6, 300)
    demand = 14 / (1 + np.exp(4 * (lam - 0.75))) + 1.5
    supply = np.piecewise(lam, [lam < 0.45, (lam >= 0.45) & (lam < 0.95), lam >= 0.95], [3.0, 8.0, 12.0])
    idx = int(np.argmin(np.abs(demand - supply)))
    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    ax.plot(lam, demand, color="#1b9e77", linewidth=2.0, label="D(lambda)")
    ax.step(lam, supply, where="post", color="#377eb8", linewidth=2.0, label="h(Q)")
    ax.scatter([lam[idx]], [supply[idx]], color="#d95f02", zorder=5, label="lambda*")
    ax.annotate("kink", xy=(0.95, 12), xytext=(1.08, 13.4), arrowprops={"arrowstyle": "->"})
    ax.set_xlabel("lambda")
    ax.set_ylabel("capacidad / demanda")
    ax.set_title("Mercado oferta-demanda heterogeneo")
    ax.legend()
    ax.grid(alpha=0.25)
    save_figure(
        fig,
        OUT_DIR / "diagrams" / "market_supply_demand",
        manifest,
        "conceptual diagram",
        "Curva de oferta por tramos y demanda decreciente con el cruce lambda* y un kink marcado.",
        svg=True,
    )


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["figure", "source_data", "script", "seed", "caption", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_results_draft(
    path: Path,
    manifest: list[dict[str, Any]],
    significance_rows: list[dict[str, str]],
) -> None:
    scarcity = find_sig(significance_rows, "scarcity_priority", "triage_forced", "smith", "capture")
    central = find_sig(significance_rows, "scarcity_priority", "triage_forced", "classic_centralized_mincost", "capture")
    comm_r3 = find_sig(significance_rows, "comm_degradation", "R3_p0", "smith", "capture")
    comm_r12 = find_sig(significance_rows, "comm_degradation", "R12_p0", "smith", "capture")
    h3_summary = read_csv(ROOT / "exp_results" / "H3_metrics.csv")
    h3_scarcity = summarize_h3_delta(h3_summary, "scarcity")
    h3_abundance = summarize_h3_delta(h3_summary, "abundance")

    def fig(path_fragment: str) -> str:
        for row in manifest:
            if path_fragment in row["figure"] and row["figure"].endswith(".pdf"):
                return "../" + row["figure"]
        return "../" + path_fragment

    text = f"""# Resultados TFM - borrador de seccion 5

## Mini-outline

- Validar primero los mecanismos aislados H1-H3 para separar teoria de interacciones del benchmark.
- Presentar cuatro escenarios canonicos del benchmark v2.7: abundancia, escasez con prioridad, fallo de robot y degradacion de comunicacion.
- Usar sweeps para delimitar regimenes: carga, radio de comunicacion, precio y cierre teoria-realidad.
- Cerrar con limitaciones: las figuras de estado usan ocupaciones registradas, no coordenadas roboticas completas.

## 5.1 Banco minimo de mecanismos

El banco minimo separa los tres mecanismos teoricos antes de interpretar el benchmark completo. H1 verifica que la dinamica de Smith reproduce el water-filling en equilibrio, H2 confirma que el clearing entero reduce desperdicio bajo escasez, y H3 corrige la interpretacion del precio: el precio no mejora el equilibrio estatico, pero si aporta valor cuando hay llegadas y deadlines.

![H3-B existing delta]({fig("h3b_existing_delta_by_regime.pdf")})

Figura: resultado H3-B disponible. En abundancia el delta medio es {h3_abundance[0]:.4f}; en escasez el delta medio es {h3_scarcity[0]:.4f}, con IC95 [{h3_scarcity[1]:.4f}, {h3_scarcity[2]:.4f}]. La afirmacion defendible es temporal: el precio rescata valor bajo escasez dinamica, no en equilibrio estatico.

## 5.2 Escenarios canonicos v2.7

El escenario de abundancia funciona como control de sanidad: las entregas son altas y las diferencias entre metodos no deben sobrerrelatarse cuando los intervalos se solapan.

![Abundance comparison]({fig("abundance/method_comparison.pdf")})

En escasez con prioridad aparece el caso central para la tesis. Smith alcanza captura media {f(scarcity.get("mean")):.3f}, mientras que el centralizado min-cost queda en {f(central.get("mean")):.3f}; la lectura correcta depende del IC95 y queda trazada en la figura, no solo en la media.

![Scarcity priority comparison]({fig("scarcity_priority/method_comparison.pdf")})

El fallo de robot mide robustez operacional. Aqui la pregunta no es solo cuanta recompensa se captura, sino si el sistema recupera asignaciones utiles sin introducir un coordinador central.

![Robot failure temporal]({fig("robot_failure/temporal_metrics.pdf")})

La degradacion de comunicacion delimita la frontera honesta del metodo. Smith conserva captura media {f(comm_r12.get("mean")):.3f} con R12, pero cae a {f(comm_r3.get("mean")):.3f} en R3; este resultado debe presentarse como limite de aplicabilidad, no como fallo oculto.

![Communication comparison]({fig("comm_degradation/method_comparison.pdf")})

## 5.3 Barridos consolidados

Los barridos convierten los escenarios puntuales en regimenes. El load sweep resume donde la carga empieza a degradar la captura; el comm sweep muestra la transicion por conectividad; el price-regime plot documenta que el precio puede restar en flujo nominal y cambiar de signo en escasez priorizada.

![Load sweep]({fig("load_sweep_capture.pdf")})

![Communication sweep]({fig("comm_sweep_capture.pdf")})

![Price regime]({fig("price_regime_delta.pdf")})

El cierre teoria-realidad debe leerse por regimen. La correlacion mejora en ventanas post-contacto con z* capado al peso de la carga, mientras que escenarios de baja comunicacion o escasez extrema quedan como casos limite.

![Theory reality]({fig("theory_reality_r2_by_regime.pdf")})

## 5.4 Diagramas de arquitectura

Los diagramas no anaden datos; ayudan a que el lector entienda la arquitectura que produce los resultados. Deben usarse antes de la discusion para conectar el mecanismo matematico con el pipeline implementado.

![Stack]({fig("stack_7_layers.pdf")})

![Single clock]({fig("single_clock.pdf")})

![Market]({fig("market_supply_demand.pdf")})

## Limitaciones de esta consolidacion

Los CSV v2.7 guardan ocupaciones, entregas, deficit y logs de cambio, pero no guardan coordenadas completas de robots y cargas. Por eso las figuras de estado final y las animaciones son diagnosticos de ocupacion/coalicion, no reconstrucciones geometricas del mundo. La sensibilidad H3-B frente a deadlines y tasas de llegada tampoco existe como artefacto previo; por la regla de no correr experimentos nuevos, queda registrada como pendiente de Fase 2.

## Claim-evidence map

- Claim: Smith reproduce la prediccion water-filling en el motor minimo. Evidence: `exp_results/conclusiones.md`, H1 slope 1.000000 y R2 1.000000. Status: supported.
- Claim: El clearing entero reduce desperdicio bajo escasez. Evidence: `exp_results/conclusiones.md`, H2 reduccion -32.0%. Status: supported.
- Claim: El precio es un mecanismo temporal, no estatico. Evidence: H3-A negativo estatico e H3-B delta positivo en escasez. Status: supported.
- Claim: La comunicacion limitada marca una frontera operacional. Evidence: comm sweep y comparacion R12/R3. Status: supported.
- Claim: Hay sensibilidad H3-B por deadline/tasa. Evidence: no artifact yet. Status: needs evidence.

## Self-review checklist

- Clarity: cada subseccion abre con una afirmacion unica.
- Flow: el texto avanza de mecanismos aislados a escenarios y luego a barridos.
- Terminologia: se usa Smith, clearing entero, precio temporal y teoria-realidad de forma estable.
- Unsupported claims: la sensibilidad H3-B queda explicitamente marcada como pendiente.
- Missing evidence: faltan coordenadas geometricas para animaciones espaciales reales y el sweep H3-B de Fase 2.
"""
    path.write_text(text, encoding="utf-8")


def summarize_h3_delta(rows: list[dict[str, str]], regime: str) -> tuple[float, float, float]:
    grouped: dict[int, dict[float, float]] = defaultdict(dict)
    for row in rows:
        if row.get("experiment") == "H3-B" and row.get("regime") == regime:
            grouped[int(float(row["seed"]))][f(row["price_gain"])] = f(row["delivered_value_ratio"])
    deltas = [vals[0.5] - vals[0.0] for vals in grouped.values() if 0.5 in vals and 0.0 in vals]
    return mean_ci(deltas)


if __name__ == "__main__":
    raise SystemExit(main())
