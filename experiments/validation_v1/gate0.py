"""Deterministic correctness and physical checks for MegaGame Gate 0.

This module is intentionally independent from the future distributed controller.
It checks mathematical/physical contracts and can audit an extracted canonical
package without importing evaluator state into a controller.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml


REQUIRED_PACKAGE_FILES = (
    "README.md",
    "MANIFEST.md",
    "PACKAGE_MANIFEST.json",
    "checksums.sha256",
    "docs/01_MASTER_SPEC.md",
    "docs/02_THEOREMS_PROOFS.md",
    "docs/03_INDUSTRIAL_SCENARIOS.md",
    "docs/05_REPRODUCTION_GUIDE.md",
    "docs/06_CLAUDE_CODE_PROMPT.md",
    "docs/10_INDUSTRIAL_SOURCE_SNAPSHOT.md",
    "configs/global_defaults.yaml",
    "configs/robot_catalog.yaml",
    "configs/load_catalog.yaml",
    "configs/S00_open_floor.yaml",
    "configs/S01_single_bottleneck.yaml",
    "configs/S02_hero_three_loads.yaml",
    "configs/S03_industrial_warehouse.yaml",
    "configs/S04_failure_recourse.yaml",
    "configs/S05_network_stress.yaml",
    "configs/S06_scale_factory.yaml",
    "src/megagame/reference.py",
    "scripts/run_reference.py",
    "scripts/validate_package.py",
    "tests/test_reference_smoke.py",
)


def _as_float_array(value: Any) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError("non-finite numerical value")
    return array


def smith_rhs(x: Iterable[float], payoff: Iterable[float], gain: float = 1.0) -> np.ndarray:
    """Return the Smith pairwise-comparison vector field."""
    x_arr = _as_float_array(x).reshape(-1)
    p_arr = _as_float_array(payoff).reshape(-1)
    if x_arr.size != p_arr.size or x_arr.size == 0:
        raise ValueError("x and payoff must have the same non-zero length")
    if np.any(x_arr < -1e-12) or not np.isclose(x_arr.sum(), 1.0, atol=1e-10):
        raise ValueError("x must belong to the simplex")
    if gain < 0 or not math.isfinite(gain):
        raise ValueError("gain must be finite and non-negative")
    rhs = np.zeros_like(x_arr)
    for a in range(x_arr.size):
        inflow = np.sum(x_arr * np.maximum(p_arr[a] - p_arr, 0.0))
        outflow = np.sum(np.maximum(p_arr - p_arr[a], 0.0))
        rhs[a] = gain * (inflow - x_arr[a] * outflow)
    return rhs


def smith_euler(x: Iterable[float], payoff: Iterable[float], dt: float, gain: float = 1.0) -> np.ndarray:
    """Take the reference implementation's projected digital update."""
    if dt < 0 or not math.isfinite(dt):
        raise ValueError("dt must be finite and non-negative")
    updated = _as_float_array(x).reshape(-1) + dt * smith_rhs(x, payoff, gain)
    updated = np.maximum(updated, 0.0)
    total = float(updated.sum())
    if total <= 0 or not math.isfinite(total):
        raise FloatingPointError("simplex projection produced an invalid mass")
    return updated / total


def difference_utility(phi, state: tuple[float, ...], baseline: tuple[float, ...], agent: int) -> float:
    """Difference utility with a fixed unilateral baseline action."""
    if len(state) != len(baseline) or not 0 <= agent < len(state):
        raise ValueError("state, baseline and agent dimensions are inconsistent")
    counterfactual = list(state)
    counterfactual[agent] = baseline[agent]
    return -(float(phi(state)) - float(phi(tuple(counterfactual))))


def wrench_map(contact_positions: Iterable[Iterable[float]]) -> np.ndarray:
    positions = _as_float_array(contact_positions).reshape(-1, 2)
    if len(positions) == 0:
        raise ValueError("at least one contact is required")
    blocks = [np.array([[1.0, 0.0], [0.0, 1.0], [-y, x]]) for x, y in positions]
    return np.concatenate(blocks, axis=1)


def wrench_residual(contact_positions: Iterable[Iterable[float]], forces: Iterable[Iterable[float]], desired: Iterable[float]) -> np.ndarray:
    forces_arr = _as_float_array(forces).reshape(-1, 2)
    desired_arr = _as_float_array(desired).reshape(3)
    return wrench_map(contact_positions) @ forces_arr.reshape(-1) - desired_arr


def caging_friction_feasible(normal: Iterable[float], tangential: Iterable[float], coefficient: Iterable[float]) -> bool:
    n = _as_float_array(normal).reshape(-1)
    t = _as_float_array(tangential).reshape(-1)
    mu = _as_float_array(coefficient).reshape(-1)
    return bool(n.size == t.size == mu.size and np.all(n >= -1e-12) and np.all(mu >= -1e-12)
                and np.all(np.abs(t) <= mu * n + 1e-12))


