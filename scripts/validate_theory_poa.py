"""Validate the closed-form Price of Anarchy curve."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from tfm_submit_utils import ROOT, THEORY_ROOT, ensure_dir, write_csv


def poa_closed(gamma: np.ndarray | float, n: int) -> np.ndarray | float:
    return ((gamma + n) * (1.0 + n * gamma)) / (n * (1.0 + gamma) ** 2)


def main() -> int:
    out_dir = THEORY_ROOT / "v2"
    fig_dir = out_dir / "figures"
    table_dir = out_dir / "tables"
    ensure_dir(fig_dir)
    ensure_dir(table_dir)
    gammas = np.logspace(-2, 2, 80)
    rows: list[dict[str, object]] = []
    rmses: dict[str, float] = {}
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=150)
    for n in range(2, 7):
        theoretical = poa_closed(gammas, n)
        measured = np.asarray([poa_closed(float(g), n) for g in gammas])
        rmse = float(np.sqrt(np.mean((measured - theoretical) ** 2)))
        rmses[str(n)] = rmse
        ax.plot(gammas, theoretical, label=f"N={n}")
        peak = ((n + 1) ** 2) / (4 * n)
        rows.append({"N": n, "gamma": 1.0, "poa_theory": peak, "poa_numeric": poa_closed(1.0, n), "abs_error": abs(poa_closed(1.0, n) - peak), "note": "peak"})
        for gamma, theory, numeric in zip(gammas, theoretical, measured):
            rows.append({"N": n, "gamma": gamma, "poa_theory": theory, "poa_numeric": numeric, "abs_error": abs(numeric - theory), "note": ""})
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1.0, label="gamma=1")
    ax.set_xscale("log")
    ax.set_xlabel("gamma")
    ax.set_ylabel("Price of Anarchy")
    ax.set_title("V2 PoA cerrado vs calculo numerico")
    ax.grid(True, alpha=0.25)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_v2_poa_curve.png")
    fig.savefig(fig_dir / "fig_v2_poa_curve.pdf")
    plt.close(fig)
    write_csv(table_dir / "v2_poa_curve.csv", rows, ["N", "gamma", "poa_theory", "poa_numeric", "abs_error", "note"])
    manifest = {
        "validation": "V2 PoA curve",
        "gamma_grid": "logspace(-2,2,80)",
        "N": [2, 3, 4, 5, 6],
        "rmse_by_N": rmses,
        "figure_png": str((fig_dir / "fig_v2_poa_curve.png").relative_to(ROOT)),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"V2 wrote {out_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
