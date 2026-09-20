from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "pre-thesis" / "evidence"
AUDIT = EVIDENCE / "integrity" / "formal-audit"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_semantic_audit_covers_the_entire_formal_inventory_once() -> None:
    inventory = _read_csv(EVIDENCE / "formal-results-audit.csv")
    semantic = _read_csv(AUDIT / "semantic-all.csv")
    summary = json.loads((AUDIT / "semantic-all-summary.json").read_text(encoding="utf-8"))
    snapshot = json.loads(
        (EVIDENCE / "source-snapshot.json").read_text(encoding="utf-8")
    )

    expected_ids = [row["result_id"] for row in inventory]
    observed_ids = [row["result_id"] for row in semantic]
    assert summary["complete"] is True
    assert summary["missing_count"] == 0
    assert len(semantic) == len(inventory) == summary["inventory_count"]
    assert observed_ids == expected_ids
    assert len(observed_ids) == len(set(observed_ids))

    semantic_by_id = {row["result_id"]: row for row in semantic}
    audited_columns = (
        "assumptions_audited",
        "domain_audited",
        "units_audited",
        "proof_audited",
        "dependencies_audited",
        "counterexample_audited",
        "evidence_link_audited",
    )
    excluded_claim_markers = {"", "NONE", "NONE_IN_DOCS_04"}
    for row in inventory:
        semantic_row = semantic_by_id[row["result_id"]]
        assert row["audit_status"] == semantic_row["normalized_verdict"]
        assert all(row[column] == "yes" for column in audited_columns)
        expected_claim_ids = sorted(
            claim_id.strip()
            for claim_id in semantic_row["claim_id"].split(";")
            if claim_id.strip() not in excluded_claim_markers
        )
        observed_claim_ids = (
            row["linked_claim_ids"].split(";") if row["linked_claim_ids"] else []
        )
        assert observed_claim_ids == expected_claim_ids

    assert all(row["audit_status"] != "pending-audit" for row in inventory)
    assert snapshot["validations"]["formal_semantic_audit_complete"] is True
    assert Counter(row["audit_status"] for row in inventory) == Counter(
        snapshot["formal_result_counts"]["audit_status_counts"]
    )
    assert snapshot["formal_result_counts"]["semantic_audit_source"] == (
        "pre-thesis/evidence/integrity/formal-audit/semantic-all.csv"
    )


def test_verdicts_are_conservative_and_never_auto_promote() -> None:
    rows = _read_csv(AUDIT / "semantic-all.csv")
    summary = json.loads((AUDIT / "semantic-all-summary.json").read_text(encoding="utf-8"))
    allowed = {"PASS", "LIMITED", "FAIL", "DUPLICATE", "CONJECTURE"}

    assert {row["normalized_verdict"] for row in rows} <= allowed
    assert summary["automatic_promotions"] == 0
    assert Counter(row["normalized_verdict"] for row in rows) == Counter(
        summary["normalized_verdict_counts"]
    )
    assert all(
        row["promotion_decision"] != "auto-promote" for row in rows
    )


def test_formal_audit_and_monograph_atlas_are_reproducible() -> None:
    scripts = (
        EVIDENCE / "tools" / "merge_formal_semantic_audits.py",
        EVIDENCE / "tools" / "build_formal_candidate_atlas.py",
    )
    for script in scripts:
        subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=ROOT,
            check=True,
        )

    atlas = ROOT / "pre-thesis" / "monograph" / "sections" / "formal-candidate-atlas.tex"
    text = atlas.read_text(encoding="utf-8")
    assert r"\input{monograph/sections/formal-candidate-atlas}" in (
        ROOT / "pre-thesis" / "monograph" / "main.tex"
    ).read_text(encoding="utf-8")
    assert text.count("PAPER-FR-") + text.count("THESIS-FR-") == len(
        _read_csv(AUDIT / "semantic-all.csv")
    )
