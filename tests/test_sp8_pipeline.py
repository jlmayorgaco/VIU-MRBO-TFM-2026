from pathlib import Path
import csv

from viu_mrob_tfm.sp8 import run_sp8_config
from viu_mrob_tfm.sp8.methods import make_sp8_allocator
from viu_mrob_tfm.sp8.metrics import evaluate_sp8_assignment
from viu_mrob_tfm.sp8.scenario import SP8ScaleParams, build_sp8_problem, iter_sp8_problems


def test_sp8_problem_generator_shapes():
    *_meta, params, problem = next(iter_sp8_problems(["debug"], [9800]))
    assert problem.robot_xy.shape == (params.n_robots, 2)
    assert problem.load_pickup_xy.shape == (params.n_loads, 2)
    assert problem.wrench_demands.shape == (params.n_loads, 3)
    assert problem.obstacle_xy.shape[0] == params.obstacle_count


def test_sp8_centralized_oracle_declares_timeout_at_large_scale():
    params = SP8ScaleParams(scenario_id="large_test", n_robots=300, n_loads=100, obstacle_count=4, mobile_obstacle_count=2)
    problem = build_sp8_problem(params, seed=9801)
    assignment = make_sp8_allocator("centralized_coalition_oracle", {"timeout_s": 0.1}).allocate(problem)
    assert not assignment.solved
    assert assignment.status == "timeout_declared_intractable"


def test_sp8_extended_fleet_ladder_contains_requested_scale_points():
    problems = list(iter_sp8_problems(["fleet_ladder_extended"], [10000]))
    sizes = [params.n_robots for *_prefix, params, _problem in problems]
    assert sizes == [
        5,
        10,
        25,
        50,
        100,
        250,
        500,
        1000,
        1250,
        1500,
        2000,
        2500,
        5000,
        7500,
        10000,
        12500,
        15000,
        20000,
        25000,
        50000,
    ]
    assert len(sizes) == len(set(sizes))


def test_sp8_large_hierarchical_allocator_avoids_dense_timeout():
    params = SP8ScaleParams(scenario_id="large_50k", n_robots=50_000, n_loads=12_500, world_size_m=3000.0, obstacle_count=16, mobile_obstacle_count=6)
    problem = build_sp8_problem(params, seed=10001)
    assignment = make_sp8_allocator("ours_wrench_market_hierarchical").allocate(problem)
    assert assignment.solved
    assert assignment.labels.shape == (50_000,)


def test_sp8_wrench_metrics_are_bounded():
    *_meta, _params, problem = next(iter_sp8_problems(["debug"], [9802]))
    assignment = make_sp8_allocator("ours_wrench_market_hierarchical").allocate(problem)
    metrics, load_rows = evaluate_sp8_assignment(problem, assignment)
    assert 0.0 <= metrics.wrench_feasible_rate <= 1.0
    assert 0.0 <= metrics.transport_success_rate <= 1.0
    assert load_rows


def test_sp8_runner_smoke_outputs_tables_figures_and_audit():
    result = run_sp8_config(Path("configs/experiments/sp8/SP8_DEBUG_smoke.yaml"))
    output_dir = Path(result["output_dir"])
    assert result["failed_theory_checks"] == 0
    for relative in [
        "report.md",
        "tables/runs.csv",
        "tables/summary.csv",
        "tables/performance_ranking.csv",
        "tables/load_status.csv",
        "tables/hypothesis_results.csv",
        "tables/theory_checks.csv",
        "theory_audit.json",
        "figures/sp8_runtime_scaling_loglog.png",
        "figures/sp8_timeout_boundary.png",
    ]:
        assert (output_dir / relative).exists()
    rows = _read_rows(output_dir / "tables/runs.csv")
    assert {"n_robots", "n_loads", "wrench_feasible_rate", "timeout_rate"}.issubset(rows[0])


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
