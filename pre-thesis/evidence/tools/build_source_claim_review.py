#!/usr/bin/env python3
"""Build the hash-bound source-level claim review for unlinked candidates.

The review closes only the file-level question: none of the selected sources is
linked wholesale to an active claim.  Fragment-level observations, equations,
figures, tables and formal results retain their own audit state.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "pre-thesis" / "evidence"
MANIFEST_PATH = EVIDENCE_DIR / "source-manifest.csv"
CROSSWALK_PATH = EVIDENCE_DIR / "content-crosswalk.csv"
IDEA_PATH = EVIDENCE_DIR / "idea-ledger.csv"
FORMAL_PATH = EVIDENCE_DIR / "formal-results-audit.csv"
WORK_PATH = EVIDENCE_DIR / "work-thematic-crosswalk.csv"
DECISIONS_PATH = EVIDENCE_DIR / "source-claim-review-decisions.json"
OUTPUT_PATH = EVIDENCE_DIR / "source-claim-review.csv"

OUTPUT_COLUMNS = (
    "unit_id",
    "corpus",
    "path",
    "source_sha256",
    "review_category",
    "review_scope",
    "claim_ids",
    "claim_link_status",
    "claim_relation",
    "evidence_locator",
    "heading_count",
    "labeled_unit_count",
    "formal_result_count",
    "formal_verdicts",
    "review_basis",
    "rationale",
    "limitation",
    "reviewed_on",
)

LABELED_KINDS = {
    "latex-observation",
    "latex-figure",
    "latex-table",
    "latex-equation",
}
HEADING_KINDS = {"latex-heading", "pdf-bookmark", "pdf-heading-candidate"}
VERDICT_ORDER = ("PASS", "LIMITED", "FAIL", "DUPLICATE", "CONJECTURE")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def safe_cell(value: object) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.replace("\r", " ").replace("\n", " ").split())
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def render_csv(rows: Iterable[dict[str, object]]) -> bytes:
    import io

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: safe_cell(row.get(column, "")) for column in OUTPUT_COLUMNS})
    return b"\xef\xbb\xbf" + stream.getvalue().encode("utf-8")


def load_decisions() -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    payload = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported source claim review decision schema")
    decisions: dict[str, dict[str, object]] = {}
    for group in payload.get("groups", []):
        for unit_id in group.get("unit_ids", []):
            if unit_id in decisions:
                raise ValueError(f"Duplicate review decision for {unit_id}")
            decisions[unit_id] = group
    return decisions, payload


def target_rows(crosswalk: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        (
            row
            for row in crosswalk
            if row["is_exact_duplicate"] == "no"
            and row["destination"] == "monograph"
            and not row["claim_ids"]
            and (
                row["corpus"] == "work"
                or (row["corpus"] == "paper" and Path(row["path"]).suffix.casefold() == ".tex")
            )
        ),
        key=lambda row: (row["corpus"], row["path"].casefold()),
    )


def build_rows() -> list[dict[str, object]]:
    manifest = {row["unit_id"]: row for row in read_csv(MANIFEST_PATH)}
    targets = target_rows(read_csv(CROSSWALK_PATH))
    decisions, payload = load_decisions()
    target_ids = {row["unit_id"] for row in targets}
    if set(decisions) != target_ids:
        missing = sorted(target_ids - set(decisions))
        extra = sorted(set(decisions) - target_ids)
        raise ValueError(f"Review coverage mismatch: missing={missing}, extra={extra}")

    ideas: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(IDEA_PATH):
        ideas[row["source_unit_id"]].append(row)
    formal_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(FORMAL_PATH):
        formal_by_path[row["path"]].append(row)
    work_audit = {row["unit_id"]: row for row in read_csv(WORK_PATH)}

    rows: list[dict[str, object]] = []
    for target in targets:
        unit_id = target["unit_id"]
        source = manifest[unit_id]
        group = decisions[unit_id]
        source_ideas = ideas[unit_id]
        formal = formal_by_path[target["path"]]
        linked_formal_claims = {
            claim_id
            for result in formal
            for claim_id in result["linked_claim_ids"].split(";")
            if claim_id
        }
        if linked_formal_claims:
            raise ValueError(
                f"Unlinked source contains a formally linked result: {unit_id}:"
                f"{sorted(linked_formal_claims)}"
            )
        verdict_counts = Counter(result["audit_status"] for result in formal)
        formal_verdicts = ";".join(
            f"{verdict}={verdict_counts[verdict]}"
            for verdict in VERDICT_ORDER
            if verdict_counts[verdict]
        )
        rationale = str(group["rationale"])
        limitation = str(group["limitation"])
        if target["corpus"] == "work":
            audited = work_audit[unit_id]
            rationale = f"{rationale} {audited['racional']}"
            limitation = f"{limitation} Evidencia faltante: {audited['evidencia_faltante']}"
            basis = (
                f"pre-thesis/evidence/work-thematic-crosswalk.csv::{unit_id};"
                f"pre-thesis/evidence/idea-ledger.csv::{unit_id}"
            )
        else:
            basis = (
                f"pre-thesis/evidence/formal-results-audit.csv::path={target['path']};"
                f"pre-thesis/evidence/idea-ledger.csv::{unit_id}"
            )
        rows.append(
            {
                "unit_id": unit_id,
                "corpus": target["corpus"],
                "path": target["path"],
                "source_sha256": source["sha256"],
                "review_category": group["id"],
                "review_scope": group["review_scope"],
                "claim_ids": "",
                "claim_link_status": payload["decision"],
                "claim_relation": payload["claim_relation"],
                "evidence_locator": f"pre-thesis/evidence/source-claim-review.csv::{unit_id}",
                "heading_count": sum(item["kind"] in HEADING_KINDS for item in source_ideas),
                "labeled_unit_count": sum(item["kind"] in LABELED_KINDS for item in source_ideas),
                "formal_result_count": len(formal),
                "formal_verdicts": formal_verdicts,
                "review_basis": basis,
                "rationale": rationale,
                "limitation": limitation,
                "reviewed_on": payload["reviewed_on"],
            }
        )
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    output = render_csv(build_rows())
    if args.check:
        if not OUTPUT_PATH.is_file() or OUTPUT_PATH.read_bytes() != output:
            print("SOURCE CLAIM REVIEW CHECK FAILED: source-claim-review.csv is missing or stale")
            return 1
        print("SOURCE CLAIM REVIEW CHECK PASSED rows=41")
        return 0
    OUTPUT_PATH.write_bytes(output)
    print("SOURCE CLAIM REVIEW BUILT rows=41")
    return 0


if __name__ == "__main__":
    sys.exit(main())
