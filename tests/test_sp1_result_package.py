from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from viu_mrob_tfm.sp1_canonical.validation.result_package import (
    build_sp1_result_package,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_complete_sp1_package_verifies_and_indexes_children(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    conference = tmp_path / "conference"
    videos = conference / "videos"
    for directory in (canonical / "tables", conference / "raw", videos):
        directory.mkdir(parents=True, exist_ok=True)

    canonical_artifact = canonical / "report.md"
    canonical_artifact.write_text("canonical", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "method": "local_gossip__nominal",
                "n": 2,
                "started_loads_mean": 1.0,
                "started_loads_ci_low": 0.8,
                "started_loads_ci_high": 1.2,
                "social_value_mean": 2.0,
                "social_value_ci_low": 1.5,
                "social_value_ci_high": 2.5,
                "optimality_gap_mean": 0.2,
                "optimality_gap_ci_low": 0.1,
                "optimality_gap_ci_high": 0.3,
                "messages_mean": 10.0,
                "messages_ci_low": 8.0,
                "messages_ci_high": 12.0,
            }
        ]
    ).to_csv(canonical / "tables" / "sp1_canonical_summary.csv", index=False)
    (canonical / "manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": "CANONICAL_TEST",
                "audit_status": "passed",
                "evidence_level": "C-pilot",
                "worlds": 2,
                "runs": 2,
                "artifact_sha256": {"report.md": _sha256(canonical_artifact)},
            }
        ),
        encoding="utf-8",
    )

    conference_artifact = conference / "report.md"
    conference_artifact.write_text("conference", encoding="utf-8")
    pd.DataFrame(
        [{"method": "Rep-C", "converged": True, "comparable_to_lp": True}]
    ).to_csv(conference / "raw" / "e1_runs.csv", index=False)
    pd.DataFrame(
        [
            {
                "method": "Argmax+repair+prune+local-exchange",
                "feasible": True,
                "integer_gap_milp": 0.0,
            }
        ]
    ).to_csv(conference / "raw" / "e4_runs.csv", index=False)
    pd.DataFrame(
        [{"method": "Auction-D", "feasible": True}, {"method": "Rep-D+recovery", "feasible": True}]
    ).to_csv(conference / "raw" / "e5_runs.csv", index=False)
    pd.DataFrame(
        [
            {
                "scenario": "open",
                "assignment_feasible": True,
                "arrival_rate": 1.0,
                "assignment_json": "[0]",
                "n_robots": 1,
                "n_loads": 1,
                "seed": 1,
            }
        ]
    ).to_csv(conference / "raw" / "e6_runs.csv", index=False)
    conference_manifest_path = conference / "manifest.json"
    conference_manifest_path.write_text(
        json.dumps(
            {
                "experiment_id": "CONFERENCE_TEST",
                "audit_status": "passed",
                "scientific_status": "partial",
                "artifact_sha256": {"report.md": _sha256(conference_artifact)},
            }
        ),
        encoding="utf-8",
    )
    (conference / "audit.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "checks": {"integrity": True},
                "gates": {"science": False},
                "failed_gates": ["science"],
            }
        ),
        encoding="utf-8",
    )
    clip = videos / "clip.mp4"
    clip.write_bytes(b"fake-mp4-for-hash-test")
    pd.DataFrame([{"video": "videos/clip.mp4"}]).to_csv(videos / "video_catalog.csv", index=False)
    (videos / "VIDEO_INDEX.md").write_text("index", encoding="utf-8")
    (videos / "manifest.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "video_count": 1,
                "videos": [
                    {
                        "video": "videos/clip.mp4",
                        "sha256": _sha256(clip),
                        "scenario": "open",
                        "n_robots": 1,
                        "seed": 1,
                        "frame_count": 1,
                        "retained_obstacles": 0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    output = tmp_path / "package"
    manifest = build_sp1_result_package(canonical, conference, output)
    assert manifest["status"] == "passed"
    assert manifest["scientific_status"] == "partial"
    assert manifest["conference"]["failed_gates"] == ["science"]
    assert manifest["videos"]["count"] == 1
    assert manifest["artifact_count"] >= 8
    assert {"README.md", "artifact_index.csv", "key_statistics.csv", "manifest.json"} <= {
        path.name for path in output.iterdir()
    }
    artifact_index = pd.read_csv(output / "artifact_index.csv")
    assert artifact_index.verification.eq("passed").all()