def wheel_speeds(v: float, omega: float, radius: float, half_track: float) -> tuple[float, float]:
    if radius <= 0 or half_track <= 0 or not all(math.isfinite(q) for q in (v, omega, radius, half_track)):
        raise ValueError("invalid differential-drive parameters")
    return ((v - half_track * omega) / radius, (v + half_track * omega) / radius)


def body_velocity(left: float, right: float, radius: float, half_track: float) -> tuple[float, float]:
    return (radius * (left + right) / 2.0, radius * (right - left) / (2.0 * half_track))


def hocbf_terms(relative_position: Iterable[float], relative_velocity: Iterable[float], relative_acceleration: Iterable[float], distance: float, alpha0: float, alpha1: float) -> tuple[float, float, float, float]:
    r = _as_float_array(relative_position).reshape(2)
    vr = _as_float_array(relative_velocity).reshape(2)
    ar = _as_float_array(relative_acceleration).reshape(2)
    h = float(r @ r - distance * distance)
    hdot = float(2.0 * r @ vr)
    hddot = float(2.0 * (vr @ vr + r @ ar))
    return h, hdot, hddot, float(hddot + alpha1 * hdot + alpha0 * h)


@dataclass(frozen=True)
class BeliefRecord:
    source: int
    key: str
    seq: int
    value: tuple[float, ...]
    stamp: float
    hop: int
    confidence: float


