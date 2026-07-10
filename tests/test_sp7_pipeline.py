from pathlib import Path
import csv

import numpy as np

from viu_mrob_tfm.sp5.methods import simulate_transport
from viu_mrob_tfm.sp7 import run_sp7_config
from viu_mrob_tfm.sp7.methods import make_sp7_policy
from viu_mrob_tfm.sp7.metrics import network_frame_metrics
from viu_mrob_tfm.sp7.scenario import CommunicationProfile, iter_sp7_problems


def test_sp7_generates_communication_profiles_and_worlds():
    worlds = list(iter_sp7_problems(["setup"], [8700]))
    assert worlds
    _generator, _variant, _seed, sp7_params, _sp5_params, problem = worlds[0]
    assert sp7_params.profile.communication_radius_m > 0
    assert len(problem.world.robots) > 0
    assert len(problem.world.loads) > 0


def test_sp7_network_trace_detects_radius_degradation():
    *_prefix, sp7_params, sp5_params, problem = next(iter_sp7_problems(["setup"], [8701]))
    policy = make_sp7_policy("ours_connectivity_wrench_game", sp7_params.profile, transport_mode=sp5_params.transport_mode)
    result = simulate_transport(policy, problem)
    wide = CommunicationProfile(profile_id="wide", communication_radius_m=float("inf"))
    narrow = CommunicationProfile(profile_id="narrow", communication_radius_m=2.2, packet_loss_probability=0.2)
    wide_frames = network_frame_metrics(problem, result, wide, seed=8701, method_id="ours_connectivity_wrench_game")
    narrow_frames = network_frame_metrics(problem, result, narrow, seed=8701, method_id="ours_connectivity_wrench_game")
    wide_conn = np.mean([float(frame.coalition_connected) for frame in wide_frames])
    narrow_conn = np.mean([float(frame.coalition_connected) for frame in narrow_frames])
    assert wide_conn >= narrow_conn


def test_sp7_runner_smoke_outputs_tables_figures_videos_and_audit():
    result = run_sp7_config(Path("configs/experiments/sp7/SP7_DEBUG_smoke.yaml"))
    output_dir = Path(result["output_dir"])
    assert result["failed_theory_checks"] == 0
    for relative in [
        "report.md",
        "tables/runs.csv",
        "tables/summary.csv",
        "tables/performance_ranking.csv",
        "tables/network_timeseries.csv",
        "tables/hypothesis_results.csv",
        "tables/theory_checks.csv",
        "tables/video_catalog.csv",
        "theory_audit.json",
        "figures/sp7_connectivity_vs_radius_by_method.png",
        "figures/sp7_transport_success_under_network_stress.png",
        "videos/VIDEO_INDEX.md",
    ]:
        assert (output_dir / relative).exists()
    rows = _read_rows(output_dir / "tables/runs.csv")
    assert {"coalition_connected_time_ratio", "packet_delivery_ratio", "sensor_coverage_rate"}.issubset(rows[0])
    assert "min_load_clearance_m" in rows[0]
    assert all(float(row["min_load_clearance_m"]) >= -1e-6 for row in rows)
    assert any(row["communication_profile"] != "nominal_full_mesh" for row in rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
