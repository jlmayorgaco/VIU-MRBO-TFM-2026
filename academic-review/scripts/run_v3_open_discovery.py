"""Execute the frozen V3 query families against public scholarly APIs only.

Google Scholar, Web of Science, Scopus and IEEE Xplore remain manual sources.
This runner uses the already tested V2 adapters but redirects every raw response,
event, record and manifest into the separate V3 namespace. Metadata discovery
never constitutes scientific evidence or a completed screening decision.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
LEDGER = V3 / "data" / "query_ledger_v3.csv"
ENV = BASE / ".env.literature"
RAW = V3 / "raw"
LOGS = V3 / "logs"
DATA = V3 / "data"
REPORTS = V3 / "reports"
MANIFESTS = V3 / "manifests"


def clean(value: Any) -> str:
    return str(value or "").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else ["source"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_v2_adapters() -> Any:
    source = BASE / "multisource-v2" / "scripts" / "run_multisource_v2.py"
    spec = importlib.util.spec_from_file_location("mrob_v3_public_api_adapters", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load public API adapters from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # CachedClient and its event serializer resolve these module globals at
    # runtime. Redirecting them prevents writes to the historical V2 campaign.
    module.V2_ROOT = V3
    module.RAW = RAW
    return module


def build_plan(ledger_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Translate the frozen source-independent V3 ledger to adapter fields."""
    plan: list[dict[str, Any]] = []
    for row in ledger_rows:
        if clean(row.get("source")) != "web_of_science":
            continue
        try:
            from_year = int(clean(row.get("from_year")))
            to_year = int(clean(row.get("to_year")))
        except ValueError as exc:
            raise ValueError(f"Invalid date window in {row.get('execution_id')}") from exc
        plan.append(
            {
                "execution_id": clean(row.get("execution_id")),
                "query_id": clean(row.get("query_id")),
                "window_id": clean(row.get("window_id")),
                "query": clean(row.get("exact_query")),
                "from_year": from_year,
                "to_year": to_year,
            }
        )
    if not plan:
        raise ValueError("The V3 ledger did not contain executable query families")
    return plan


def payload_items(adapters: Any, source: str, payload: Any) -> tuple[list[dict[str, Any]], int]:
    if source == "crossref":
        return adapters.crossref_items(payload)
    if source == "openalex":
        return adapters.openalex_items(payload)
    if source == "arxiv":
        return adapters.parse_arxiv(payload)
    raise ValueError(f"Unsupported public source: {source}")


