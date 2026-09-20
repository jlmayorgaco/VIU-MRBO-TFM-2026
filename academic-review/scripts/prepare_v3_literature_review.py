"""Prepare the auditable V3 literature-review workspace.

V3 is intentionally a derivative of the earlier exploratory campaigns.  This
script never rewrites their corpus or promotes structural coding to scientific
evidence.  It creates (1) a query ledger, (2) a seed registry, and (3) a
prioritized close-reading queue for already identity-verified full text.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


BASE = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = BASE / "literature-review-v3"
MATRIX = BASE / "data" / "processed" / "fulltext_evidence_matrix.csv"
CORPUS = BASE / "data" / "processed" / "candidate_corpus_stage2.csv"
WOS_MANIFEST = BASE / "inputs" / "wos" / "wos_export_manifest.json"
WOS_PACK = BASE / "multisource-v2" / "manual-packs" / "web_of_science_query_pack.csv"

FULLTEXT = "fulltext_verified"
FIELD_NAMES = [
    "problem_formulation",
    "coordination_architecture",
    "information_assumptions",
    "method",
    "physical_layer",
    "execution",
    "theory",
    "experiments",
    "results",
    "limitations",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", clean(value).lower()).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def source_text(row: dict[str, Any], abstract: str = "") -> str:
    """Return metadata-only routing text, deliberately excluding extracted spans.

    The Stage 3 structural pass may match a phrase in a reference list.  That is
    useful for retrieval but must not inflate the priority or SP routing of a
    paper that does not itself make the claim.
    """
    return " ".join([normalise(row.get("title")), normalise(abstract)])


def derive_targets(row: dict[str, Any], abstract: str = "") -> list[str]:
    """Assign review targets for routing, never as a scientific claim."""
    text = source_text(row, abstract)
    targets: list[str] = []
    if any(term in text for term in ["task allocation", "task assignment", "coalition", "team formation", "auction", "market based", "potential game", "replicator", "heterogeneous"]):
        targets.append("SP1")
    if any(term in text for term in ["cooperative transport", "object transport", "payload", "load", "wrench", "force closure", "contact", "caging", "docking", "formation control", "manipulation"]):
        targets.append("SP2")
    if any(term in text for term in ["path planning", "motion planning", "navigation", "traffic", "congestion", "warehouse", "collision avoidance", "orca", "rvo", "reservation"]):
        targets.append("SP3")
    if any(term in text for term in ["fault", "failure", "replacement", "recovery", "packet loss", "time delay", "communication", "network"]):
        targets.append("TRANSVERSAL")
    return targets or ["CONTEXT"]


def priority_score(row: dict[str, Any], targets: list[str], abstract: str = "") -> int:
    role_weight = {"CORE": 55, "SURVEY": 50, "BASELINE": 45, "ENABLING": 30, "FOUNDATIONAL": 25, "CONTEXT": 10}
    score = role_weight.get(clean(row.get("scientific_role")), 0)
    score += 6 * len([target for target in targets if target.startswith("SP")])
    score += 4 if "TRANSVERSAL" in targets else 0
    title = normalise(row.get("title"))
    metadata = source_text(row, abstract)
    score += 15 if any(term in title for term in ["survey", "review", "taxonomy"]) else 0
    score += 10 if any(term in title for term in ["coalition", "cooperative transport", "payload", "object transport"]) else 0
    score += 5 if "heterogeneous" in metadata else 0
    score += 3 if clean(row.get("doi")) else 0
    return score


def priority_tier(score: int) -> str:
    if score >= 65:
        return "P0"
    if score >= 60:
        return "P1"
    if score >= 40:
        return "P2"
    return "P3"


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {clean(item.get("query_id")): item for item in data.get("exports", [])}


def query_ledger_rows(pack_rows: list[dict[str, str]], exports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for query in pack_rows:
        execution_id = clean(query.get("execution_id"))
        export = exports.get(execution_id, {})
        rows.append(
            {
                "review_version": "V3",
                "source": clean(query.get("database")),
                "execution_id": execution_id,
                "query_id": clean(query.get("query_id")),
                "window_id": clean(query.get("window_id")),
                "exact_query": clean(query.get("exact_query")),
                "from_year": clean(query.get("from_year")),
                "to_year": clean(query.get("to_year")),
                "field_scope": clean(query.get("field_scope")),
                "export_format": clean(query.get("export_format")),
                "historical_status": clean(export.get("status")) or "not_reconciled_in_v3",
                "historical_expected_records": clean(export.get("expected_records")),
                "historical_observed_records": clean(export.get("observed_records")),
                "historical_raw_file": clean(export.get("file")),
                "historical_sha256": clean(export.get("sha256")),
                "v3_execution_status": "not_queried",
                "v3_notes": "A V3 query must be logged separately; historical exports remain provenance only.",
            }
        )
    return rows


def seed_rows(corpus_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    fields = [
        "candidate_id", "title", "authors", "year", "venue", "doi_norm", "document_type",
        "provenance", "provenance_sources", "provenance_queries", "screening_decision",
        "fulltext_status", "fulltext_identity_status", "evidence_status", "wos_ut",
    ]
    rows: list[dict[str, Any]] = []
    for record in corpus_rows:
        item = {field.replace("doi_norm", "doi"): clean(record.get(field)) for field in fields}
        item["seed_role"] = "exploratory_prior_campaign"
        item["v3_screening_status"] = "not_screened"
        item["v3_allowed_use"] = "discovery_only_until_v3_review"
        rows.append(item)
    return rows


def reading_rows(matrix_rows: list[dict[str, str]], corpus_by_id: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in matrix_rows:
        if clean(record.get("evidence_strength")) != FULLTEXT:
            continue
        discovery = corpus_by_id.get(clean(record.get("candidate_id")), {})
        abstract = clean(discovery.get("abstract"))
        routing_basis = "title_abstract_metadata" if abstract else "title_metadata"
        targets = derive_targets(record, abstract)
        score = priority_score(record, targets, abstract)
        row = {
            "candidate_id": clean(record.get("candidate_id")),
            "title": clean(record.get("title")),
            "authors": clean(record.get("authors")),
            "year": clean(record.get("year")),
            "venue": clean(record.get("venue")),
            "doi": clean(record.get("doi")),
            "document_type": clean(record.get("document_type")),
            "scientific_role_structural": clean(record.get("scientific_role")),
            "review_targets_routing_only": ";".join(targets),
            "routing_basis": routing_basis,
            "priority_score": score,
            "priority_tier": priority_tier(score),
            "fulltext_local_path": clean(record.get("fulltext_local_path")),
            "fulltext_sha256": clean(record.get("fulltext_sha256")),
            "structural_evidence_spans_json": clean(record.get("evidence_spans_json")),
            "v3_review_state": "not_started",
            "v3_evidence_status": "requires_close_reading",
            "v3_allowed_use": "not_a_claim_until_passage_is_verified",
            "reviewer": "",
            "reviewed_at_utc": "",
            "claim_localizers": "",
            "notes": "",
        }
        rows.append(row)
    return sorted(rows, key=lambda row: (-int(row["priority_score"]), row["year"], row["candidate_id"]))


def card_rows(reading_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in reading_queue:
        cards.append(
            {
                "candidate_id": row["candidate_id"],
                "citation": {key: row[key] for key in ["title", "authors", "year", "venue", "doi"]},
                "routing": {key: row[key] for key in ["scientific_role_structural", "review_targets_routing_only", "priority_score", "priority_tier"]},
                "fulltext": {key: row[key] for key in ["fulltext_local_path", "fulltext_sha256"]},
                "structural_evidence_spans_json": row["structural_evidence_spans_json"],
                "review_template": {
                    "problem_scope": "",
                    "robot_load_contact_model": "",
                    "information_and_architecture": "",
                    "method_and_parameters": "",
                    "guarantee_and_assumptions": "",
                    "baseline_protocol_and_metrics": "",
                    "results_with_localizer": "",
                    "limitations_or_counterevidence": "",
                    "relevance_to_tfm": "",
                },
                "evidence_status": "requires_close_reading",
                "allowed_use": "not_a_claim_until_passage_is_verified",
            }
        )
    return cards


def write_qa(path: Path, query_rows: list[dict[str, Any]], seeds: list[dict[str, Any]], reading_queue: list[dict[str, Any]]) -> None:
    role_counts = Counter(row["scientific_role_structural"] for row in reading_queue)
    target_counts = Counter(target for row in reading_queue for target in row["review_targets_routing_only"].split(";") if target)
    tier_counts = Counter(row["priority_tier"] for row in reading_queue)
    wos_counts = Counter(row["historical_status"] for row in query_rows)
    lines = [
        "# V3 intake quality assurance",
        "",
        "This report prepares a close-reading workspace. It does not promote structural coding or historical search results to V3 evidence.",
        "",
        f"- Historical candidate seeds retained: **{len(seeds)}**.",
        f"- Identity-verified full texts queued for close reading: **{len(reading_queue)}**.",
        f"- Web of Science query definitions ledgered: **{len(query_rows)}**.",
        "- Every queue row is initialized as `requires_close_reading` and is prohibited from supporting a claim until a passage is verified.",
        "",
        "## Structural-role routing",
        "",
        *[f"- `{name or 'UNCLASSIFIED'}`: {count}" for name, count in sorted(role_counts.items())],
        "",
        "## Routing targets",
        "",
        *[f"- `{name}`: {count}" for name, count in sorted(target_counts.items())],
        "",
        "## Reading priority",
        "",
        *[f"- `{name}`: {count}" for name, count in sorted(tier_counts.items())],
        "",
        "## Historical Web of Science exports",
        "",
        *[f"- `{name or 'not_reconciled_in_v3'}`: {count}" for name, count in sorted(wos_counts.items())],
        "",
        "V3 execution fields remain `not_queried`; prior WoS files are retained only as auditable historical provenance.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    paths = {
        "data": output / "data",
        "reports": output / "reports",
        "manifests": output / "manifests",
    }
    for directory in paths.values():
        directory.mkdir(parents=True, exist_ok=True)
    corpus_rows = read_csv(CORPUS)
    matrix_rows = read_csv(MATRIX)
    query_rows = query_ledger_rows(read_csv(WOS_PACK), load_manifest(WOS_MANIFEST))
    seeds = seed_rows(corpus_rows)
    corpus_by_id = {clean(row.get("candidate_id")): row for row in corpus_rows}
    queue = reading_rows(matrix_rows, corpus_by_id)
    if len({row["candidate_id"] for row in queue}) != len(queue):
        raise ValueError("V3 reading queue contains duplicate candidate IDs")
    if any(row["v3_evidence_status"] != "requires_close_reading" for row in queue):
        raise ValueError("V3 queue promoted evidence before close reading")
    if len(query_rows) != len(read_csv(WOS_PACK)):
        raise ValueError("Every source query must receive a V3 ledger row")

    query_path = paths["data"] / "query_ledger_v3.csv"
    seed_path = paths["data"] / "seed_registry_v3.csv"
    queue_path = paths["data"] / "priority_reading_queue_v3.csv"
    cards_path = paths["data"] / "review_cards_v3.jsonl"
    qa_path = paths["reports"] / "v3_intake_qa.md"
    write_csv(query_path, query_rows, list(query_rows[0]))
    write_csv(seed_path, seeds, list(seeds[0]))
    write_csv(queue_path, queue, list(queue[0]))
    write_jsonl(cards_path, card_rows(queue))
    write_qa(qa_path, query_rows, seeds, queue)
    outputs = [query_path, seed_path, queue_path, cards_path, qa_path]
    manifest = {
        "schema_version": "1.0",
        "review_version": "V3",
        "generated_at_utc": utc_now(),
        "inputs": {str(path.relative_to(BASE)).replace("\\", "/"): sha256(path) for path in [CORPUS, MATRIX, WOS_MANIFEST, WOS_PACK]},
        "outputs": {str(path.relative_to(BASE)).replace("\\", "/"): sha256(path) for path in outputs},
        "counts": {"candidate_seeds": len(seeds), "fulltext_close_reading_queue": len(queue), "query_ledger_rows": len(query_rows)},
        "evidence_boundary": "All V3 reading cards require close reading and a verified localizer before claim use.",
    }
    manifest_path = paths["manifests"] / "v3_prepare_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = prepare(args.output)
    print(json.dumps(manifest["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
