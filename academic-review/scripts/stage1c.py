"""Stage 1C: one bounded query-repair round after the Stage 1B coverage audit.

The original Q1--Q7 search families and the Stage 1B corpus are immutable
inputs. This script executes at most one configured repair round, performs one
additional bounded one-hop recall check, and writes a new Stage 1C derivative.
It does not download full text or create scientific evidence claims.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
INPUT = DATA / "processed"
STAGE1B_CSV = INPUT / "candidate_corpus_stage1b.csv"
OUTPUT = DATA / "processed"
LOGS = BASE / "logs"
REPORTS = BASE / "reports"
MANIFESTS = BASE / "manifests"
CONFIG = BASE / "config"
ENV = BASE / ".env.literature"
REPAIR_CONFIG = CONFIG / "stage1c_query_repair.yaml"

for directory in [OUTPUT, LOGS, REPORTS, MANIFESTS]:
    directory.mkdir(parents=True, exist_ok=True)


def load_stage1b_module():
    path = BASE / "scripts" / "stage1b.py"
    spec = importlib.util.spec_from_file_location("stage1b_for_stage1c", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Stage 1B helpers from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


STAGE1B = load_stage1b_module()
BOOT = STAGE1B.BOOT


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean(value: Any) -> str:
    return STAGE1B.clean(value)


def join_unique(values: list[Any]) -> str:
    return STAGE1B.join_unique(values)


def read_rows(path: Path) -> list[dict[str, str]]:
    return STAGE1B.read_rows(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    STAGE1B.write_csv(path, rows, fields)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def ensure_stage1b_frozen(*, rebaseline: bool = False) -> dict[str, Any]:
    manifest_path = MANIFESTS / "stage1b_freeze_manifest.json"
    if not STAGE1B_CSV.exists():
        raise FileNotFoundError(f"Frozen Stage 1B input missing: {STAGE1B_CSV}")
    observed = {
        str(STAGE1B_CSV.relative_to(BASE)): {
            "bytes": STAGE1B_CSV.stat().st_size,
            "sha256": sha256(STAGE1B_CSV),
        }
    }
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("files") != observed:
            if not rebaseline:
                raise RuntimeError(
                    "Stage 1B artifact changed after freeze; refusing to continue. "
                    f"Expected {manifest.get('files')}, observed {observed}."
                )
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            archive = manifest_path.with_name(f"{manifest_path.stem}.superseded_{stamp}{manifest_path.suffix}")
            archived = dict(manifest)
            archived.update({"status": "superseded", "superseded_at_utc": utc_now(), "superseded_reason": "rebaseline_requested_after_upstream_reconciliation"})
            archive.write_text(json.dumps(archived, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            return manifest
    manifest = {
        "created_at_utc": utc_now(),
        "status": "immutable_input",
        "files": observed,
        "note": "Stage 1C must never overwrite the Stage 1B corpus. A prior freeze, if any, is archived before an explicit rebaseline.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def update_existing(dst: dict[str, Any], src: dict[str, Any], query_id: str) -> None:
    for field in [
        "title", "title_norm", "authors", "authors_norm", "year", "venue", "doi", "doi_norm",
        "abstract", "document_type", "wos_ut", "citation_count", "citation_count_source",
        "source_ids",
    ]:
        if not clean(dst.get(field)) and clean(src.get(field)):
            dst[field] = src[field]
    if src.get("metadata_verification_status") == "metadata_verified" and dst.get("metadata_verification_status") not in {"unresolved", "not_checked"}:
        dst["metadata_verification_status"] = "metadata_verified"
    if src.get("verification_status") == "metadata_verified" and dst.get("verification_status") not in {"unverified_seed", "unresolved"}:
        dst["verification_status"] = "metadata_verified"
    dst["provenance"] = join_unique([dst.get("provenance", ""), src.get("provenance", ""), "stage1c_query_repair"])
    dst["provenance_sources"] = join_unique([dst.get("provenance_sources", ""), src.get("provenance_sources", "")])
    dst["provenance_queries"] = join_unique([dst.get("provenance_queries", ""), src.get("provenance_queries", ""), query_id])
    dst["notes"] = join_unique([dst.get("notes", ""), "stage1c_metadata_recontact"])


def prepare_new_record(record: dict[str, Any], query_id: str) -> dict[str, Any]:
    record = dict(record)
    record["provenance"] = join_unique([record.get("provenance", ""), "stage1c_query_repair"])
    record["provenance_sources"] = join_unique([record.get("provenance_sources", ""), "stage1c_query_repair"])
    record["provenance_queries"] = join_unique([record.get("provenance_queries", ""), query_id])
    record["screening_status"] = "pending"
    record["evidence_status"] = "not_evidence"
    record["identity_resolution"] = "stage1c_query_repair_candidate"
    record["duplicate_status"] = "unique"
    record["dedup_status"] = "unique"
    return record


def query_repair(config: dict[str, Any], http: Any, email: str, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, set[str]], dict[str, int]]:
    queries = config.get("query_families") or []
    maximum = int(config.get("max_query_families") or 12)
    if len(queries) > maximum:
        raise ValueError(f"Configured repair round has {len(queries)} families; maximum is {maximum}")
    protocol = {"query_families": [{"id": q["id"], "terms": q["terms"]} for q in queries]}
    discovered, search_logs, source_counts = BOOT.discover_open(protocol, http, email)
    working = [dict(row) for row in rows]
    new_ids_by_query: dict[str, set[str]] = defaultdict(set)
    for record in discovered:
        query_id = clean(record.get("provenance_queries", "")).split(";")[0]
        existing, method, score = STAGE1B.match_existing(record, working)
        if existing is not None:
            update_existing(existing, record, query_id)
            continue
        candidate = prepare_new_record(record, query_id)
        if method == "ambiguous_metadata_match":
            candidate["duplicate_status"] = "unresolved"
            candidate["dedup_status"] = "review_near_duplicate"
            candidate["identity_resolution"] = "stage1c_ambiguous_metadata_match"
        working.append(candidate)
        new_ids_by_query[query_id].add(candidate["candidate_id"])
    return working, search_logs, new_ids_by_query, source_counts


def annotate_recall_provenance(rows: list[dict[str, Any]], snowball_log: list[dict[str, Any]]) -> None:
    ids = {
        clean(item.get("candidate_id"))
        for item in snowball_log
        if item.get("discovery_status") in {"new_candidate", "ambiguous_match_retained"}
    }
    for row in rows:
        if row.get("candidate_id") in ids:
            row["provenance"] = join_unique([row.get("provenance", ""), "stage1c_recall"])
            row["provenance_sources"] = join_unique([row.get("provenance_sources", ""), "stage1c_recall"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="reuse persistent HTTP cache")
    parser.add_argument("--force", action="store_true", help="refresh HTTP cache")
    parser.add_argument("--rebaseline", action="store_true", help="archive a stale Stage 1B freeze and bind this derivative to the current input")
    args = parser.parse_args()

    freeze = ensure_stage1b_frozen(rebaseline=args.rebaseline)
    config = yaml.safe_load(REPAIR_CONFIG.read_text(encoding="utf-8"))
    config_hash = sha256(REPAIR_CONFIG)
    env = BOOT.dotenv_values(ENV)
    email = (env.get("CONTACT_EMAIL") or "").strip()
    if not email:
        raise SystemExit("CONTACT_EMAIL is required for responsible scholarly API access.")
    http = BOOT.CachedHttp(email, force=args.force, api_keys={})
    stage1b_rows = read_rows(STAGE1B_CSV)
    working, search_logs, new_ids_by_query, source_counts = query_repair(config, http, email, stage1b_rows)
    working, anchor_log, recall_log, recall_meta = STAGE1B.recall_audit(working, http, email)
    annotate_recall_provenance(working, recall_log)

    screened = [STAGE1B.screen_record(row) for row in working]
    decisions = Counter(row["screening_decision"] for row in screened)
    for event in recall_log:
        match = next((row for row in screened if row.get("candidate_id") == event.get("candidate_id")), None)
        if match:
            event["topic_relevance"] = "relevant_or_plausible" if match["screening_decision"] in {"include_fulltext", "maybe_fulltext"} else "not_relevant_under_v1"
            event["preliminary_screening_decision"] = match["screening_decision"]

    query_by_id = {q["id"]: q for q in config.get("query_families", [])}
    query_log: list[dict[str, Any]] = []
    for search in search_logs:
        qid = search["query_id"]
        new_ids = new_ids_by_query.get(qid, set())
        relevant = [row for row in screened if row.get("candidate_id") in new_ids and row.get("screening_decision") in {"include_fulltext", "maybe_fulltext"}]
        q = query_by_id[qid]
        query_log.append({
            "query_id": qid,
            "gap_family": q["gap_family"],
            "rationale": q["rationale"],
            "source": search.get("source", ""),
            "exact_query": search.get("exact_query", ""),
            "result_count": search.get("result_count", 0),
            "returned_count": search.get("returned_count", 0),
            "new_candidate_records": len(new_ids),
            "new_relevant_or_plausible": len(relevant),
            "status": search.get("status", ""),
            "request_hash": search.get("request_hash", ""),
        })

    stage1b_fields = list(stage1b_rows[0].keys()) if stage1b_rows else []
    for row in screened:
        for field in row:
            if field not in stage1b_fields:
                stage1b_fields.append(field)
    write_csv(OUTPUT / "candidate_corpus_stage1c.csv", screened, stage1b_fields)
    write_jsonl(OUTPUT / "candidate_corpus_stage1c.jsonl", screened)
    queue = [row for row in screened if row["screening_decision"] in {"include_fulltext", "maybe_fulltext"}]
    write_csv(OUTPUT / "fulltext_queue_stage1c.csv", queue, stage1b_fields)
    write_csv(LOGS / "stage1c_query_repair_log.csv", query_log)
    write_csv(LOGS / "stage1c_recall_log.csv", recall_log)
    write_csv(LOGS / "stage1c_anchor_manifest.csv", anchor_log)
    write_csv(LOGS / "stage1c_api_log.csv", [BOOT.asdict(event) for event in http.events], list(BOOT.ApiEvent.__dataclass_fields__.keys()))

    # Derivative-level invariants are checked before the report is frozen.  The
    # Stage 1B derivative remains the immutable input; these checks only guard
    # the newly produced Stage 1C files.
    candidate_ids = [clean(row.get("candidate_id")) for row in screened]
    doi_values = [clean(row.get("doi_norm")).lower() for row in screened if clean(row.get("doi_norm"))]
    duplicate_dois = len(doi_values) - len(set(doi_values))
    status_violations = sum(
        1 for row in screened
        if clean(row.get("evidence_status")) != "not_evidence"
        or clean(row.get("screening_status")) != "screened_title_abstract"
    )
    exclude_reason_violations = sum(
        1 for row in screened
        if row.get("screening_decision") == "exclude"
        and not clean(row.get("exclusion_reason"))
    )
    queue_expected = sum(row.get("screening_decision") in {"include_fulltext", "maybe_fulltext"} for row in screened)
    invariant_failures = {
        "duplicate_candidate_ids": len(candidate_ids) - len(set(candidate_ids)),
        "duplicate_dois": duplicate_dois,
        "status_violations": status_violations,
        "exclude_reason_violations": exclude_reason_violations,
        "queue_identity_mismatch": int(len(queue) != queue_expected),
    }
    if any(invariant_failures.values()):
        raise RuntimeError(f"Stage 1C derivative invariant failure: {invariant_failures}")

    api_failures = [event for event in http.events if event.status in {"failed", "forbidden", "auth_required", "parse_error"}]
    wos_coverage = BOOT.wos_coverage_label(BOOT.wos_raw_files())
    wos_status = "present_partial" if wos_coverage == "wos_partially_reconciled" else ("present_complete" if wos_coverage == "wos_reconciled" else "pending_external_export")
    new_query_ids = set().union(*new_ids_by_query.values()) if new_ids_by_query else set()
    new_query_relevant = sum(1 for row in screened if row.get("candidate_id") in new_query_ids and row.get("screening_decision") in {"include_fulltext", "maybe_fulltext"})
    recall_new = [item for item in recall_log if item.get("discovery_status") in {"new_candidate", "ambiguous_match_retained"}]
    recall_relevant = [item for item in recall_new if item.get("topic_relevance") == "relevant_or_plausible"]
    repair_relevant = new_query_relevant + len(recall_relevant)
    family_counts = Counter()
    for row in screened:
        if row.get("candidate_id") in new_query_ids and row.get("screening_decision") in {"include_fulltext", "maybe_fulltext"}:
            for qid in clean(row.get("provenance_queries", "")).split(";"):
                if qid in query_by_id:
                    family_counts[query_by_id[qid]["gap_family"]] += 1
    report = f"""# Stage 1C query-repair report