def merged_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate conservatively while retaining every query/source provenance."""
    merged: dict[str, dict[str, Any]] = {}
    for record in records:
        key = clean(record.get("doi_norm")) or clean(record.get("title_norm")) or clean(record.get("candidate_id"))
        if not key:
            continue
        if key not in merged:
            merged[key] = dict(record)
            continue
        primary = merged[key]
        for field in ("provenance_sources", "provenance_queries", "source_ids"):
            values = [item for item in (primary.get(field, "") + ";" + record.get(field, "")).split(";") if item]
            primary[field] = ";".join(dict.fromkeys(values))
        primary["citation_count"] = str(max(int(primary.get("citation_count") or 0), int(record.get("citation_count") or 0)))
        if not clean(primary.get("abstract")) and clean(record.get("abstract")):
            primary["abstract"] = record["abstract"]
        if not clean(primary.get("open_access_url")) and clean(record.get("open_access_url")):
            primary["open_access_url"] = record["open_access_url"]
    return sorted(merged.values(), key=lambda row: (row.get("title_norm", ""), row.get("year", ""), row.get("candidate_id", "")))


def retain_other_sources(path: Path, selected_sources: list[str]) -> list[dict[str, str]]:
    """Keep prior output from sources not being refreshed in this invocation."""
    if not path.is_file() or not path.read_text(encoding="utf-8-sig").strip():
        return []
    return [row for row in read_csv(path) if clean(row.get("source")) not in selected_sources]


def run_source(adapters: Any, source: str, plan: list[dict[str, Any]], client: Any, limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []
    for item in plan:
        before = len(client.events)
        payload, endpoint, params = adapters.source_query(source, item, client, limit)
        items, reported = payload_items(adapters, source, payload)
        normalized = [adapters.normalize_item(source, row, item["query_id"], item["window_id"]) for row in items]
        returned = [row for row in normalized if row]
        records.extend(returned)
        events = client.events[before:]
        error_events = [event for event in events if event.status not in {"ok", "cache_hit"}]
        executions.append(
            {
                "review_version": "V3",
                "source": source,
                "execution_id": item["execution_id"],
                "query_id": item["query_id"],
                "window_id": item["window_id"],
                "exact_query": item["query"],
                "adapter_query": json.dumps(params, ensure_ascii=False, sort_keys=True),
                "endpoint": endpoint,
                "from_year": item["from_year"],
                "to_year": item["to_year"],
                "reported_result_count": reported,
                "returned_record_count": len(returned),
                "status": "ok" if not error_events else ("partial" if returned else error_events[-1].status),
                "error": error_events[-1].error if error_events else "",
                "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
    return records, executions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="crossref,openalex", help="Public sources: crossref, openalex, arxiv")
    parser.add_argument("--limit-per-query", type=int, default=25)
    parser.add_argument("--resume", action="store_true", help="Reuse matching raw V3 responses.")
    args = parser.parse_args()
    selected_sources = [name.strip() for name in args.sources.split(",") if name.strip()]
    supported = {"crossref", "openalex", "arxiv"}
    invalid = set(selected_sources) - supported
    if invalid:
        raise SystemExit(f"Unsupported public source(s): {', '.join(sorted(invalid))}")
    if not selected_sources:
        raise SystemExit("At least one public source is required")

    for directory in (RAW, LOGS, DATA, REPORTS, MANIFESTS):
        directory.mkdir(parents=True, exist_ok=True)
    env = dotenv_values(ENV)
    email = clean(env.get("CONTACT_EMAIL") or os.environ.get("CONTACT_EMAIL"))
    if not email:
        raise SystemExit("CONTACT_EMAIL is required for responsible scholarly API access.")
    keys = {"OPENALEX_API_KEY": clean(env.get("OPENALEX_API_KEY") or os.environ.get("OPENALEX_API_KEY"))}
    adapters = load_v2_adapters()
    client = adapters.CachedClient(email, keys, force=not args.resume)
    plan = build_plan(read_csv(LEDGER))
    all_records: list[dict[str, Any]] = []
    all_executions: list[dict[str, Any]] = []
    for source in selected_sources:
        records, executions = run_source(adapters, source, plan, client, max(1, min(args.limit_per_query, 100)))
        all_records.extend(records)
        all_executions.extend(executions)

    raw_path = DATA / "v3_open_discovery_records.csv"
    unique_path = DATA / "v3_open_discovery_unique.csv"
    execution_path = DATA / "query_execution_v3.csv"
    events_path = LOGS / "public_api_events_v3.csv"
    combined_records = retain_other_sources(raw_path, selected_sources) + all_records
    combined_executions = retain_other_sources(execution_path, selected_sources) + all_executions
    combined_events = retain_other_sources(events_path, selected_sources) + [asdict(event) for event in client.events]
    write_csv(raw_path, combined_records)
    write_csv(unique_path, merged_records(combined_records))
    write_csv(execution_path, combined_executions)
    write_csv(events_path, combined_events)
    statuses = Counter(row["status"] for row in combined_executions)
    report = REPORTS / "v3_open_discovery_coverage.md"
    report.write_text(
        "# V3 public open-discovery coverage\n\n"
        "This report records metadata discovery only. It is neither screening nor passage-localized scientific evidence.\n\n"
        + "\n".join(f"- `{status}`: {count} query executions" for status, count in sorted(statuses.items()))
        + f"\n- Raw query-source records: {len(combined_records)}\n- Conservative DOI/title unique records: {len(merged_records(combined_records))}\n"
        + "\nWeb of Science and Google Scholar retain their manual-source status; no browser scraping was performed.\n",
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ledger_sha256": sha256(LEDGER),
        "sources": selected_sources,
        "limit_per_query": args.limit_per_query,
        "record_count": len(combined_records),
        "unique_record_count": len(merged_records(combined_records)),
        "execution_status_counts": dict(sorted(statuses.items())),
        "files": {name: sha256(path) for name, path in {"records": raw_path, "unique": unique_path, "executions": execution_path, "events": events_path}.items()},
    }
    (MANIFESTS / "v3_open_discovery_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(combined_records), "unique": len(merged_records(combined_records)), "statuses": dict(sorted(statuses.items()))}, sort_keys=True))


if __name__ == "__main__":
    main()
