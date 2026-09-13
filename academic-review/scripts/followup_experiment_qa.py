"""Summarize versioned follow-up campaigns without hard-coding results.

The report reads campaign manifests written by the experiment CLIs. Missing
manifests remain visibly pending; this script never turns a missing run into a
zero or a success.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "academic-review/data/processed/experimental_followup_campaigns.csv"
DEFAULT_REPORT = ROOT / "academic-review/reports/experimental_followup_qa.md"


CAMPAIGNS = (
    {
        "campaign": "SP1_CANONICAL_CONFIRMATORY_v1",
        "config": "experiments/configs/sp1_canonical_confirmatory.yaml",
        "manifest": "results/sp1_canonical/SP1_CANONICAL_CONFIRMATORY_v1/manifest.json",
        "notes": "CPU confirmatory role/coalition formation campaign.",
    },
    {
        "campaign": "SP2_HONORS_v3",
        "config": "experiments/configs/sp2_submit_ready.yaml",
        "manifest": "results/sp2_canonical/SP2_HONORS_v3/manifest.json",
        "notes": "CPU closure campaign covering kinematics, mechanics, networks, and dynamic failures.",
    },
    {
        "campaign": "SP5_PAYLOAD_TRANSPORT_PILOT_v2",
        "config": "experiments/configs/sp5_payload_transport_pilot.yaml",
        "manifest": "results/sp5/SP5_PAYLOAD_TRANSPORT_PILOT_v2/manifest.json",
        "notes": "Pilot required before SP5 confirmatory seed opening.",
    },
    {
        "campaign": "SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2",
        "config": "experiments/configs/sp5_payload_transport_confirmatory.yaml",
        "manifest": "results/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2/manifest.json",
        "notes": "CPU confirmatory reduced-order rigid-payload campaign; requires a PASS pilot audit.",
    },
    {
        "campaign": "SP6_RECOVERY_CONFIRMATORY",
        "config": "experiments/configs/sp6_recovery_confirmatory.yaml",
        "manifest": "results/processed/sp6/SP6_RECOVERY_CONFIRMATORY_v1/manifest.json",
        "notes": "CPU confirmatory recovery campaign; failure and repair outcomes must remain in the denominator.",
    },
    {
        "campaign": "SP7_TRAFFIC_CONFIRMATORY",
        "config": "experiments/configs/sp7_traffic_confirmatory.yaml",
        "manifest": "results/processed/sp7/SP7_TRAFFIC_CONFIRMATORY_v1/manifest.json",
        "notes": "CPU confirmatory multi-coalition traffic campaign.",
    },
    {
        "campaign": "SP8_NETWORK_CONFIRMATORY",
        "config": "experiments/configs/sp8_network_confirmatory.yaml",
        "manifest": "results/processed/sp8/SP8_NETWORK_CONFIRMATORY_v1/manifest.json",
        "notes": "CPU confirmatory communication/network campaign.",
    },
    {
        "campaign": "CARGO_E2E_CONFIRMATORY_v1",
        "config": "experiments/configs/cargo_e2e_confirmatory.yaml",
        "manifest": "results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/manifest.json",
        "notes": "Physical Coppelia confirmatory run is gated by approved preflight evidence and explicit authorization.",
    },
)


FIELDS = [
    "campaign",
    "config",
    "manifest",
    "present",
    "status",
    "audit_status",
    "evidence_level",
    "runs",
    "git_commit",
    "git_dirty",
    "notes",
]


def _first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
        nested = payload.get("metrics")
        if isinstance(nested, dict) and key in nested and nested[key] not in (None, ""):
            return nested[key]
    return ""


def collect() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in CAMPAIGNS:
        manifest_path = ROOT / spec["manifest"]
        record = {
            "campaign": spec["campaign"],
            "config": spec["config"],
            "manifest": spec["manifest"],
            "present": "false",
            "status": "not_run",
            "audit_status": "",
            "evidence_level": "",
            "runs": "",
            "git_commit": "",
            "git_dirty": "",
            "notes": spec["notes"],
        }
        if manifest_path.exists():
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            audit_value = _first(payload, "audit_status", "audit", "theory_audit_status", "theory_audit")
            if not audit_value:
                for candidate_audit in (
                    manifest_path.parent / "audit.json",
                    manifest_path.parent / "audit" / "campaign_audit.json",
                ):
                    if candidate_audit.exists():
                        audit_payload = json.loads(candidate_audit.read_text(encoding="utf-8"))
                        audit_value = _first(audit_payload, "status", "audit_status")
                        break
            if isinstance(audit_value, str) and audit_value.lower().endswith(".json"):
                audit_path = ROOT / audit_value.replace("\\", "/")
                if audit_path.exists():
                    audit_payload = json.loads(audit_path.read_text(encoding="utf-8"))
                    audit_value = _first(audit_payload, "status", "audit_status")
            status_value = _first(payload, "status", "campaign_status")
            if not status_value and str(audit_value).lower() in {"pass", "passed", "complete"}:
                status_value = "complete"
            record.update(
                {
                    "present": "true",
                    "status": str(status_value or "present"),
                    "audit_status": str(audit_value),
                    "evidence_level": str(_first(payload, "evidence_level", "evidence")),
                    "runs": str(_first(payload, "runs", "dynamic_runs", "total_runs")),
                    "git_commit": str(_first(payload, "git_commit", "repository_commit", "git_sha_at_execution")),
                    "git_dirty": str(_first(payload, "git_dirty", "repository_dirty")),
                }
            )
        rows.append(record)
    return rows


def build(csv_path: Path, report_path: Path) -> None:
    rows = collect()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    present = sum(row["present"] == "true" for row in rows)
    lines = [
        "# Follow-up experimental campaign QA",
        "",
        "This report is generated from campaign manifests. A missing manifest is recorded as `not_run`; it is never treated as a zero, a failure, or a success. CPU campaigns remain evidence about the implemented reduced-order protocols, not proof of global stability, optimality, or physical-world robustness.",
        "",
        f"Manifest coverage at generation time: {present}/{len(rows)} campaigns present.",
        "",
        "| Campaign | Present | Status | Audit | Evidence | Runs | Git commit | Dirty |",
        "|---|---:|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['campaign']}` | {row['present']} | {row['status']} | {row['audit_status']} | {row['evidence_level']} | {row['runs']} | `{row['git_commit']}` | {row['git_dirty']} |"
        )
    lines += [
        "",
        "## Gate and interpretation notes",
        "",
        "- SP1 and SP2 are the canonical CPU campaigns and must be read together with their frozen configuration, raw runs, audit, and generated tables.",
        "- SP5 confirmatory execution is valid only after the pilot writes a PASS theory audit and the confirmatory seed-opening event is present.",
        "- CARGO_E2E_CONFIRMATORY is intentionally not inferred from CPU smoke output. Its physical Coppelia run requires preflight evidence and explicit authorization.",
        "- Any campaign with `git_dirty=true` records the repository state at execution time; this reflects the shared worktree and does not mean result rows are invalid, but the exact frozen config and commit must be retained.",
        "- The Web of Science export is an external literature gate, not an experiment; the current session requires institutional authentication and has not been exported.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    build(args.csv.resolve(), args.report.resolve())
    print(f"wrote {args.csv}")
    print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