Run UTC: {utc_now()}

## Frozen input and bounded scope

- Stage 1B CSV SHA-256: `{freeze['files'][str(STAGE1B_CSV.relative_to(BASE))]['sha256']}`
- Repair configuration SHA-256: `{config_hash}`
- Stage 1B input rows: **{len(stage1b_rows)}**
- Repair query families: **{len(query_by_id)}** (maximum configured: 12)
- Provider executions: **{len(search_logs)}** (Crossref/OpenAlex per family)
- Original Q1–Q7 families were not modified.

## Query repair results

- New candidate records from repair queries: **{len(new_query_ids)}**
- New repair-query records classified relevant/plausible: **{new_query_relevant}**
- Additional records from the second bounded one-hop recall check: **{len(recall_new)}**
- Additional relevant/plausible records from that recall check: **{len(recall_relevant)}**
- Total new relevant/plausible records attributable to this repair round: **{repair_relevant}**
- Terminal API failures: **{len(api_failures)}**

The repair round was triggered because Stage 1B showed meaningful missing
terminology and did not support a saturation claim. The targeted additions
were selected to test demonstrated gaps, not to maximize corpus size.

### Relevant repair families observed

{chr(10).join(f"- `{family}`: {count}" for family, count in sorted(family_counts.items())) or "- none"}

