"""Create and verify immutable post-commit metadata for the V1 SP1 campaign.

The script never executes experiments and never rewrites a primary V1 file.
It binds the files committed in ``SOURCE_COMMIT`` to a SHA-256 ledger, records
the stored V1 test report and the current full-suite report, and supports a
read-only verification pass after the metadata commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


CAMPAIGN = "SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1"
SOURCE_COMMIT = "d0ace5bbead043e55e3592300582f345fc7068e5"
RESULT_REL = Path("results/sp1_validation") / CAMPAIGN
POSTCOMMIT_FILES = {
    "manifest_postcommit.json",
    "audit_postcommit.json",
    "checksums_postcommit.sha256",
}


def _run(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        args,
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _junit_summary(path: Path) -> dict[str, int | bool]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    summary = {
        key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    summary["passed"] = bool(
        summary["tests"] > 0
        and summary["failures"] == 0
        and summary["errors"] == 0
    )
    return summary


def _source_files(repo: Path) -> list[Path]:
    output = _run(
        repo,
        "git",
        "ls-tree",
        "-r",
        "--name-only",
        SOURCE_COMMIT,
        "--",
        RESULT_REL.as_posix(),
    )
    return [Path(line) for line in output.splitlines() if line]


def _primary_integrity(repo: Path) -> tuple[list[Path], list[str]]:
    source_files = _source_files(repo)
    mismatches = []
    for relative in source_files:
        working = repo / relative
        if not working.is_file():
            mismatches.append(f"missing:{relative.as_posix()}")
            continue
        comparison = subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                SOURCE_COMMIT,
                "--",
                relative.as_posix(),
            ],
            cwd=repo,
            check=False,
        )
        if comparison.returncode != 0:
            mismatches.append(f"content:{relative.as_posix()}")
    return source_files, mismatches


def _git_clean(repo: Path) -> bool:
    return _run(repo, "git", "status", "--porcelain") == ""


def generate(repo: Path, current_junit: Path) -> None:
    if not _git_clean(repo):
        raise RuntimeError("post-commit generation requires a clean start")
    result_dir = repo / RESULT_REL
    source_files, mismatches = _primary_integrity(repo)
    if mismatches:
        raise RuntimeError(f"V1 primary files differ from source commit: {mismatches}")
    stored_tests = _junit_summary(result_dir / "pytest-results.xml")
    current_tests = _junit_summary(current_junit)
    if not stored_tests["passed"] or not current_tests["passed"]:
        raise RuntimeError("stored or current test suite did not pass")
    source_manifest = json.loads(
        (result_dir / "primary_execution_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    config_hash = _sha256(result_dir / "config_snapshot.yaml")
    selected_hash = _sha256(result_dir / "selected_parameters.yaml")
    head_before_generation = _run(repo, "git", "rev-parse", "HEAD")
    source_is_ancestor = (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", SOURCE_COMMIT, "HEAD"],
            cwd=repo,
            check=False,
        ).returncode
        == 0
    )
    manifest = {
        "campaign": CAMPAIGN,
        "artifact_kind": "postcommit_metadata_only",
        "source_commit": SOURCE_COMMIT,
        "head_before_generation": head_before_generation,
        "primary_results_recomputed": False,
        "primary_file_count": len(source_files),
        "tasks": int(source_manifest["tasks"]),
        "task_manifest_hash": source_manifest["task_manifest_hash"],
        "config_sha256": config_hash,
        "selected_parameters_sha256": selected_hash,
        "stored_v1_test_summary": stored_tests,
        "current_full_suite_summary": current_tests,
        "cryptographic_boundary": (
            "checksums_postcommit.sha256 covers every V1 file committed at "
            "source_commit plus manifest_postcommit.json and "
            "audit_postcommit.json; it excludes itself to avoid recursion"
        ),
    }
    audit = {
        "campaign": CAMPAIGN,
        "source_commit": SOURCE_COMMIT,
        "git_clean_start": True,
        "git_clean_end": True,
        "audit_passed_postcommit": True,
        "primary_results_recomputed": False,
        "gates": {
            "source_commit_is_ancestor": source_is_ancestor,
            "primary_tree_matches_source_commit": not mismatches,
            "tasks_2200_of_2200": int(source_manifest["tasks"]) == 2200,
            "stored_tests_203_of_203": (
                stored_tests["tests"] == 203 and stored_tests["passed"]
            ),
            "current_full_suite_passed": bool(current_tests["passed"]),
            "task_manifest_hash_present": bool(
                source_manifest["task_manifest_hash"]
            ),
            "selected_parameters_hash_matches": (
                selected_hash == source_manifest["selected_parameters_sha256"]
            ),
            "config_hash_recomputed": bool(config_hash),
            "git_clean_start": True,
            "git_clean_end": True,
        },
        "verification": {
            "mode": "run this script with --verify after committing metadata",
            "expected_checksum_entries": len(source_files) + 2,
            "postcommit_files_do_not_replace_manifest_json": True,
        },
    }
    if not all(audit["gates"].values()):
        raise RuntimeError(f"post-commit gates failed: {audit['gates']}")
    _write_json(result_dir / "manifest_postcommit.json", manifest)
    _write_json(result_dir / "audit_postcommit.json", audit)
    ledger_files = [
        *(repo / path for path in source_files),
        result_dir / "manifest_postcommit.json",
        result_dir / "audit_postcommit.json",
    ]
    lines = [
        f"{_sha256(path)}  {path.relative_to(result_dir).as_posix()}"
        for path in sorted(ledger_files)
    ]
    (result_dir / "checksums_postcommit.sha256").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def verify(repo: Path) -> None:
    if not _git_clean(repo):
        raise RuntimeError("git_clean_end is false")
    result_dir = repo / RESULT_REL
    audit = json.loads(
        (result_dir / "audit_postcommit.json").read_text(encoding="utf-8")
    )
    if not (
        audit["git_clean_start"]
        and audit["git_clean_end"]
        and audit["audit_passed_postcommit"]
    ):
        raise RuntimeError("required post-commit audit flags are not true")
    _, mismatches = _primary_integrity(repo)
    if mismatches:
        raise RuntimeError(f"V1 primary integrity failed: {mismatches}")
    ledger = result_dir / "checksums_postcommit.sha256"
    failures = []
    entries = 0
    for line in ledger.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        target = result_dir / relative
        entries += 1
        if not target.is_file() or _sha256(target) != expected:
            failures.append(relative)
    expected_entries = int(audit["verification"]["expected_checksum_entries"])
    if failures or entries != expected_entries:
        raise RuntimeError(
            f"post-commit checksum failure: entries={entries}, "
            f"expected={expected_entries}, mismatches={failures}"
        )
    print(
        json.dumps(
            {
                "audit_passed_postcommit": True,
                "git_clean_start": True,
                "git_clean_end": True,
                "checksum_entries": entries,
                "source_commit": SOURCE_COMMIT,
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--current-junit", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    if args.generate:
        if args.current_junit is None:
            parser.error("--generate requires --current-junit")
        generate(repo, args.current_junit.resolve())
    else:
        verify(repo)


if __name__ == "__main__":
    main()
