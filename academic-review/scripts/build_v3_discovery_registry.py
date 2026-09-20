"""Reconcile V3 public discovery with historical seeds without silent loss.

The registry is a discovery inventory. It preserves the legacy V1/V2 screening
state as provenance, but assigns every merged item a fresh V3 screening state of
``not_screened`` until a V3 decision and rationale are recorded.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
SEEDS = V3 / "data" / "seed_registry_v3.csv"
OPEN = V3 / "data" / "v3_open_discovery_unique.csv"
LEGACY = BASE / "data" / "processed" / "candidate_corpus_stage1c.csv"


def clean(value: Any) -> str:
    return str(value or "").strip()


def norm_doi(value: Any) -> str:
    value = clean(value).lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    return value.removeprefix("doi:").strip().rstrip(".,;)")


def norm_title(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def identity_key(row: dict[str, Any]) -> str:
    doi = norm_doi(row.get("doi_norm") or row.get("doi"))
    if doi:
        return f"doi:{doi}"
    title = norm_title(row.get("title_norm") or row.get("title"))
    return f"title-year:{title}|{clean(row.get('year'))}" if title else f"candidate:{clean(row.get('candidate_id'))}"


def merge_values(*values: str) -> str:
    items: list[str] = []
    for value in values:
        items.extend(item for item in clean(value).split(";") if item)
    return ";".join(dict.fromkeys(items))


def build_registry(seed_rows: list[dict[str, str]], open_rows: list[dict[str, str]], legacy_by_id: dict[str, dict[str, str]]) -> tuple[list[dict[str, str]], Counter[str]]:
    registry: dict[str, dict[str, str]] = {}
    aliases: Counter[str] = Counter()
    all_rows: list[tuple[str, dict[str, str]]] = [("historical_seed", row) for row in seed_rows] + [("v3_open_discovery", row) for row in open_rows]
    for origin, source in all_rows:
        candidate_id = clean(source.get("candidate_id"))
        legacy = legacy_by_id.get(candidate_id, {})
        key = identity_key(source)
        if key not in registry:
            registry[key] = {
                "v3_registry_id": candidate_id or hashlib.sha256(key.encode("utf-8")).hexdigest()[:13].upper(),
                "identity_key": key,
                "candidate_ids": candidate_id,
                "title": clean(source.get("title")),
                "authors": clean(source.get("authors")),
                "year": clean(source.get("year")),
                "venue": clean(source.get("venue")),
                "doi": norm_doi(source.get("doi_norm") or source.get("doi")),
                "abstract": clean(source.get("abstract") or legacy.get("abstract")),
                "document_type": clean(source.get("document_type") or legacy.get("document_type")),
                "discovery_origins": origin,
                "provenance_sources": clean(source.get("provenance_sources") or source.get("provenance")),
                "provenance_queries": clean(source.get("provenance_queries")),
                "legacy_screening_decisions": clean(source.get("screening_decision")),
                "legacy_fulltext_status": clean(source.get("fulltext_status")),
                "legacy_evidence_status": clean(source.get("evidence_status")),
                "metadata_status": clean(source.get("metadata_verification_status") or source.get("verification_status") or "metadata_partial"),
                "v3_screening_status": "not_screened",
                "v3_screening_reason": "",
                "v3_allowed_use": "discovery_only_until_v3_screening_and_passage_verification",
                "duplicate_alias_count": "0",
            }
            continue
        target = registry[key]
        aliases[key] += 1
        target["candidate_ids"] = merge_values(target["candidate_ids"], candidate_id)
        target["discovery_origins"] = merge_values(target["discovery_origins"], origin)
        target["provenance_sources"] = merge_values(target["provenance_sources"], clean(source.get("provenance_sources") or source.get("provenance")))
        target["provenance_queries"] = merge_values(target["provenance_queries"], clean(source.get("provenance_queries")))
        target["legacy_screening_decisions"] = merge_values(target["legacy_screening_decisions"], clean(source.get("screening_decision")))
        target["legacy_fulltext_status"] = merge_values(target["legacy_fulltext_status"], clean(source.get("fulltext_status")))
        target["legacy_evidence_status"] = merge_values(target["legacy_evidence_status"], clean(source.get("evidence_status")))
        if not target["abstract"] and clean(source.get("abstract") or legacy.get("abstract")):
            target["abstract"] = clean(source.get("abstract") or legacy.get("abstract"))
        if not target["authors"] and clean(source.get("authors")):
            target["authors"] = clean(source.get("authors"))
        if not target["venue"] and clean(source.get("venue")):
            target["venue"] = clean(source.get("venue"))
    for key, count in aliases.items():
        registry[key]["duplicate_alias_count"] = str(count)
    return sorted(registry.values(), key=lambda row: (row["title"].lower(), row["year"], row["v3_registry_id"])), aliases


def main() -> None:
    seeds = read_csv(SEEDS)
    open_records = read_csv(OPEN)
    legacy_by_id = {clean(row.get("candidate_id")): row for row in read_csv(LEGACY)}
    registry, aliases = build_registry(seeds, open_records, legacy_by_id)
    output = V3 / "data" / "discovery_registry_v3.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output, registry, list(registry[0]))
    origins = Counter(row["discovery_origins"] for row in registry)
    report = V3 / "reports" / "v3_discovery_registry_qa.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# V3 discovery registry QA\n\n"
        "The registry preserves candidates and aliases. It does not re-use historical screening as a V3 inclusion decision.\n\n"
        f"- Historical seed rows: {len(seeds)}\n"
        f"- New open-discovery unique rows: {len(open_records)}\n"
        f"- Registry identities: {len(registry)}\n"
        f"- Collapsed aliases: {sum(aliases.values())}\n"
        + "\n".join(f"- `{origin}`: {count}" for origin, count in sorted(origins.items()))
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed_registry_sha256": sha256(SEEDS),
        "open_discovery_sha256": sha256(OPEN),
        "legacy_corpus_sha256": sha256(LEGACY),
        "registry_sha256": sha256(output),
        "registry_identities": len(registry),
        "collapsed_aliases": sum(aliases.values()),
    }
    (V3 / "manifests" / "v3_discovery_registry_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"registry": len(registry), "aliases": sum(aliases.values())}, sort_keys=True))


if __name__ == "__main__":
    main()
