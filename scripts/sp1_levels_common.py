"""Shared publication utilities for the four SP1 experimental levels.

The module is intentionally limited to deterministic post-processing. Raw
campaigns remain in their canonical locations and every level manifest records
their SHA-256 hashes.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEVELS_OUTPUT_ROOT = REPOSITORY_ROOT / "scripts" / "results" / "sp1_levels"
GEO_SOURCE_ROOT = (
    REPOSITORY_ROOT
    / "results"
    / "sp1_geo"
    / "SP1_TFM_GEO_QPG_SIGNAL_ENGINE_CLOSURE_BENCHMARK_v1"
)

COLORS = {
    "blue": "#2369BD",
    "orange": "#E65113",
    "green": "#2D8A57",
    "red": "#C63C32",
    "purple": "#7A58A6",
    "gold": "#D89C19",
    "cyan": "#168AAD",
    "dark": "#1F1F24",
    "gray": "#6B7280",
    "light_gray": "#D7DEE8",
    "floor": "#F8FAFC",
}

METHOD_LABELS = {
    "milp_physical_oracle": "MILP físico",
    "hungarian_slots": "Húngaro por slots",
    "capacity_cbba_scalar": "Capacity-CBBA",
    "physical_cbba_marginal": "CBBA físico",
    "weighted_grape_scalar": "Weighted-GRAPE",
    "role_grape_s_physical": "Role-GRAPE-S",
    "pair_role_grape_s_physical": "Pair/Role-GRAPE-S",
    "qpg_logit_scalar": "QPG escalar",
    "geo_qpg_logit_physical": "Geo-QPG físico",
    "geo_qpg_smith_physical": "Geo-QPG Smith",
}

METHOD_COLORS = {
    "milp_physical_oracle": COLORS["dark"],
    "hungarian_slots": COLORS["gray"],
    "capacity_cbba_scalar": COLORS["blue"],
    "physical_cbba_marginal": COLORS["cyan"],
    "weighted_grape_scalar": COLORS["gold"],
    "role_grape_s_physical": COLORS["purple"],
    "pair_role_grape_s_physical": COLORS["green"],
    "qpg_logit_scalar": COLORS["orange"],
    "geo_qpg_logit_physical": COLORS["red"],
    "geo_qpg_smith_physical": COLORS["purple"],
}

FAMILY_LABELS = {
    "F0_easy_separable": "F0 · separable",
    "F1_heterogeneous_critical": "F1 · heterogéneo",
    "F2_scarce_priority": "F2 · escasez",
    "F3_torque_complementarity": "F3 · torque",
    "F4_mixed_geometry_route": "F4 · geometría",
    "F5_network_failure": "F5 · fallo de red",
}


@dataclass(frozen=True)
class PowerLawFit:
    """Log-log descriptive regression parameters."""

    exponent: float
    scale: float
    r_squared: float
    n_points: int


def configure_publication_style() -> None:
    """Apply a compact IEEE/Nature-inspired Matplotlib style."""

    mpl.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 360,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
            "font.size": 9.0,
            "axes.titlesize": 10.2,
            "axes.titleweight": "bold",
            "axes.labelsize": 9.2,
            "axes.labelcolor": COLORS["dark"],
            "axes.edgecolor": COLORS["dark"],
            "axes.linewidth": 0.75,
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": COLORS["light_gray"],
            "grid.alpha": 0.55,
            "grid.linewidth": 0.55,
            "xtick.color": COLORS["dark"],
            "ytick.color": COLORS["dark"],
            "xtick.labelsize": 8.2,
            "ytick.labelsize": 8.2,
            "legend.frameon": False,
            "legend.fontsize": 8.0,
            "legend.title_fontsize": 8.2,
            "lines.linewidth": 1.8,
            "lines.markersize": 5.2,
            "patch.linewidth": 0.75,
            "figure.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def label_panels(axes: Sequence[plt.Axes]) -> None:
    """Place robust panel labels outside the plotting region."""

    for index, axis in enumerate(axes):
        axis.text(
            -0.12,
            1.07,
            chr(ord("a") + index),
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=10.5,
            fontweight="bold",
            color=COLORS["dark"],
        )


def save_figure(
    figure: plt.Figure,
    output_stem: Path,
    *,
    tight: bool = True,
) -> list[Path]:
    """Save one figure as vector PDF and high-resolution PNG."""

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    if tight:
        figure.tight_layout()
    paths = [output_stem.with_suffix(".pdf"), output_stem.with_suffix(".png")]
    figure.savefig(paths[0], bbox_inches="tight", facecolor="white")
    figure.savefig(
        paths[1],
        bbox_inches="tight",
        facecolor="white",
        dpi=360,
    )
    plt.close(figure)
    return paths


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def source_record(path: Path) -> dict[str, object]:
    """Build a canonical source registry entry."""

    resolved = path.resolve()
    return {
        "path": resolved.relative_to(REPOSITORY_ROOT).as_posix(),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def artifact_records(
    output_dir: Path,
    *,
    exclude_names: Iterable[str] = ("manifest.json",),
) -> dict[str, dict[str, object]]:
    """Hash all generated files except the manifest itself."""

    excluded = set(exclude_names)
    records: dict[str, dict[str, object]] = {}
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name in excluded:
            continue
        records[path.relative_to(output_dir).as_posix()] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return records


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    """Write UTF-8 JSON with stable formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_level_manifest(
    *,
    output_dir: Path,
    level: str,
    description: str,
    sources: Sequence[Path],
    row_counts: Mapping[str, int],
    claims: Sequence[str],
    limitations: Sequence[str],
) -> Path:
    """Create the reproducibility manifest for one level."""

    manifest = {
        "schema_version": "sp1-level-package-v1",
        "level": level,
        "description": description,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "matplotlib": mpl.__version__,
        },
        "sources": [source_record(path) for path in sources],
        "row_counts": {key: int(value) for key, value in row_counts.items()},
        "claims": list(claims),
        "limitations": list(limitations),
        "artifacts": artifact_records(output_dir),
    }
    path = output_dir / "manifest.json"
    write_json(path, manifest)
    return path


