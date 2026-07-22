from __future__ import annotations

from pathlib import Path

import pandas as pd

from viu_mrob_tfm.sp1_canonical.validation.visualization import (
    load_selected_trajectories,
    select_representative_runs,
)


def _run_row(
    *,
    scenario: str,
    n_robots: int,
    seed: int,
    arrival_time: float,
    success: bool = True,
    arrival_rate: float = 1.0,
) -> dict[str, object]:
    return {
        "scenario": scenario,
        "n_robots": n_robots,
        "n_loads": max(1, n_robots // 5),
        "seed": seed,
        "world_hash": f"hash-{scenario}-{n_robots}-{seed}",
        "assignment_feasible": True,
        "arrival_success": success,
        "arrival_rate": arrival_rate,
        "coalition_arrival_time_s": arrival_time,
    }


def test_select_representative_runs_uses_successful_median_and_deterministic_fallback() -> None:
    runs = pd.DataFrame(
        [
            _run_row(scenario="open", n_robots=8, seed=1, arrival_time=2.0),
            _run_row(scenario="open", n_robots=8, seed=2, arrival_time=5.0),
            _run_row(scenario="open", n_robots=8, seed=3, arrival_time=9.0),
            _run_row(
                scenario="warehouse",
                n_robots=8,
                seed=4,
                arrival_time=float("nan"),
                success=False,
                arrival_rate=0.75,
            ),
            _run_row(
                scenario="warehouse",
                n_robots=8,
                seed=5,
                arrival_time=float("nan"),
                success=False,
                arrival_rate=0.50,
            ),
        ]
    )

    selected = select_representative_runs(runs)

    open_row = selected[selected.scenario == "open"].iloc[0]
    warehouse_row = selected[selected.scenario == "warehouse"].iloc[0]
    assert int(open_row.seed) == 2
    assert open_row.selection_reason == "successful_nearest_median_arrival_time"
    assert int(warehouse_row.seed) == 4
    assert warehouse_row.selection_reason == "fallback_highest_arrival_rate"


def test_load_selected_trajectories_filters_large_csv_by_case(tmp_path: Path) -> None:
    selected = pd.DataFrame(
        [
            _run_row(scenario="open", n_robots=8, seed=2, arrival_time=5.0),
            _run_row(scenario="warehouse", n_robots=20, seed=3, arrival_time=8.0),
        ]
    )
    rows = []
    for scenario, n_robots, seed in (
        ("open", 8, 2),
        ("warehouse", 20, 3),
        ("open", 8, 99),
    ):
        for time_s in (0.0, 1.0):
            rows.append(
                {
                    "scenario": scenario,
                    "n_robots": n_robots,
                    "seed": seed,
                    "world_hash": f"hash-{scenario}-{n_robots}-{seed}",
                    "time_s": time_s,
                }
            )
    path = tmp_path / "e6_trajectories.csv"
    pd.DataFrame(rows).to_csv(path, index=False)

    result = load_selected_trajectories(path, selected, chunksize=2)

    assert len(result) == 4
    assert set(result.seed) == {2, 3}
