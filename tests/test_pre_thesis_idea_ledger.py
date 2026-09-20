from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "pre-thesis" / "evidence"


def _read_csv(name: str) -> list[dict[str, str]]:
    with (EVIDENCE / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_idea_ledger_is_complete_and_has_stable_unique_ids() -> None:
    rows = _read_csv("idea-ledger.csv")
    summary = json.loads((EVIDENCE / "idea-ledger-summary.json").read_text(encoding="utf-8"))
    assert len(rows) == summary["row_count"]
    assert len({row["idea_id"] for row in rows}) == len(rows)
    assert Counter(row["corpus"] for row in rows) == Counter(summary["by_corpus"])
    assert summary["schema_version"] == 4
    assert all(row["title"] and row["normalized_title"] for row in rows)


def test_every_canonical_book_and_work_pdf_has_a_document_entry() -> None:
    manifest = _read_csv("source-manifest.csv")
    expected = {
        row["unit_id"]
        for row in manifest
        if row["corpus"] in {"books", "work"}
        and row["media_type"] == "application/pdf"
        and row["is_canonical"] == "yes"
    }
    observed = {
        row["source_unit_id"]
        for row in _read_csv("idea-ledger.csv")
        if row["kind"] == "document" and row["corpus"] in {"books", "work"}
    }
    assert observed == expected


def test_formal_results_are_registered_without_automatic_promotion() -> None:
    formal = _read_csv("formal-results-audit.csv")
    rows = [row for row in _read_csv("idea-ledger.csv") if row["kind"] == "formal-result"]
    formal_by_id = {row["result_id"]: row for row in formal}
    assert len(rows) == len(formal)
    assert {
        row["locator"].split(":lines:", 1)[0] for row in rows
    } == {row["result_id"] for row in formal}
    for row in rows:
        result_id = row["locator"].split(":lines:", 1)[0]
        formal_row = formal_by_id[result_id]
        assert row["semantic_review_status"] == f"formal-{formal_row['audit_status'].casefold()}"
        assert row["claim_ids"] == formal_row["linked_claim_ids"]
        assert row["claim_relation"] == (
            "audited-formal-result" if formal_row["linked_claim_ids"] else ""
        )
    assert all("no se promueve" in row["rationale"].casefold() for row in rows)
    assert Counter(row["semantic_review_status"] for row in rows) == Counter(
        f"formal-{row['audit_status'].casefold()}" for row in formal
    )


def test_labeled_latex_units_preserve_exact_formal_context_without_promotion() -> None:
    rows = _read_csv("idea-ledger.csv")
    formal_rows = _read_csv("formal-results-audit.csv")
    formal_by_id = {row["result_id"]: row for row in formal_rows}
    summary = json.loads((EVIDENCE / "idea-ledger-summary.json").read_text(encoding="utf-8"))
    review_payload = json.loads(
        (EVIDENCE / "labeled-unit-review-decisions.json").read_text(encoding="utf-8")
    )
    decisions = {row["idea_id"]: row for row in review_payload["decisions"]}
    labeled_rows = [
        row
        for row in rows
        if row["kind"].startswith("latex-") and ":label:" in row["locator"]
    ]
    labeled = {
        (row["path"], row["kind"], row["locator"].split(":label:", 1)[-1]): row
        for row in labeled_rows
    }
    expected = {
        ("paper/sec_ensayo_cierre_interp.tex", "latex-observation", "obs:ensayo-cierre-tasa"),
        ("paper/sec_ensayo_cierre_figs.tex", "latex-figure", "fig:sim-ref"),
        ("paper/sec_auditoria.tex", "latex-table", "tab:auditoria"),
        ("paper/sec_figuras.tex", "latex-figure", "fig:amr"),
    }
    assert expected <= set(labeled)
    assert len(labeled_rows) == 477
    assert len({(row["path"], row["kind"], row["locator"]) for row in labeled_rows}) == 477
    contextual = [
        row
        for row in labeled_rows
        if row["formal_context_status"] == "within-audited-formal-result"
    ]
    outside = [
        row
        for row in labeled_rows
        if row["formal_context_status"] == "outside-formal-result"
    ]
    assert len(contextual) == summary["labeled_formal_context_count"] == 21
    assert len(outside) == summary["labeled_outside_formal_count"] == 456
    assert Counter(row["formal_context_verdicts"] for row in contextual) == Counter(
        summary["labeled_formal_context_by_verdict"]
    )
    for row in contextual:
        assert row["idea_id"] not in decisions
        assert not row["claim_ids"]
        assert not row["claim_relation"]
        assert row["evidence_status"] == "candidate"
        result_id = row["formal_context_result_ids"]
        formal = formal_by_id[result_id]
        assert row["formal_context_verdicts"] == formal["audit_status"]
        assert set(row["formal_context_claim_ids"].split(";") if row["formal_context_claim_ids"] else []) == set(
            formal["linked_claim_ids"].split(";") if formal["linked_claim_ids"] else []
        )
        assert row["semantic_review_status"] == (
            f"formal-context-{formal['audit_status'].casefold()}"
        )
        assert "no convierte" in row["rationale"].casefold()

    reviewed = [row for row in outside if row["idea_id"] in decisions]
    pending = [row for row in outside if row["idea_id"] not in decisions]
    assert len(reviewed) == summary["labeled_reviewed_count"] == 456
    assert len(pending) == summary["labeled_pending_count"] == 0
    assert {row["idea_id"] for row in reviewed} == set(decisions)
    assert Counter(row["claim_relation"] for row in reviewed) == Counter(
        summary["labeled_reviewed_by_relation"]
    )
    assert Counter(row["semantic_review_status"] for row in reviewed) == Counter(
        summary["labeled_reviewed_by_status"]
    )
    for row in reviewed:
        decision = decisions[row["idea_id"]]
        assert row["path"] == decision["path"]
        assert row["locator"] == decision["locator"]
        assert row["claim_ids"] == ";".join(sorted(set(decision["claim_ids"])))
        for key in (
            "claim_relation",
            "evidence_status",
            "destination",
            "incorporation_mode",
            "semantic_review_status",
            "rationale",
        ):
            assert row[key] == decision[key]
    for row in pending:
        assert not row["claim_ids"]
        assert not row["claim_relation"]
        assert row["evidence_status"] == "candidate"
        assert not row["formal_context_result_ids"]
        assert not row["formal_context_verdicts"]
        assert not row["formal_context_claim_ids"]
        assert row["semantic_review_status"] == "pending-semantic-review"
        assert any(
            token in row["rationale"].casefold()
            for token in (
                "no constituye",
                "requiere contraste",
                "requiere verificar",
                "no valida",
            )
        )

    thesis_labeled = [row for row in labeled_rows if row["corpus"] == "thesis"]
    assert len(thesis_labeled) == 140
    assert not [
        row
        for row in thesis_labeled
        if row["semantic_review_status"] == "pending-semantic-review"
    ]
    assert Counter(row["destination"] for row in thesis_labeled) == {
        "thesis-body": 72,
        "monograph": 48,
        "archive-only": 20,
    }


def test_labeled_unit_review_is_hash_bound_and_keeps_roles_distinct() -> None:
    payload = json.loads(
        (EVIDENCE / "labeled-unit-review-decisions.json").read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == 1
    assert len(payload["decisions"]) == 456
    bindings = {row["path"]: row for row in payload["source_bindings"]}
    assert len(bindings) == 47
    for path, binding in bindings.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == binding["source_sha256"]
    relations = Counter(row["claim_relation"] for row in payload["decisions"])
    assert relations == {
        "defines": 116,
        "limits": 123,
        "contextualizes": 169,
        "specifies-protocol": 12,
        "reports-evidence": 36,
    }
    evidence_rows = [
        row for row in payload["decisions"] if row["claim_relation"] == "reports-evidence"
    ]
    assert len(evidence_rows) == 36
    assert Counter(row["evidence_status"] for row in evidence_rows) == {
        "evidence-summary": 12,
        "exploratory-evidence-summary": 7,
        "exploratory-negative-evidence": 2,
        "suppressed-evidence-summary": 5,
        "unbound-historical-software-tests": 1,
        "untraceable-complete-mission-runs": 1,
        "untraceable-footprint-clearance-study": 1,
        "untraceable-mixed-contact-plant-campaign": 1,
        "untraceable-multicampaign-planning-results": 1,
        "untraceable-negotiated-crossing-run": 1,
        "untraceable-pairwise-fiber-fragmentation-study": 1,
        "untraceable-r11-joint-revision-benchmark": 1,
        "untraceable-reduced-trajectory-run": 1,
        "untraceable-seven-method-benchmark": 1,
    }
    assert sum(row["destination"] == "archive-only" for row in evidence_rows) == 15
    assert sum(row["destination"] == "monograph" for row in evidence_rows) == 13
    assert sum(row["destination"] == "thesis-body" for row in evidence_rows) == 8
