"""Summary plotting helpers for aggregate metrics."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def plot_metric_summary(
    metrics: dict[str, float],
    output_path: str | Path | None = None,
) -> Figure:
    """Create a bar chart from a mapping of metric names to values."""

    labels = list(metrics.keys())
    values = list(metrics.values())
    figure, axis = plt.subplots()
    axis.bar(labels, values, color="tab:orange")
    axis.set_ylabel("Valor")
    axis.set_title("Resumen de métricas")
    axis.tick_params(axis="x", rotation=30)
    if output_path is not None:
        figure.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    return figure