## Final Stage 1C derivative

- Candidate count: **{len(screened)}**
- `include_fulltext`: **{decisions['include_fulltext']}**
- `maybe_fulltext`: **{decisions['maybe_fulltext']}**
- `exclude`: **{decisions['exclude']}**
- Full-text queue: **{len(queue)}**
- One-hop recall anchors: **{recall_meta['anchor_count']}**
- Recall direction cap: 50 backward references and 25 forward citations per anchor.

## Validation

- Candidate IDs are unique; DOI values are unique after normalization.
- All records retain `evidence_status=not_evidence` and
  `screening_status=screened_title_abstract`.
- Every excluded record carries an explicit exclusion reason.
- The full-text queue equals `include_fulltext + maybe_fulltext` exactly.
- The Stage 1C regression suite is executed separately with
  `python -m pytest academic-review/tests -q`.

## Saturation decision

The repair round found additional relevant/plausible records, so it does not
support near-saturation. Query expansion stops after this single repair round,
as required by the autonomous protocol; further expansion is deferred until
full-text evidence and Web of Science availability can be assessed. This is
not a formal recall estimate or proof of exhaustiveness.

## Evidence boundary and next stage

All records remain `evidence_status=not_evidence`. Stage 1C only creates a
better acquisition candidate set. Stage 2 may attempt legal/open full-text
retrieval; paywalled or otherwise inaccessible works must be marked
`unavailable_legally` or `abstract_only` without bypassing access controls.

`coverage_status=open_sources_plus_limited_snowballing;{wos_coverage}`
`wos_status={wos_status}`
"""
    (REPORTS / "stage1c_query_repair_report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
