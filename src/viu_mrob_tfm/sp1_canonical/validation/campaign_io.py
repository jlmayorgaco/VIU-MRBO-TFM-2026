"""Shared reproducibility helpers for the V1.1/V2 SP1 campaigns."""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml


def deep_merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if (
            key in result
            and isinstance(result[key], Mapping)
            and isinstance(value, Mapping)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_resolved_config(repo: Path, config_path: Path) -> dict[str, Any]:
    overlay = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    base_reference = overlay.get("base_config")
    if base_reference is None:
        return overlay
    base_path = repo / str(base_reference)
    base = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    return deep_merge(base, overlay)


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=json_default,
        )
        + "\n",
        encoding="utf-8",
    )


def write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def write_shard(path: Path, payload: Any) -> None:
    """Atomically replace one JSON checkpoint shard."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary)
    try:
        temporary_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                default=json_default,
            ),
            encoding="utf-8",
        )
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_pandas_csv_from_parquet(path: Path) -> str:
    frame = pd.read_parquet(path)
    buffer = io.StringIO(newline="")
    frame.to_csv(buffer, index=False)
    return hashlib.sha256(buffer.getvalue().encode("utf-8")).hexdigest()


def verify_checksum_ledger(root: Path, ledger_path: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(maxsplit=1)
        target = root / relative
        reconstructed = False
        if target.exists():
            observed = sha256_file(target)
        elif relative in {"all_messages.csv", "all_traces.csv"}:
            parquet = root / relative.replace(".csv", ".parquet")
            observed = (
                sha256_pandas_csv_from_parquet(parquet)
                if parquet.exists()
                else ""
            )
            reconstructed = parquet.exists()
        else:
            observed = ""
        rows.append(
            {
                "file": relative,
                "expected_sha256": expected,
                "observed_sha256": observed,
                "exists": target.exists(),
                "reconstructed_from_parquet": reconstructed,
                "valid": observed == expected,
            }
        )
    return pd.DataFrame(rows)


def write_checksums(
    output_dir: Path,
    *,
    filename: str = "checksums.sha256",
    exclude: set[str] | None = None,
) -> None:
    excluded = {filename} | (exclude or set())
    lines = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output_dir).as_posix()
        if relative in excluded or relative.startswith("checkpoints/"):
            continue
        lines.append(f"{sha256_file(path)}  {relative}")
    (output_dir / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_metadata(repo: Path) -> dict[str, Any]:
    def call(*arguments: str) -> str:
        return subprocess.check_output(
            ["git", *arguments],
            cwd=repo,
            text=True,
            encoding="utf-8",
        ).strip()

    return {
        "commit": call("rev-parse", "HEAD"),
        "branch": call("branch", "--show-current"),
        "status_porcelain": call("status", "--porcelain"),
    }


def git_path_matches_commit(repo: Path, commit: str, path: Path) -> bool:
    relative = path.resolve().relative_to(repo.resolve()).as_posix()
    result = subprocess.run(
        ["git", "diff", "--quiet", commit, "--", relative],
        cwd=repo,
        check=False,
    )
    return result.returncode == 0


def parse_junit(path: Path) -> dict[str, int | bool]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    tests = sum(int(suite.attrib.get("tests", 0)) for suite in suites)
    failures = sum(int(suite.attrib.get("failures", 0)) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", 0)) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", 0)) for suite in suites)
    return {
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "passed": failures == 0 and errors == 0,
    }


def write_parquet_or_empty(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if frame.shape[1] == 0:
        frame = pd.DataFrame({"empty": pd.Series(dtype="bool")})
    frame.to_parquet(path, index=False)
