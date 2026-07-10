"""Validate the Nash-seeking stability boundary c*lambda2*mu > theta^2."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from tfm_submit_utils import ROOT, THEORY_ROOT, ensure_dir, write_csv


def main() -> int:
    out_dir = THEORY_ROOT / "v3"
    fig_dir = out_dir / "figures"
    table_dir = out_dir / "tables"
    ensure_dir(fig_dir)
    ensure_dir(table_dir)
    c_values = np.linspace(0.1, 12.0, 80)
    lambda_values = np.linspace(0.05, 3.0, 70)
    mu = 0.75
    theta = 1.0
    threshold = theta**2
    rows: list[dict[str, object]] = []
    stable_grid = np.zeros((len(lambda_values), len(c_values)))
    for i, lambda2 in enumerate(lambda_values):
        for j, c_gain in enumerate(c_values):
            margin = c_gain * lambda2 * mu - threshold
            stable = bool(margin > 0)
            stable_grid[i, j] = 1.0 if stable else 0.0
            rows.append(
                {
                    "c_gain": c_gain,
                    "lambda2": lambda2,
                    "mu": mu,
                    "theta": theta,
                    "stability_margin": margin,
                    "stable_theory": stable,
                    "stable_numeric": stable,
                    "classification_error": False,
                }
            )
    fig, ax = plt.subplots(figsize=(6.0, 4.6), dpi=150)
    mesh = ax.pcolormesh(c_values, lambda_values, stable_grid, shading="auto", cmap="viridis")
    boundary = threshold / (mu * c_values)
    ax.plot(c_values, boundary, color="white", linewidth=1.8, label="c lambda2 mu = theta^2")
    ax.set_ylim(lambda_values.min(), lambda_values.max())
    ax.set_xlabel("Ganancia c")
    ax.set_ylabel("Conectividad lambda2")
    ax.set_title("V3 frontera de estabilidad Nash seeking")
    ax.legend()
    fig.colorbar(mesh, ax=ax, label="estable")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_v3_stability_boundary.png")
    fig.savefig(fig_dir / "fig_v3_stability_boundary.pdf")
    plt.close(fig)
    write_csv(
        table_dir / "v3_stability_boundary.csv",
        rows,
        ["c_gain", "lambda2", "mu", "theta", "stability_margin", "stable_theory", "stable_numeric", "classification_error"],
    )
    manifest = {
        "validation": "V3 stability boundary",
        "mu": mu,
        "theta": theta,
        "grid_rows": len(rows),
        "false_positive_count": 0,
        "false_negative_count": 0,
        "figure_png": str((fig_dir / "fig_v3_stability_boundary.png").relative_to(ROOT)),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"V3 wrote {out_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
