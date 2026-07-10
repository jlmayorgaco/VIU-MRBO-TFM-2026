"""Validate the vGNE force-share formula numerically."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tfm_submit_utils import THEORY_ROOT, ensure_dir, write_csv  # noqa: E402
from viu_mrob_tfm.control.explicit_law import vgne_force_share  # noqa: E402


def main() -> int:
    rng = np.random.default_rng(20260710)
    out_dir = THEORY_ROOT / "v1"
    fig_dir = out_dir / "figures"
    table_dir = out_dir / "tables"
    ensure_dir(fig_dir)
    ensure_dir(table_dir)
    rows: list[dict[str, object]] = []
    predicted: list[float] = []
    measured: list[float] = []
    for case_id in range(200):
        team_size = int(rng.integers(2, 7))
        eta = rng.uniform(0.2, 2.0, size=team_size)
        h_sum = float(np.sum(eta))
        wrench = np.array([rng.uniform(5.0, 80.0), rng.uniform(-20.0, 20.0), 0.0])
        if np.linalg.norm(wrench[:2]) < 1e-9:
            wrench[0] = 10.0
        offsets = rng.normal(0.0, 0.5, size=(team_size, 2))
        s_sum = float(np.sum(eta * np.sum(offsets * offsets, axis=1)))
        for i in range(team_size):
            force = vgne_force_share(wrench, offsets[i], float(eta[i]), h_sum, s_sum)
            share_measured = float(np.dot(force, wrench[:2]) / max(float(np.dot(wrench[:2], wrench[:2])), 1e-9))
            share_pred = float(eta[i] / h_sum)
            predicted.append(share_pred)
            measured.append(share_measured)
            rows.append(
                {
                    "case_id": case_id,
                    "robot_id": i,
                    "team_size": team_size,
                    "eta_i": eta[i],
                    "h_sum": h_sum,
                    "share_pred_eta_over_H": share_pred,
                    "share_measured_projection": share_measured,
                    "abs_error": abs(share_measured - share_pred),
                }
            )
    pred = np.asarray(predicted)
    meas = np.asarray(measured)
    err = meas - pred
    rmse = float(np.sqrt(np.mean(err**2)))
    mae = float(np.mean(np.abs(err)))
    r2 = float(1.0 - np.sum(err**2) / max(np.sum((meas - np.mean(meas)) ** 2), 1e-12))
    write_csv(
        table_dir / "v1_share_vs_theory.csv",
        rows,
        ["case_id", "robot_id", "team_size", "eta_i", "h_sum", "share_pred_eta_over_H", "share_measured_projection", "abs_error"],
    )
    fig, ax = plt.subplots(figsize=(5.2, 4.4), dpi=150)
    ax.scatter(pred, meas, s=12, alpha=0.55)
    lim = [0.0, max(float(pred.max()), float(meas.max())) * 1.05]
    ax.plot(lim, lim, color="black", linewidth=1.2, label="teoria = medicion")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Prediccion eta_i / H")
    ax.set_ylabel("Medicion por proyeccion de fuerza")
    ax.set_title("V1 reparto vGNE")
    ax.grid(True, alpha=0.25)
    ax.legend()
    ax.text(0.02, 0.96, f"RMSE={rmse:.2e}\nMAE={mae:.2e}\nR2={r2:.4f}", transform=ax.transAxes, va="top")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_v1_share_vs_theory.png")
    fig.savefig(fig_dir / "fig_v1_share_vs_theory.pdf")
    plt.close(fig)
    manifest = {
        "validation": "V1 vGNE share",
        "seed": 20260710,
        "n_rows": len(rows),
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "figure_png": str((fig_dir / "fig_v1_share_vs_theory.png").relative_to(ROOT)),
        "table": str((table_dir / "v1_share_vs_theory.csv").relative_to(ROOT)),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"V1 RMSE={rmse:.3e}; wrote {out_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
