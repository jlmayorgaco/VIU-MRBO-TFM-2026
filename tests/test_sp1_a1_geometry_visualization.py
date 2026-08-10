from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pytest


matplotlib.use("Agg")

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "sp1_a1_hungarian.py"
MODULE_NAME = "sp1_a1_geometry_visualization_under_test"

SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
HUNGARIAN = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = HUNGARIAN
SPEC.loader.exec_module(HUNGARIAN)


def build_cases(
    *,
    m_slots: int = 10,
) -> dict[str, tuple[list[object], list[object]]]:
    return HUNGARIAN.build_geometry_visualization_cases(
        seed=20260728,
        m_slots=m_slots,
        delta=0.20,
        q_bar=5.0,
        workspace_width=100.0,
        workspace_height=100.0,
    )


def result_signature(result: object) -> tuple[object, ...]:
    return (
        tuple(
            (item.robot_id, item.slot_id, item.load_id, item.cost)
            for item in result.assignments
        ),
        tuple(
            (load_id, tuple(members))
            for load_id, members in result.coalitions.items()
        ),
        tuple(result.idle_robots),
        result.total_cost,
        result.feasible,
        result.coverage,
    )


def test_paired_cases_share_logical_instance_and_only_positions_change() -> None:
    cases = build_cases(m_slots=20)
    assert tuple(cases) == HUNGARIAN.GEOMETRY_NAMES

    signatures = []
    positions = []
    for robots, loads in cases.values():
        quotas = tuple(
            HUNGARIAN.required_robot_count(load, 5.0)
            for load in loads
        )
        signatures.append(
            (
                len(robots),
                len(loads),
                tuple(robot.id for robot in robots),
                tuple(load.id for load in loads),
                tuple(load.mass for load in loads),
                quotas,
            )
        )
        positions.append(
            tuple((robot.x, robot.y) for robot in robots)
            + tuple((load.x, load.y) for load in loads)
        )
        assert sum(quotas) == 20
        assert len(robots) == 30

    assert all(signature == signatures[0] for signature in signatures)
    assert len(set(positions)) == len(HUNGARIAN.GEOMETRY_NAMES)


def test_one_solver_call_per_geometry_and_complete_disjoint_coalitions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = build_cases()
    original_solver = HUNGARIAN.solve_hungarian
    calls = 0

    def counted_solver(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return original_solver(*args, **kwargs)

    monkeypatch.setattr(HUNGARIAN, "solve_hungarian", counted_solver)
    results = HUNGARIAN.solve_geometry_visualization_cases(
        cases=cases,
        q_bar=5.0,
    )

    assert calls == len(HUNGARIAN.GEOMETRY_NAMES)
    for result in results.values():
        assigned = [item.robot_id for item in result.assignments]
        assert result.feasible
        assert len(assigned) == len(result.slots) == 10
        assert len(assigned) == len(set(assigned))
        assert all(
            len(result.coalitions[load_id]) == quota
            for load_id, quota in result.required_cardinality.items()
        )


def test_motion_preview_preserves_objects_and_idle_robot_positions() -> None:
    cases = build_cases()
    robots, loads = cases["uniform"]
    result = HUNGARIAN.solve_hungarian(robots, loads, 5.0)
    snapshot = tuple((robot.id, robot.x, robot.y) for robot in robots)
    targets = HUNGARIAN.build_motion_preview_positions(
        robots,
        loads,
        result,
        100.0,
        100.0,
    )

    assert tuple((robot.id, robot.x, robot.y) for robot in robots) == snapshot
    robot_by_id = {robot.id: robot for robot in robots}
    assert all(
        np.array_equal(targets[robot_id], robot_by_id[robot_id].position)
        for robot_id in result.idle_robots
    )
    assert any(
        not np.array_equal(targets[item.robot_id], robot_by_id[item.robot_id].position)
        for item in result.assignments
    )


def test_plot_has_one_link_per_assignment_and_does_not_change_result(
    tmp_path: Path,
) -> None:
    robots, loads = build_cases()["ring"]
    before = HUNGARIAN.solve_hungarian(robots, loads, 5.0)
    output = tmp_path / "ring_assignment.png"
    line_count = HUNGARIAN.plot_geometry_case(
        robots,
        loads,
        before,
        "ring",
        100.0,
        100.0,
        output,
        show=False,
    )
    after = HUNGARIAN.solve_hungarian(robots, loads, 5.0)

    assert line_count == len(before.assignments)
    assert result_signature(before) == result_signature(after)
    assert output.is_file()
    assert output.stat().st_size > 0


def test_static_package_manifest_hashes_and_csv_non_regression(
    tmp_path: Path,
) -> None:
    protected_csv = tmp_path / "mc_scaling.csv"
    protected_csv.write_bytes(b"sentinel,csv\n1,2\n")
    before = protected_csv.read_bytes()

    manifest = HUNGARIAN.run_geometry_visualization(
        seed=20260728,
        m_slots=10,
        delta=0.20,
        q_bar=5.0,
        workspace_width=100.0,
        workspace_height=100.0,
        fps=2,
        duration_seconds=0.5,
        make_videos=False,
        include_motion_preview=True,
        output_dir=tmp_path,
        show=False,
    )

    assert protected_csv.read_bytes() == before
    assert len(manifest["scenarios"]) == 5
    assert (
        json.loads(
            (tmp_path / "geometry_visualization_manifest.json").read_text(
                encoding="utf-8"
            )
        )["scenarios"].keys()
        == manifest["scenarios"].keys()
    )
    for record in manifest["scenarios"].values():
        png = tmp_path / record["png_path"]
        assert png.is_file()
        assert png.stat().st_size > 0
        assert HUNGARIAN.sha256_file(png) == record["sha256"]["png"]
        assert record["video_path"] is None


def test_tiny_animation_writes_mp4_or_gif(tmp_path: Path) -> None:
    robots, loads = build_cases()["corridor"]
    result = HUNGARIAN.solve_hungarian(robots, loads, 5.0)
    metadata = HUNGARIAN.animate_geometry_recruitment(
        robots,
        loads,
        result,
        "corridor",
        tmp_path / "corridor_recruitment.mp4",
        100.0,
        100.0,
        fps=2,
        duration_seconds=0.5,
        include_motion_preview=True,
    )

    output = Path(metadata["path"])
    assert metadata["format"] in {"mp4", "gif"}
    assert metadata["frames"] == 2
    assert output.suffix == f".{metadata['format']}"
    assert output.is_file()
    assert output.stat().st_size > 0


def test_forced_ffmpeg_fallback_writes_gif(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    robots, loads = build_cases()["uniform"]
    result = HUNGARIAN.solve_hungarian(robots, loads, 5.0)
    monkeypatch.setattr(HUNGARIAN, "check_ffmpeg_available", lambda: False)

    metadata = HUNGARIAN.animate_geometry_recruitment(
        robots,
        loads,
        result,
        "uniform",
        tmp_path / "uniform_recruitment.mp4",
        100.0,
        100.0,
        fps=2,
        duration_seconds=0.5,
        include_motion_preview=False,
    )

    output = Path(metadata["path"])
    assert metadata["format"] == "gif"
    assert output.suffix == ".gif"
    assert output.is_file()
    assert output.stat().st_size > 0
