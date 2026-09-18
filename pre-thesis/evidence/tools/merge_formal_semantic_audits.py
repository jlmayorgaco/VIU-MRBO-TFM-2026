#!/usr/bin/env python3
"""Merge disjoint formal audits with a single conservative verdict vocabulary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "pre-thesis" / "evidence"
AUDIT_DIR = EVIDENCE_DIR / "integrity" / "formal-audit"
INVENTORY_PATH = EVIDENCE_DIR / "formal-results-audit.csv"
OUTPUT_PATH = AUDIT_DIR / "semantic-all.csv"
SUMMARY_PATH = AUDIT_DIR / "semantic-all-summary.json"
REPORT_PATH = AUDIT_DIR / "semantic-all.md"

BASE_COLUMNS = (
    "source_path",
    "locator",
    "label",
    "type",
    "assumptions",
    "domain",
    "units",
    "proof_status",
    "dependencies",
    "counterexample_check",
    "claim_id",
    "evidence_id",
    "verdict",
    "rationale",
    "auditor",
    "result_id",
    "title",
    "recommended_destination",
)
OUTPUT_COLUMNS = BASE_COLUMNS + (
    "source_audit",
    "source_verdict",
    "normalized_verdict",
    "promotion_decision",
    "normalization_note",
)
NORMALIZATION = {
    "PASS": ("PASS", "identity"),
    "LIMITED": ("LIMITED", "identity"),
    "FAIL": ("FAIL", "identity"),
    "DUPLICATE": ("DUPLICATE", "identity"),
    "CONJECTURE": ("CONJECTURE", "identity"),
    "CANDIDATE": ("LIMITED", "legacy CANDIDATE normalized to LIMITED; no promotion"),
    "REJECT": ("FAIL", "legacy REJECT normalized to FAIL"),
    "NOT_FORMAL": ("FAIL", "legacy NOT_FORMAL normalized to FAIL"),
    "PROMOTE": ("PASS", "legacy PROMOTE normalized to PASS; still requires manual crosswalk"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if path != INVENTORY_PATH and tuple(reader.fieldnames or ()) != BASE_COLUMNS:
            raise ValueError(f"unexpected schema in {path.name}: {reader.fieldnames}")
        return list(reader)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def promotion_decision(row: dict[str, str], normalized: str) -> str:
    claim = row["claim_id"].strip().upper()
    evidence = row["evidence_id"].strip().upper()
    if normalized == "DUPLICATE":
        return "retain-canonical-result-only"
    if normalized == "PASS" and claim not in {"", "NONE", "NONE_IN_DOCS_04"} and not evidence.startswith("SOURCE_"):
        return "eligible-for-manual-crosswalk-not-auto-promoted"
    if normalized == "PASS":
        return "proof-pass-but-claim-or-independent-evidence-unmapped"
    if normalized in {"LIMITED", "CONJECTURE"}:
        return "monograph-candidate-with-explicit-limitation"
    return "reject-as-formal-support"


def audit_files() -> list[Path]:
    return sorted(
        path
        for path in AUDIT_DIR.glob("semantic-*.csv")
        if path.name != OUTPUT_PATH.name
    )


def merge(*, allow_partial: bool) -> tuple[list[dict[str, str]], dict[str, object]]:
    inventory = read_csv(INVENTORY_PATH)
    expected = {row["result_id"]: row for row in inventory}
    if len(expected) != len(inventory):
        raise ValueError("formal inventory contains duplicate result_id values")

    merged: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    files = audit_files()
    if not files:
        raise FileNotFoundError(f"no semantic audit CSV found below {AUDIT_DIR}")
    for path in files:
        for raw in read_csv(path):
            result_id = raw["result_id"].strip()
            if result_id not in expected:
                raise ValueError(f"{path.name}: unknown result_id {result_id}")
            if result_id in seen:
                raise ValueError(f"duplicate result_id {result_id} in {seen[result_id]} and {path.name}")
            if raw["source_path"] != expected[result_id]["path"]:
                raise ValueError(
                    f"{path.name}:{result_id}: source path {raw['source_path']} != {expected[result_id]['path']}"
                )
            missing = [column for column in BASE_COLUMNS if not raw.get(column, "").strip()]
            if missing:
                raise ValueError(f"{path.name}:{result_id}: empty required fields {missing}")
            source_verdict = raw["verdict"].strip().upper()
            if source_verdict not in NORMALIZATION:
                raise ValueError(f"{path.name}:{result_id}: unknown verdict {source_verdict}")
            normalized, note = NORMALIZATION[source_verdict]
            row = dict(raw)
            row.update(
                {
                    "source_audit": path.name,
                    "source_verdict": source_verdict,
                    "normalized_verdict": normalized,
                    "promotion_decision": promotion_decision(raw, normalized),
                    "normalization_note": note,
                }
            )
            merged.append(row)
            seen[result_id] = path.name

    missing_ids = sorted(set(expected) - set(seen))
    if missing_ids and not allow_partial:
        raise ValueError(f"semantic audit is incomplete: {len(missing_ids)} missing IDs")
    for result_id, item in expected.items():
        source = REPO_ROOT / item["path"]
        if not source.is_file() or sha256_file(source) != item["source_sha256"]:
            raise ValueError(f"source hash drift for {result_id}: {item['path']}")

    order = {row["result_id"]: index for index, row in enumerate(inventory)}
    merged.sort(key=lambda row: order[row["result_id"]])
    counts = Counter(row["normalized_verdict"] for row in merged)
    summary: dict[str, object] = {
        "schema_version": 1,
        "complete": not missing_ids and len(merged) == len(inventory),
        "inventory_count": len(inventory),
        "audited_count": len(merged),
        "missing_count": len(missing_ids),
        "missing_result_ids": missing_ids,
        "audit_files": [path.name for path in files],
        "normalized_verdict_counts": dict(sorted(counts.items())),
        "source_verdict_counts": dict(
            sorted(Counter(row["source_verdict"] for row in merged).items())
        ),
        "promotion_decision_counts": dict(
            sorted(Counter(row["promotion_decision"] for row in merged).items())
        ),
        "automatic_promotions": 0,
        "rule": (
            "A semantic PASS is necessary but never sufficient for promotion; an exact "
            "claim/evidence crosswalk and active-source review remain mandatory."
        ),
    }
    return merged, summary


def csv_bytes(rows: Sequence[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})
    return b"\xef\xbb\xbf" + stream.getvalue().encode("utf-8")


def report_text(summary: dict[str, object]) -> str:
    verdicts = summary["normalized_verdict_counts"]
    decisions = summary["promotion_decision_counts"]
    lines = [
        "# Auditoría semántica exhaustiva de resultados formales",
        "",
        f"Cobertura: {summary['audited_count']}/{summary['inventory_count']} resultados; completa: `{str(summary['complete']).lower()}`.",
        "",
        "## Veredictos normalizados",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in verdicts.items())
    lines.extend(["", "## Decisiones de incorporación", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in decisions.items())
    lines.extend(
        [
            "",
            "No se produjo ninguna promoción automática. `PASS` solo cierra la revisión del enunciado y su prueba en la fuente auditada; aún exige correspondencia exacta con un claim, evidencia independiente cuando proceda y revisión de la fuente activa. `LIMITED` y `CONJECTURE` solo pueden conservarse en la monografía con su frontera explícita. `FAIL` no respalda conclusiones y `DUPLICATE` remite al resultado canónico.",
            "",
            "La taxonomía histórica de `semantic-a.csv` se conserva en `source_verdict`; el agregado normaliza `CANDIDATE` a `LIMITED`, y `REJECT`/`NOT_FORMAL` a `FAIL`. Esta normalización no reescribe la auditoría original.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rows, summary = merge(allow_partial=args.allow_partial)
    rendered_csv = csv_bytes(rows)
    rendered_summary = (
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    rendered_report = report_text(summary).encode("utf-8")
    if args.check:
        issues = []
        for path, payload in (
            (OUTPUT_PATH, rendered_csv),
            (SUMMARY_PATH, rendered_summary),
            (REPORT_PATH, rendered_report),
        ):
            if not path.is_file() or path.read_bytes() != payload:
                issues.append(f"missing-or-stale:{path.name}")
        if issues:
            print("FORMAL SEMANTIC MERGE CHECK FAILED")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print(
            "FORMAL SEMANTIC MERGE CHECK PASSED "
            f"audited={summary['audited_count']}/{summary['inventory_count']}"
        )
        return 0
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(rendered_csv)
    SUMMARY_PATH.write_bytes(rendered_summary)
    REPORT_PATH.write_bytes(rendered_report)
    print(
        "FORMAL SEMANTIC MERGE BUILT "
        f"audited={summary['audited_count']}/{summary['inventory_count']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
