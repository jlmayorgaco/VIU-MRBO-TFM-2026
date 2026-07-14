"""Preflight audit for the submit-ready TFM freeze."""

from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from tfm_submit_utils import (
    CANONICAL_SPS,
    DOCS_GENERATED,
    ROOT,
    audit_file,
    canonical_file,
    ensure_dir,
    failed_checks_from_audit,
)


REQUIRED_SCRIPTS = [
    "scripts/preflight_repo_audit.py",
    "scripts/generate_method_matrix.py",
    "scripts/generate_regime_map.py",
    "scripts/build_stats_annex.py",
    "scripts/check_claims.py",
    "scripts/validate_theory_vgne_share.py",
    "scripts/validate_theory_poa.py",
    "scripts/validate_theory_stability.py",
    "scripts/build_theory_validation_report.py",
    "scripts/run_sp9_experiment.py",
]


def run_text(args: list[str], timeout_s: int = 20) -> str:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_s,
            check=False,
        )
        return completed.stdout.strip()
    except Exception as exc:  # pragma: no cover - defensive audit code
        return f"ERROR: {exc}"


def stable_pytest_collect_tail(collect_output: str) -> str:
    tail = "\n".join(collect_output.splitlines()[-5:])
    return re.sub(r"(\d+\s+tests collected) in [0-9.]+s", r"\1 in <duration>", tail)


def parse_make_targets() -> list[str]:
    makefile = ROOT / "Makefile"
    if not makefile.exists():
        return []
    targets: list[str] = []
    for line in makefile.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("\t") or line.startswith(".") or ":=" in line or "?=" in line:
            continue
        if ":" in line:
            target = line.split(":", 1)[0].strip()
            if target and " " not in target:
                targets.append(target)
    return sorted(set(targets))


def grep_imports(pattern: str) -> list[str]:
    matches: list[str] = []
    for root_name in ("src", "scripts", "tests"):
        base = ROOT / root_name
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if pattern in text:
                matches.append(str(path.relative_to(ROOT)))
    return matches


def canonical_status() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sp, meta in CANONICAL_SPS.items():
        result_dir = ROOT / meta.result_dir
        config_exists = (ROOT / meta.config).exists()
        result_dir_exists = result_dir.exists()
        report_exists = (result_dir / "report.md").exists()
        runs_exists = canonical_file(sp, "runs.csv").exists()
        summary_exists = canonical_file(sp, "summary.csv").exists()
        failed_checks = failed_checks_from_audit(audit_file(sp))
        rows.append(
            {
                "sp": sp,
                "title": meta.title,
                "config": str(meta.config),
                "config_exists": config_exists,
                "result_dir": str(meta.result_dir),
                "result_dir_exists": result_dir_exists,
                "report_exists": report_exists,
                "runs_exists": runs_exists,
                "summary_exists": summary_exists,
                "ranking_exists": canonical_file(sp, "performance_ranking.csv").exists(),
                "hypothesis_exists": canonical_file(sp, "hypothesis_results.csv").exists(),
                "theory_audit": str(audit_file(sp).relative_to(ROOT)),
                "failed_checks": failed_checks,
                "core_artifacts_complete": bool(
                    config_exists
                    and result_dir_exists
                    and report_exists
                    and runs_exists
                    and summary_exists
                    and failed_checks == 0
                ),
            }
        )
    return rows


def main() -> int:
    ensure_dir(DOCS_GENERATED)
    current_branch = run_text(["git", "branch", "--show-current"])
    status_short = run_text(["git", "status", "--short"], timeout_s=60)
    collect_only = run_text([sys.executable, "-m", "pytest", "--collect-only", "-q"], timeout_s=120)
    coppelia_candidates = ["coppeliaSim", "CoppeliaSim", "coppeliaSim.exe", "CoppeliaSim.exe"]
    coppelia_found = [cmd for cmd in coppelia_candidates if shutil.which(cmd)]

    audit = {
        "python": sys.version,
        "platform": platform.platform(),
        "branch": current_branch,
        "dirty_entry_count": len([line for line in status_short.splitlines() if line.strip()]),
        "make_targets": parse_make_targets(),
        "required_scripts": {item: (ROOT / item).exists() for item in REQUIRED_SCRIPTS},
        "canonical_status": canonical_status(),
        "imports": {
            "viu_mrob_tfm.simulation": grep_imports("viu_mrob_tfm.simulation"),
            "viu_mrob_tfm.controllers": grep_imports("viu_mrob_tfm.controllers"),
        },
        "coppeliasim_in_path": coppelia_found,
        "pytest_collect_only_tail": stable_pytest_collect_tail(collect_only),
    }

    json_path = DOCS_GENERATED / "preflight_repo_audit.json"
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Preflight Repo Audit",
        "",
        f"- Branch: `{current_branch}`",
        f"- Python: `{platform.python_version()}`",
        f"- Dirty entries: `{audit['dirty_entry_count']}`",
        f"- CoppeliaSim in PATH: `{', '.join(coppelia_found) if coppelia_found else 'not found'}`",
        "",
        "## Canonical SP Status",
        "",
        "| SP | Result dir | Core artifacts | Separate ranking (optional) | Hypotheses | Audit failed checks |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in audit["canonical_status"]:
        lines.append(
            "| {sp} | `{result_dir}` | {core_artifacts_complete} | {ranking_exists} | {hypothesis_exists} | {failed_checks} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Import Decision",
            "",
            "`src/viu_mrob_tfm/simulation` and `src/viu_mrob_tfm/controllers` remain live because current tests/scripts import them.",
            "",
            "## Required Script Presence",
            "",
            "| Script | Exists |",
            "|---|---:|",
        ]
    )
    for path, exists in audit["required_scripts"].items():
        lines.append(f"| `{path}` | {exists} |")
    lines.extend(["", "## Pytest Collect", "", "```text", audit["pytest_collect_only_tail"], "```", ""])
    (DOCS_GENERATED / "preflight_repo_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {json_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