def quantile_summary(
    frame: pd.DataFrame,
    *,
    groups: Sequence[str],
    metrics: Sequence[str],
) -> pd.DataFrame:
    """Return n, mean, median, P05 and P95 for each numeric metric."""

    rows: list[dict[str, object]] = []
    grouped = frame.groupby(list(groups), dropna=False, sort=True)
    for keys, block in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(groups, keys, strict=True))
        for metric in metrics:
            values = pd.to_numeric(block[metric], errors="coerce").dropna()
            row[f"{metric}_n"] = int(values.size)
            row[f"{metric}_mean"] = (
                float(values.mean()) if not values.empty else math.nan
            )
            row[f"{metric}_median"] = (
                float(values.median()) if not values.empty else math.nan
            )
            row[f"{metric}_p05"] = (
                float(values.quantile(0.05)) if not values.empty else math.nan
            )
            row[f"{metric}_p95"] = (
                float(values.quantile(0.95)) if not values.empty else math.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def proportion_summary(
    frame: pd.DataFrame,
    *,
    groups: Sequence[str],
    columns: Sequence[str],
) -> pd.DataFrame:
    """Compute count and empirical proportion for Boolean-like columns."""

    rows: list[dict[str, object]] = []
    grouped = frame.groupby(list(groups), dropna=False, sort=True)
    for keys, block in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(groups, keys, strict=True))
        for column in columns:
            values = pd.to_numeric(block[column], errors="coerce").dropna()
            row[f"{column}_n"] = int(values.size)
            row[f"{column}_rate"] = (
                float(values.mean()) if not values.empty else math.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def fit_power_law(x: Sequence[float], y: Sequence[float]) -> PowerLawFit:
    """Fit y = scale * x**exponent on strictly positive finite points."""

    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    mask = (
        np.isfinite(x_array)
        & np.isfinite(y_array)
        & (x_array > 0.0)
        & (y_array > 0.0)
    )
    x_log = np.log(x_array[mask])
    y_log = np.log(y_array[mask])
    if x_log.size < 2:
        return PowerLawFit(math.nan, math.nan, math.nan, int(x_log.size))
    exponent, intercept = np.polyfit(x_log, y_log, 1)
    fitted = exponent * x_log + intercept
    residual = float(np.sum((y_log - fitted) ** 2))
    total = float(np.sum((y_log - y_log.mean()) ** 2))
    r_squared = 1.0 - residual / total if total > 0.0 else 1.0
    return PowerLawFit(
        exponent=float(exponent),
        scale=float(np.exp(intercept)),
        r_squared=float(r_squared),
        n_points=int(x_log.size),
    )


def line_with_band(
    axis: plt.Axes,
    data: pd.DataFrame,
    *,
    x: str,
    median: str,
    low: str,
    high: str,
    color: str,
    label: str,
    marker: str = "o",
    linestyle: str = "-",
) -> None:
    """Draw a publication line plus empirical interval."""

    ordered = data.sort_values(x)
    x_values = pd.to_numeric(ordered[x], errors="coerce").to_numpy(float)
    medians = pd.to_numeric(ordered[median], errors="coerce").to_numpy(float)
    lows = pd.to_numeric(ordered[low], errors="coerce").to_numpy(float)
    highs = pd.to_numeric(ordered[high], errors="coerce").to_numpy(float)
    axis.fill_between(
        x_values,
        lows,
        highs,
        color=color,
        alpha=0.13,
        linewidth=0.0,
    )
    axis.plot(
        x_values,
        medians,
        color=color,
        marker=marker,
        linestyle=linestyle,
        label=label,
    )


def method_label(method: str) -> str:
    """Return a concise publication label for an internal method id."""

    return METHOD_LABELS.get(method, method.replace("_", " "))


def family_label(family: str) -> str:
    """Return a concise publication label for an internal family id."""

    return FAMILY_LABELS.get(family, family.replace("_", " "))


def add_sample_note(axis: plt.Axes, text: str) -> None:
    """Place a quiet sample/uncertainty note below one panel."""

    axis.text(
        0.0,
        -0.22,
        text,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=7.4,
        color=COLORS["gray"],
    )


def ensure_columns(frame: pd.DataFrame, required: Sequence[str]) -> None:
    """Fail early when a source schema no longer matches the level script."""

    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def bool_to_float(series: pd.Series) -> pd.Series:
    """Normalize Boolean/string/numeric campaign fields to {0,1,NaN}."""

    if pd.api.types.is_bool_dtype(series):
        return series.astype(float)
    normalized = series.astype(str).str.lower().map(
        {
            "true": 1.0,
            "false": 0.0,
            "1": 1.0,
            "0": 0.0,
            "none": math.nan,
            "nan": math.nan,
        }
    )
    numeric = pd.to_numeric(series, errors="coerce")
    return normalized.fillna(numeric)