class BeliefStore:
    """Minimal versioned store used to test provenance and duplicate handling."""

    def __init__(self) -> None:
        self.records: dict[tuple[int, str], BeliefRecord] = {}
        self.accepted_updates = 0

    def receive(self, record: BeliefRecord, now: float) -> bool:
        if record.seq < 0 or record.hop < 0 or record.stamp > now:
            return False
        identity = (record.source, record.key)
        old = self.records.get(identity)
        if old is not None and record.seq <= old.seq:
            return False
        age = max(0.0, now - record.stamp)
        confidence = record.confidence * math.exp(-0.45 * record.hop) * math.exp(-0.18 * age)
        self.records[identity] = BeliefRecord(record.source, record.key, record.seq,
                                               tuple(record.value), record.stamp, record.hop, confidence)
        self.accepted_updates += 1
        return True


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_package(root: Path) -> dict[str, Any]:
    root = root.resolve()
    missing = [relative for relative in REQUIRED_PACKAGE_FILES if not (root / relative).is_file()]
    yaml_errors: list[dict[str, str]] = []
    for path in sorted((root / "configs").glob("*.yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - exercised by corrupt packages
            yaml_errors.append({"path": path.relative_to(root).as_posix(), "error": repr(exc)})

    checksum_missing: list[str] = []
    checksum_mismatch: list[str] = []
    checksum_count = 0
    checksum_path = root / "checksums.sha256"
    if checksum_path.is_file():
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                checksum, relative = line.split("  ", 1)
            except ValueError as exc:
                raise ValueError(f"invalid checksum line: {line!r}") from exc
            checksum_count += 1
            path = root.joinpath(*relative.split("/"))
            if not path.is_file():
                checksum_missing.append(relative)
            elif _sha256(path) != checksum:
                checksum_mismatch.append(relative)

    package_manifest_count = None
    package_manifest_path = root / "PACKAGE_MANIFEST.json"
    if package_manifest_path.is_file():
        package_manifest_count = int(json.loads(package_manifest_path.read_text(encoding="utf-8"))["file_count"])
    manifest_text = (root / "MANIFEST.md").read_text(encoding="utf-8") if (root / "MANIFEST.md").is_file() else ""
    manifest_match = re.search(r"Payload files:\s*(\d+)", manifest_text)
    manifest_payload_count = int(manifest_match.group(1)) if manifest_match else None
    count_convention = {
        "manifest_payload_files": manifest_payload_count,
        "package_manifest_files": package_manifest_count,
        "checksum_entries": checksum_count,
        "checksum_extra_declared_path": "PACKAGE_MANIFEST.json" if package_manifest_count is not None else None,
        "consistent_by_inclusion": bool(
            manifest_payload_count is not None
            and package_manifest_count == manifest_payload_count + 1
            and checksum_count == package_manifest_count + 1
        ),
    }

    status = not missing and not yaml_errors and not checksum_missing and not checksum_mismatch
    return {
        "status": "passed" if status else "failed",
        "root": str(root),
        "required_file_count": len(REQUIRED_PACKAGE_FILES),
        "missing_required_files": missing,
        "yaml_files_checked": len(list((root / "configs").glob("*.yaml"))),
        "yaml_errors": yaml_errors,
        "checksum_entries_checked": checksum_count,
        "checksum_missing": checksum_missing,
        "checksum_mismatch": checksum_mismatch,
        "declared_count_convention": count_convention,
    }


def run_reference_smoke(package_root: Path, output_root: Path) -> list[dict[str, Any]]:
    summaries = []
    for scenario in ("S00_open_floor.yaml", "S01_single_bottleneck.yaml", "S02_hero_three_loads.yaml"):
        output = output_root / scenario.removesuffix(".yaml")
        command = [sys.executable, str(package_root / "scripts/run_reference.py"),
                   "--scenario", str(package_root / "configs" / scenario), "--horizon", "1", "--out", str(output)]
        completed = subprocess.run(command, cwd=package_root, check=True, text=True, capture_output=True)
        summaries.append(json.loads(completed.stdout))
    return summaries


def run_math_checks() -> dict[str, Any]:
    x = np.array([0.2, 0.3, 0.5])
    payoff = np.array([0.2, 1.1, -0.4])
    rhs = smith_rhs(x, payoff, gain=0.45)
    updated = smith_euler(x, payoff, dt=0.02, gain=0.45)
    assert abs(float(rhs.sum())) < 1e-12
    assert np.all(updated >= -1e-12) and abs(float(updated.sum()) - 1.0) < 1e-12

    phi = lambda s: (s[0] - 1.0) ** 2 + 2.0 * (s[1] + 0.5) ** 2 + 0.25 * s[0] * s[1]
    old = (0.3, -0.1)
    new = (0.8, -0.1)
    baseline = (0.0, 0.0)
    delta_u = difference_utility(phi, new, baseline, 0) - difference_utility(phi, old, baseline, 0)
    assert abs(delta_u + (phi(new) - phi(old))) < 1e-12

    contacts = np.array([[-0.8, 0.0], [0.8, 0.0], [0.0, 0.8]])
    desired = np.array([1.0, 0.4, 0.15])
    forces, *_ = np.linalg.lstsq(wrench_map(contacts), desired, rcond=None)
    residual = wrench_residual(contacts, forces.reshape(-1, 2), desired)
    assert np.linalg.norm(residual) / max(1.0, np.linalg.norm(desired)) < 1e-2
    assert caging_friction_feasible([1.0, 0.8], [0.2, -0.1], [0.5, 0.3])
    assert not caging_friction_feasible([1.0, -0.1], [0.2, 0.0], [0.5, 0.3])

    left, right = wheel_speeds(0.6, -0.4, 0.1, 0.24)
    v_back, omega_back = body_velocity(left, right, 0.1, 0.24)
    assert np.allclose([v_back, omega_back], [0.6, -0.4], atol=1e-12)

    h, hdot, hddot, barrier = hocbf_terms([2.0, 0.0], [0.0, 0.0], [0.0, 0.0], 1.0, 3.0, 3.8)
    assert h > 0 and hdot == 0 and hddot == 0 and barrier >= 0

    store = BeliefStore()
    record = BeliefRecord(2, "load:0", 14, (1.0, 2.0), 0.0, 0, 1.0)
    assert store.receive(record, now=0.0)
    assert not store.receive(record, now=0.1)
    assert not store.receive(BeliefRecord(2, "load:0", 12, (9.0, 9.0), 0.0, 1, 1.0), now=0.1)
    assert store.receive(BeliefRecord(2, "load:0", 15, (3.0, 4.0), 0.2, 1, 1.0), now=0.2)
    assert store.records[(2, "load:0")].seq == 15 and store.accepted_updates == 2

    values = np.concatenate([rhs, updated, residual, [h, hdot, hddot, barrier, left, right]])
    assert np.all(np.isfinite(values))
    return {
        "status": "passed",
        "smith_rhs_sum": float(rhs.sum()),
        "smith_simplex_sum": float(updated.sum()),
        "wrench_relative_residual": float(np.linalg.norm(residual) / max(1.0, np.linalg.norm(desired))),
        "gossip_accepted_updates": store.accepted_updates,
        "hocbf_value": barrier,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic MegaGame Gate 0 checks")
    parser.add_argument("--package-root", type=Path, help="extracted canonical package directory")
    parser.add_argument("--out", type=Path, default=Path("experiments/validation_v1/gate0/results"))
    args = parser.parse_args()

    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    math_result = run_math_checks()
    result: dict[str, Any] = {"status": "passed", "math_physical": math_result}
    if args.package_root is not None:
        package_root = args.package_root.resolve()
        package_result = audit_package(package_root)
        (args.out / "package_audit.json").write_text(json.dumps(package_result, indent=2), encoding="utf-8")
        if package_result["status"] != "passed":
            result["status"] = "failed"
        result["package_audit"] = package_result
        if package_result["status"] == "passed":
            result["reference_smoke"] = run_reference_smoke(package_root, args.out / "reference_smoke")

    (args.out / "gate0_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
