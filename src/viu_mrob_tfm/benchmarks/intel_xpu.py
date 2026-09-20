"""Reproducible CPU--Intel XPU diagnostic benchmark.

This module is deliberately separate from the confirmatory experiments.  It
checks whether an Intel GPU is usable and estimates the crossover between CPU
and XPU for dense tensor work and an SP1-inspired population update.  It does
not accelerate SciPy/HiGHS or establish a thesis claim.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRESETS: dict[str, list[dict[str, Any]]] = {
    "smoke": [
        {
            "name": "matmul_512",
            "kernel": "matmul",
            "size": 512,
            "iterations": 1,
            "warmups": 1,
            "repetitions": 2,
        },
        {
            "name": "sp1_single_world",
            "kernel": "sp1_population",
            "batch": 1,
            "n_robots": 500,
            "n_loads": 8,
            "n_resources": 3,
            "iterations": 20,
            "warmups": 1,
            "repetitions": 2,
        },
    ],
    "quick": [
        {
            "name": "matmul_512",
            "kernel": "matmul",
            "size": 512,
            "iterations": 1,
            "warmups": 4,
            "repetitions": 7,
        },
        {
            "name": "matmul_2048",
            "kernel": "matmul",
            "size": 2048,
            "iterations": 1,
            "warmups": 4,
            "repetitions": 5,
        },
        {
            "name": "matmul_4096",
            "kernel": "matmul",
            "size": 4096,
            "iterations": 1,
            "warmups": 4,
            "repetitions": 3,
        },
        {
            "name": "sp1_single_world",
            "kernel": "sp1_population",
            "batch": 1,
            "n_robots": 500,
            "n_loads": 8,
            "n_resources": 3,
            "iterations": 200,
            "warmups": 4,
            "repetitions": 5,
        },
        {
            "name": "sp1_batch_64",
            "kernel": "sp1_population",
            "batch": 64,
            "n_robots": 500,
            "n_loads": 8,
            "n_resources": 3,
            "iterations": 50,
            "warmups": 4,
            "repetitions": 5,
        },
        {
            "name": "sp1_batch_256",
            "kernel": "sp1_population",
            "batch": 256,
            "n_robots": 500,
            "n_loads": 8,
            "n_resources": 3,
            "iterations": 20,
            "warmups": 4,
            "repetitions": 3,
        },
    ],
}


def summarize_timings(cpu_s: list[float], xpu_s: list[float], xpu_e2e_s: list[float]) -> dict[str, float]:
    """Summarize paired device timings using medians.

    ``speedup`` is CPU time divided by XPU time, so values above one favor the
    GPU.  The function is independent of PyTorch to keep ordinary test suites
    usable on machines without XPU.
    """

    if not cpu_s or not xpu_s or not xpu_e2e_s:
        raise ValueError("timing collections must be non-empty")
    cpu_median = float(statistics.median(cpu_s))
    xpu_median = float(statistics.median(xpu_s))
    e2e_median = float(statistics.median(xpu_e2e_s))
    return {
        "cpu_median_s": cpu_median,
        "cpu_min_s": float(min(cpu_s)),
        "cpu_max_s": float(max(cpu_s)),
        "xpu_resident_median_s": xpu_median,
        "xpu_resident_min_s": float(min(xpu_s)),
        "xpu_resident_max_s": float(max(xpu_s)),
        "xpu_end_to_end_median_s": e2e_median,
        "xpu_end_to_end_min_s": float(min(xpu_e2e_s)),
        "xpu_end_to_end_max_s": float(max(xpu_e2e_s)),
        "speedup_resident_cpu_over_xpu": cpu_median / max(xpu_median, 1e-15),
        "speedup_end_to_end_cpu_over_xpu": cpu_median / max(e2e_median, 1e-15),
    }


def validate_preset(name: str) -> None:
    if name not in PRESETS:
        raise ValueError(f"unknown preset: {name}")
    case_names = [str(case["name"]) for case in PRESETS[name]]
    if len(case_names) != len(set(case_names)):
        raise ValueError(f"duplicate case names in preset {name}")
    for case in PRESETS[name]:
        if int(case["iterations"]) <= 0 or int(case["repetitions"]) <= 0:
            raise ValueError(f"invalid iteration budget in {case['name']}")
        if case["kernel"] not in {"matmul", "sp1_population"}:
            raise ValueError(f"unknown kernel in {case['name']}")


def _sync(torch: Any, device: Any) -> None:
    if device.type == "xpu":
        torch.xpu.synchronize(device)


def _make_inputs(torch: Any, case: dict[str, Any], seed: int) -> dict[str, Any]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    if case["kernel"] == "matmul":
        size = int(case["size"])
        return {
            "a": torch.randn((size, size), generator=generator, dtype=torch.float32),
            "b": torch.randn((size, size), generator=generator, dtype=torch.float32),
        }
    batch = int(case["batch"])
    n = int(case["n_robots"])
    k = int(case["n_loads"])
    m = int(case["n_resources"])
    raw = torch.rand((batch, n, k + 1), generator=generator, dtype=torch.float32) + 0.05
    state = raw / raw.sum(dim=-1, keepdim=True)
    return {
        "state": state,
        "dual": torch.zeros((batch, k, m), dtype=torch.float32),
        "costs": torch.rand((batch, n, k), generator=generator, dtype=torch.float32),
        "normalized": 0.35
        + 0.9 * torch.rand((batch, n, k, m), generator=generator, dtype=torch.float32),
    }


def _move_inputs(inputs: dict[str, Any], device: Any) -> dict[str, Any]:
    return {name: tensor.to(device) for name, tensor in inputs.items()}


def _matmul_kernel(inputs: dict[str, Any], iterations: int) -> Any:
    result = inputs["a"] @ inputs["b"]
    for _ in range(1, int(iterations)):
        result = inputs["a"] @ inputs["b"]
    return result


def _sp1_population_kernel(torch: Any, inputs: dict[str, Any], iterations: int) -> tuple[Any, Any]:
    """Central primal--dual update shaped like the SP1 tensor operations."""

    state = inputs["state"]
    dual = inputs["dual"]
    costs = inputs["costs"]
    normalized = inputs["normalized"]
    step = 0.03
    entropy_tau = 0.003
    for _ in range(int(iterations)):
        load_gradient = costs - torch.einsum("bkm,bnkm->bnk", dual, normalized)
        gradient = torch.cat([load_gradient, torch.zeros_like(state[..., :1])], dim=-1)
        gradient = gradient + entropy_tau * (torch.log(torch.clamp(state, min=1e-12)) + 1.0)
        candidate = state * torch.exp(torch.clamp(-step * gradient, min=-30.0, max=30.0))
        state = candidate / torch.clamp(candidate.sum(dim=-1, keepdim=True), min=1e-12)
        coverage = torch.einsum("bnk,bnkm->bkm", state[..., :-1], normalized)
        dual = torch.clamp(dual + step * (1.0 - coverage), min=0.0)
    return state, dual


def _call_kernel(torch: Any, case: dict[str, Any], inputs: dict[str, Any]) -> Any:
    if case["kernel"] == "matmul":
        return _matmul_kernel(inputs, int(case["iterations"]))
    return _sp1_population_kernel(torch, inputs, int(case["iterations"]))


def _to_cpu(output: Any) -> tuple[Any, ...]:
    values = output if isinstance(output, tuple) else (output,)
    return tuple(value.detach().cpu() for value in values)


def _time_resident(
    torch: Any,
    case: dict[str, Any],
    cpu_inputs: dict[str, Any],
    device: Any,
) -> tuple[list[float], tuple[Any, ...]]:
    inputs = _move_inputs(cpu_inputs, device)
    output: Any = None
    for _ in range(int(case["warmups"])):
        output = _call_kernel(torch, case, inputs)
        _sync(torch, device)
    durations: list[float] = []
    for _ in range(int(case["repetitions"])):
        _sync(torch, device)
        started = time.perf_counter()
        output = _call_kernel(torch, case, inputs)
        _sync(torch, device)
        durations.append(time.perf_counter() - started)
    return durations, _to_cpu(output)


def _time_xpu_end_to_end(
    torch: Any,
    case: dict[str, Any],
    cpu_inputs: dict[str, Any],
    device: Any,
) -> list[float]:
    for _ in range(int(case["warmups"])):
        inputs = _move_inputs(cpu_inputs, device)
        output = _call_kernel(torch, case, inputs)
        _to_cpu(output)
        _sync(torch, device)
    durations: list[float] = []
    for _ in range(int(case["repetitions"])):
        _sync(torch, device)
        started = time.perf_counter()
        inputs = _move_inputs(cpu_inputs, device)
        output = _call_kernel(torch, case, inputs)
        _to_cpu(output)
        _sync(torch, device)
        durations.append(time.perf_counter() - started)
    return durations


def _accuracy(torch: Any, expected: tuple[Any, ...], observed: tuple[Any, ...]) -> dict[str, Any]:
    maximum = 0.0
    squared_error = 0.0
    squared_reference = 0.0
    close = True
    for cpu_value, xpu_value in zip(expected, observed, strict=True):
        difference = (cpu_value - xpu_value).double()
        maximum = max(maximum, float(torch.max(torch.abs(difference))))
        squared_error += float(torch.sum(difference * difference))
        reference = cpu_value.double()
        squared_reference += float(torch.sum(reference * reference))
        close = close and bool(torch.allclose(cpu_value, xpu_value, rtol=5e-3, atol=5e-4))
    relative_l2 = math.sqrt(squared_error) / max(math.sqrt(squared_reference), 1e-15)
    return {
        "max_abs_error": maximum,
        "relative_l2_error": relative_l2,
        "numerically_consistent": close,
    }


def _shape_label(case: dict[str, Any]) -> str:
    if case["kernel"] == "matmul":
        return f"{case['size']}x{case['size']}"
    return (
        f"B={case['batch']},N={case['n_robots']},K={case['n_loads']},"
        f"M={case['n_resources']}"
    )


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run(preset: str, output_dir: Path, *, seed: int, cpu_threads: int) -> dict[str, Any]:
    validate_preset(preset)
    import torch

    if not torch.xpu.is_available():
        raise RuntimeError("PyTorch XPU is not available; install the XPU wheel and check the Intel driver")
    if cpu_threads > 0:
        torch.set_num_threads(int(cpu_threads))
    cpu = torch.device("cpu")
    xpu = torch.device("xpu:0")
    rows: list[dict[str, Any]] = []
    for index, case in enumerate(PRESETS[preset]):
        inputs = _make_inputs(torch, case, seed + index)
        cpu_times, cpu_output = _time_resident(torch, case, inputs, cpu)
        xpu_times, xpu_output = _time_resident(torch, case, inputs, xpu)
        e2e_times = _time_xpu_end_to_end(torch, case, inputs, xpu)
        row = {
            "case": str(case["name"]),
            "kernel": str(case["kernel"]),
            "shape": _shape_label(case),
            "iterations": int(case["iterations"]),
            "warmups": int(case["warmups"]),
            "repetitions": int(case["repetitions"]),
            **summarize_timings(cpu_times, xpu_times, e2e_times),
            **_accuracy(torch, cpu_output, xpu_output),
            "cpu_samples_s": json.dumps(cpu_times),
            "xpu_resident_samples_s": json.dumps(xpu_times),
            "xpu_end_to_end_samples_s": json.dumps(e2e_times),
        }
        rows.append(row)
        print(
            f"{row['case']}: CPU={row['cpu_median_s']:.6f}s, "
            f"XPU={row['xpu_resident_median_s']:.6f}s, "
            f"speedup={row['speedup_resident_cpu_over_xpu']:.2f}x, "
            f"e2e={row['speedup_end_to_end_cpu_over_xpu']:.2f}x"
        )

    properties = torch.xpu.get_device_properties(0)
    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "diagnostic_only": True,
        "preset": preset,
        "seed": int(seed),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "torch_xpu_compiled": bool(torch.xpu._is_compiled()),
        "torch_xpu_available": bool(torch.xpu.is_available()),
        "xpu_device_name": torch.xpu.get_device_name(0),
        "xpu_device_properties": str(properties),
        "cpu_model": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "cpu_threads_used_by_torch": int(torch.get_num_threads()),
        "logical_cpus": os.cpu_count(),
        "git_commit": _git_commit(),
        "timing_scope": {
            "cpu_median_s": "resident CPU tensors and synchronized operation",
            "xpu_resident_median_s": "resident XPU tensors and synchronized operation",
            "xpu_end_to_end_median_s": "host-to-XPU copy, synchronized operation, and XPU-to-host copy",
        },
    }
    payload = {"metadata": metadata, "cases": rows}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "benchmark.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (output_dir / "benchmark.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="quick")
    parser.add_argument("--output-dir", type=Path, default=Path("output/intel_xpu_benchmark"))
    parser.add_argument("--seed", type=int, default=20260722)
    parser.add_argument(
        "--cpu-threads",
        type=int,
        default=0,
        help="Torch CPU thread count; zero keeps the runtime default.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    payload = run(
        arguments.preset,
        arguments.output_dir,
        seed=arguments.seed,
        cpu_threads=arguments.cpu_threads,
    )
    if not all(bool(row["numerically_consistent"]) for row in payload["cases"]):
        print("CPU/XPU numerical consistency check failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
