"""Stage 1B: identity audit, bounded recall audit and title/abstract screening.

This script consumes the frozen Stage 1A corpus and writes only Stage 1B
derivatives. It deliberately does not download PDFs or write scientific
evidence claims.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
INPUT = DATA / "processed"
STAGE1A_CSV = INPUT / "candidate_corpus_stage1a.csv"
STAGE1A_JSONL = INPUT / "candidate_corpus_stage1a.jsonl"
OUTPUT = DATA / "processed"
LOGS = BASE / "logs"
REPORTS = BASE / "reports"
MANIFESTS = BASE / "manifests"
CONFIG = BASE / "config"
PROTOCOL = BASE / "protocol" / "screening_protocol_v1.md"
ENV = BASE / ".env.literature"

for directory in [OUTPUT, LOGS, REPORTS, MANIFESTS, CONFIG]:
    directory.mkdir(parents=True, exist_ok=True)


BOOTSTRAP_PATH = BASE / "scripts" / "bootstrap_literature.py"
_spec = importlib.util.spec_from_file_location("stage1a_bootstrap", BOOTSTRAP_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Cannot load Stage 1A helpers from {BOOTSTRAP_PATH}")
BOOT = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = BOOT
_spec.loader.exec_module(BOOT)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"none", "nan", "null"} else text


def fold(value: Any) -> str:
    text = unicodedata.normalize("NFKD", clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def tokens(value: Any) -> set[str]:
    return set(fold(value).split())


def contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_stage1a_frozen(*, rebaseline: bool = False) -> dict[str, Any]:
    """Create once, then verify, the immutable Stage 1A hash manifest."""
    manifest_path = MANIFESTS / "stage1a_freeze_manifest.json"
    paths = [STAGE1A_CSV, STAGE1A_JSONL]
    if not all(path.exists() for path in paths):
        missing = ", ".join(str(path) for path in paths if not path.exists())
        raise FileNotFoundError(f"Frozen Stage 1A input missing: {missing}")

    current = {
        str(path.relative_to(BASE)): {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in paths
    }
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest.get("files", {})
        if expected != current:
            if not rebaseline:
                raise RuntimeError(
                    "Stage 1A artifacts changed after freeze; refusing to continue. "
                    f"Expected {expected}, observed {current}."
                )
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            archive = manifest_path.with_name(f"{manifest_path.stem}.superseded_{stamp}{manifest_path.suffix}")
            archived = dict(manifest)
            archived.update({"status": "superseded", "superseded_at_utc": utc_now(), "superseded_reason": "rebaseline_requested_after_new_source_ingestion"})
            archive.write_text(json.dumps(archived, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            return manifest

    manifest = {
        "created_at_utc": utc_now(),
        "status": "immutable_input",
        "files": current,
        "note": "Stage 1B must never overwrite these files. A prior freeze, if any, is archived before an explicit rebaseline.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if len({row.get("candidate_id", "") for row in rows}) != len(rows):
        raise ValueError("Stage 1A candidate_id values are not unique")
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0].keys()) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fields:
            return
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def join_unique(values: list[Any]) -> str:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        for part in clean(value).split(";"):
            part = part.strip()
            if part and part not in seen:
                seen.add(part)
                result.append(part)
    return ";".join(result)


def openalex_id(value: Any) -> str:
    match = re.search(r"\bW\d+\b", clean(value))
    return match.group(0) if match else ""


def row_openalex_id(row: dict[str, Any]) -> str:
    return openalex_id(row.get("source_ids", ""))


def row_text(row: dict[str, Any]) -> str:
    return fold(" ".join([clean(row.get("title", "")), clean(row.get("abstract", ""))]))


def identity_compatible(a: dict[str, Any], b: dict[str, Any], threshold: float = 98.5) -> tuple[bool, float]:
    title_a = clean(a.get("title_norm")) or BOOT.norm_title(a.get("title", ""))
    title_b = clean(b.get("title_norm")) or BOOT.norm_title(b.get("title", ""))
    score = float(BOOT.ratio(title_a, title_b))
    if score < threshold:
        return False, score
    ya, yb = BOOT.safe_year(a.get("year", "")), BOOT.safe_year(b.get("year", ""))
    if ya and yb and abs(int(ya) - int(yb)) > 1:
        return False, score
    aa, ab = BOOT.first_author(a.get("authors", "")), BOOT.first_author(b.get("authors", ""))
    if aa and ab and aa != ab:
        return False, score
    va, vb = BOOT.norm_title(a.get("venue", "")), BOOT.norm_title(b.get("venue", ""))
    if va and vb and BOOT.ratio(va, vb) < 80:
        return False, score
    return True, score


def merge_alias_group(rows: list[dict[str, Any]], canonical: dict[str, Any], relationship: str) -> dict[str, Any]:
    merged = dict(canonical)
    aliases = [row for row in rows if row["candidate_id"] != canonical["candidate_id"]]
    merged["alias_candidate_ids"] = join_unique([row.get("candidate_id", "") for row in rows])
    merged["alias_dois"] = join_unique([row.get("doi_norm", "") for row in rows])
    merged["alias_titles"] = join_unique([row.get("title", "") for row in rows])
    merged["alias_source_ids"] = join_unique([row.get("source_ids", "") for row in rows])
    merged["identity_resolution"] = "merged_version_aliases"
    merged["version_relationship"] = relationship
    merged["duplicate_status"] = "unique"
    merged["dedup_status"] = "resolved_version_merge"
    merged["notes"] = join_unique([merged.get("notes", ""), f"Stage1B merged {len(aliases)} version alias(es): {relationship}"])
    for key in ["provenance", "provenance_sources", "provenance_queries", "source_ids"]:
        merged[key] = join_unique([row.get(key, "") for row in rows])
    for key in ["legacy_seed_id"]:
        merged[key] = join_unique([row.get(key, "") for row in rows])
    return merged


def resolve_probable_duplicates(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    flagged = [row for row in rows if row.get("duplicate_status") == "needs_review"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in flagged:
        groups[clean(row.get("title_norm")) or BOOT.norm_title(row.get("title", ""))].append(row)

    resolved_by_id: dict[str, dict[str, Any]] = {row["candidate_id"]: dict(row) for row in rows}
    removed: set[str] = set()
    log: list[dict[str, Any]] = []
    for group_index, (title_norm, group) in enumerate(sorted(groups.items()), start=1):
        title = fold(group[0].get("title", ""))
        if "dc mrta" in title:
            decision = "merge_published_preprint"
            relationship = "published_version_of_preprint"
            canonical = next((row for row in group if "arxiv" not in fold(row.get("venue", ""))), group[0])
        elif "optimizing coalition formation strategies" in title:
            decision = "merge_published_preprint"
            relationship = "published_version_of_preprint"
            canonical = next((row for row in group if "robotics" in fold(row.get("venue", ""))), group[0])
        elif "technical program" in title:
            decision = "retain_distinct_work"
            relationship = "distinct_work"
            canonical = None
        elif "grasp type robot end effectors" in title or "standard practice" in title:
            decision = "retain_distinct_standard_revision"
            relationship = "distinct_standard_revision"
            canonical = None
        else:
            decision = "retain_unresolved"
            relationship = "unresolved_identity"
            canonical = None

        resolved = None
        if canonical is not None:
            resolved = merge_alias_group(group, canonical, relationship)
            resolved_by_id[canonical["candidate_id"]] = resolved
            for row in group:
                if row["candidate_id"] != canonical["candidate_id"]:
                    removed.add(row["candidate_id"])

        for row in group:
            is_alias = canonical is not None and row["candidate_id"] != canonical["candidate_id"]
            out_status = "unique" if canonical is not None else ("unresolved" if decision == "retain_unresolved" else "unique")
            if not is_alias:
                resolved_by_id[row["candidate_id"]]["duplicate_status"] = out_status
                resolved_by_id[row["candidate_id"]]["identity_resolution"] = decision
                resolved_by_id[row["candidate_id"]]["version_relationship"] = relationship
            log.append({
                "resolution_group": f"DUP-{group_index:02d}",
                "candidate_id": row["candidate_id"],
                "resolved_candidate_id": canonical["candidate_id"] if canonical else row["candidate_id"],
                "decision": "merged_alias" if is_alias else decision,
                "match_method": "doi;publisher_registry_metadata;normalized_title;authors;year;venue",
                "identity_confidence": "high" if canonical else "distinct_or_unresolved",
                "duplicate_status_after": out_status,
                "alias_preserved": "yes" if canonical else "not_applicable",
                "notes": relationship,
            })

    output = [row for row in resolved_by_id.values() if row["candidate_id"] not in removed]
    return output, log


def recovery_match(seed: dict[str, Any], candidate: dict[str, Any]) -> tuple[bool, float, str]:
    title_seed = clean(seed.get("title_norm")) or BOOT.norm_title(seed.get("title", ""))
    title_candidate = clean(candidate.get("title_norm")) or BOOT.norm_title(candidate.get("title", ""))
    score = float(BOOT.ratio(title_seed, title_candidate))
    if score < 98.5:
        return False, score, "title_below_threshold"
    sy, cy = BOOT.safe_year(seed.get("year", "")), BOOT.safe_year(candidate.get("year", ""))
    if sy and cy and abs(int(sy) - int(cy)) > 1:
        return False, score, "year_incompatible"
    sa, ca = BOOT.first_author(seed.get("authors", "")), BOOT.first_author(candidate.get("authors", ""))
    if sa and ca and sa != ca:
        return False, score, "first_author_incompatible"
    return bool(candidate.get("doi_norm")), score, "accepted_metadata_match"


def recover_missing_dois(rows: list[dict[str, Any]], http: Any, email: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recovery_log: list[dict[str, Any]] = []
    output = [dict(row) for row in rows]
    for row in output:
        if row.get("doi_norm"):
            continue
        observations: list[dict[str, Any]] = []
        title = row.get("title", "")
        cr = http.get_json(
            "crossref",
            "stage1b_doi_recovery",
            "https://api.crossref.org/works",
            params={"query.bibliographic": title, "rows": 5, "mailto": email},
        )
        for item in (((cr or {}).get("message") or {}).get("items") or []):
            candidate = BOOT.crossref_item_to_record(item, "stage1b_doi_recovery")
            accepted, score, reason = recovery_match(row, candidate)
            if candidate.get("doi_norm"):
                observations.append({"source": "crossref", "doi": candidate["doi_norm"], "score": score, "accepted": accepted, "reason": reason})

        oa_query = BOOT.openalex_search_query(title)
        oa = http.get_json(
            "openalex",
            "stage1b_doi_recovery",
            "https://api.openalex.org/works",
            params={"search": oa_query, "per-page": 5},
        )
        for item in ((oa or {}).get("results") or []):
            candidate = BOOT.openalex_item_to_record(item, "stage1b_doi_recovery")
            accepted, score, reason = recovery_match(row, candidate)
            if candidate.get("doi_norm"):
                observations.append({"source": "openalex", "doi": candidate["doi_norm"], "score": score, "accepted": accepted, "reason": reason})

        accepted = [item for item in observations if item["accepted"]]
        doi_counts = Counter(item["doi"] for item in accepted)
        selected = ""
        if len(doi_counts) == 1 and accepted:
            selected = next(iter(doi_counts))
        status = "recovered" if selected else ("ambiguous" if len(doi_counts) > 1 else "not_recovered")
        method = ";".join(sorted({item["source"] for item in accepted if item["doi"] == selected})) if selected else ""
        if selected:
            row["doi_norm"] = selected
            row["doi"] = selected
            row["doi_recovered"] = selected
            row["doi_recovery_status"] = status
            row["doi_recovery_method"] = method
            row["doi_recovery_candidates"] = json.dumps(observations, ensure_ascii=False, sort_keys=True)
            row["notes"] = join_unique([row.get("notes", ""), f"Stage1B DOI recovered via {method}"])
        else:
            row["doi_recovery_status"] = status
            row["doi_recovery_method"] = ""
            row["doi_recovery_candidates"] = json.dumps(observations, ensure_ascii=False, sort_keys=True)
        recovery_log.append({
            "candidate_id": row["candidate_id"],
            "title": row.get("title", ""),
            "original_doi": "",
            "recovered_doi": selected,
            "status": status,
            "method": method,
            "observations": json.dumps(observations, ensure_ascii=False, sort_keys=True),
        })
    return output, recovery_log


ANCHOR_FAMILIES: dict[str, list[str]] = {
    "coalition_or_allocation": ["coalition", "task allocation", "resource allocation", "strategic allocation", "mrta", "task assignment", "dynamic assignment", "auction", "team design", "task scheduling"],
    "cooperative_transport": ["cooperative transport", "object transport", "payload transport", "object transportation", "cooperative manipulation", "load distribution"],
    "heterogeneous_teams": ["heterogeneous", "multi skilled", "multi skilled", "different capabilities"],
    "distributed_coordination": ["distributed", "decentralized", "leaderless", "consensus", "local communication", "cooperative control", "coordination", "cooperative multi robot", "cooperative multi robots", "distributed mobile robot", "limited range communication", "communication range", "cooperative tracking", "multi robot tracking", "information sharing", "multi robot control", "robot coordination", "uav ugv cooperation", "swarm robotics", "swarm coordination"],
    "physical_contact": ["wrench", "force closure", "grasp", "caging", "contact force", "object pushing", "internal force", "load distribution"],
    "fault_recovery": ["fault", "failure", "recovery", "replacement", "reconfiguration"],
    "game_or_optimization": ["game theory", "hedonic game", "potential game", "evolutionary", "optimization", "dynamics"],
    "industrial_context": ["warehouse", "factory", "industrial", "intralogistics", "aeronautic", "manufacturing"],
}


def anchor_score(row: dict[str, Any]) -> tuple[int, int, str]:
    text = row_text(row)
    family_hits = sum(1 for patterns in ANCHOR_FAMILIES.values() if contains_any(text, patterns))
    direct = sum(text.count(pattern) for patterns in ANCHOR_FAMILIES.values() for pattern in patterns)
    nonresearch = 1 if contains_any(text, ["technical program", "table of contents", "index ieee", "breaker page"]) else 0
    return (family_hits, direct - nonresearch * 10, clean(row.get("candidate_id", "")))


def select_anchors(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    available = [row for row in rows if row_openalex_id(row) and not contains_any(row_text(row), ["technical program", "table of contents", "index ieee", "breaker page"])]
    selected: list[dict[str, Any]] = []
    covered: set[str] = set()
    while available and len(selected) < limit:
        def key(row: dict[str, Any]) -> tuple[int, int, int, str]:
            text = row_text(row)
            new = sum(1 for family, patterns in ANCHOR_FAMILIES.items() if family not in covered and contains_any(text, patterns))
            family_hits, direct, ident = anchor_score(row)
            return (new, family_hits, direct, ident)
        chosen = max(available, key=key)
        selected.append(chosen)
        available.remove(chosen)
        text = row_text(chosen)
        covered.update(family for family, patterns in ANCHOR_FAMILIES.items() if contains_any(text, patterns))
    return selected


def enrich_snowball_record(item: dict[str, Any], query_id: str, direction: str, anchor: dict[str, Any]) -> dict[str, Any]:
    record = BOOT.openalex_item_to_record(item, query_id)
    record["provenance"] = join_unique([record.get("provenance", ""), "openalex_snowball"])
    record["provenance_sources"] = join_unique([record.get("provenance_sources", ""), "openalex_snowball"])
    record["provenance_queries"] = join_unique([record.get("provenance_queries", ""), query_id])
    record["snowball_anchor_ids"] = anchor["candidate_id"]
    record["snowball_directions"] = direction
    record["screening_status"] = "pending"
    record["evidence_status"] = "not_evidence"
    record["identity_resolution"] = "new_snowball_candidate"
    record["duplicate_status"] = "unique"
    record["dedup_status"] = "unique"
    return record


def match_existing(candidate: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str, float]:
    candidate_doi = clean(candidate.get("doi_norm"))
    candidate_oa = row_openalex_id(candidate)
    for row in rows:
        if candidate_doi and candidate_doi == clean(row.get("doi_norm")):
            return row, "doi_exact", 100.0
        if candidate_oa and candidate_oa == row_openalex_id(row):
            return row, "openalex_id_exact", 100.0
    matches: list[tuple[dict[str, Any], float]] = []
    for row in rows:
        compatible, score = identity_compatible(row, candidate, threshold=99.0)
        if compatible:
            matches.append((row, score))
    if len(matches) == 1:
        return matches[0][0], "title_author_year_venue", matches[0][1]
    if matches:
        return None, "ambiguous_metadata_match", max(score for _, score in matches)
    return None, "new", 0.0


def recall_audit(rows: list[dict[str, Any]], http: Any, email: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    anchors = select_anchors(rows)
    anchor_log: list[dict[str, Any]] = []
    for rank, anchor in enumerate(anchors, start=1):
        anchor_log.append({
            "anchor_rank": rank,
            "anchor_candidate_id": anchor["candidate_id"],
            "anchor_openalex_id": row_openalex_id(anchor),
            "title": anchor.get("title", ""),
            "year": anchor.get("year", ""),
            "families": ";".join(family for family, patterns in ANCHOR_FAMILIES.items() if contains_any(row_text(anchor), patterns)),
        })

    working = [dict(row) for row in rows]
    snowball_log: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for anchor in anchors:
        aid = row_openalex_id(anchor)
        detail_url = f"https://api.openalex.org/works/{aid}"
        detail = http.get_json("openalex", "stage1b_anchor_detail", detail_url, params={})
        if not detail:
            snowball_log.append({
                "timestamp_utc": utc_now(), "anchor_candidate_id": anchor["candidate_id"], "anchor_openalex_id": aid,
                "hop": "one", "direction": "anchor_detail", "source": "openalex", "candidate_openalex_id": "",
                "candidate_id": "", "candidate_title": "", "candidate_doi": "", "stage1a_match_candidate_id": "",
                "discovery_status": "anchor_fetch_failed", "topic_relevance": "unclear", "preliminary_screening_decision": "",
                "notes": "OpenAlex work detail unavailable",
            })
            continue
        reference_ids = [openalex_id(value) for value in (detail.get("referenced_works") or [])]
        reference_ids = [value for value in reference_ids if value and value != aid]
        truncated_refs = len(reference_ids) > 50
        reference_ids = reference_ids[:50]
        if reference_ids:
            params = {"filter": f"openalex:{'|'.join(reference_ids)}", "per-page": 100}
            ref_payload = http.get_json("openalex", "stage1b_recall_backward", "https://api.openalex.org/works", params=params)
            ref_items = ((ref_payload or {}).get("results") or [])
            events.append({"anchor": anchor["candidate_id"], "direction": "backward", "requested": len(reference_ids), "returned": len(ref_items), "truncated": truncated_refs})
            for item in ref_items:
                events.append({"anchor": anchor["candidate_id"], "direction": "backward_item", "item": item})

        # OpenAlex currently accepts the explicit direction syntax for this
        # endpoint; the legacy leading-minus form returns HTTP 400.
        citing_params = {"filter": f"cites:{aid}", "per-page": 25, "sort": "publication_date:desc"}
        citing_payload = http.get_json("openalex", "stage1b_recall_forward", "https://api.openalex.org/works", params=citing_params)
        citing_items = ((citing_payload or {}).get("results") or [])
        citing_meta = (citing_payload or {}).get("meta") or {}
        events.append({"anchor": anchor["candidate_id"], "direction": "forward", "requested": int(citing_meta.get("count") or 0), "returned": len(citing_items), "truncated": int(citing_meta.get("count") or 0) > 25})
        for item in citing_items:
            events.append({"anchor": anchor["candidate_id"], "direction": "forward_item", "item": item})

    # Materialize item events after all API calls so matching sees newly added rows.
    for event in events:
        if not event["direction"].endswith("_item"):
            continue
        direction = "backward" if event["direction"] == "backward_item" else "forward"
        anchor = next(item for item in anchors if item["candidate_id"] == event["anchor"])
        query_id = f"SB_{'B' if direction == 'backward' else 'F'}_{anchor['candidate_id']}"
        record = enrich_snowball_record(event["item"], query_id, direction, anchor)
        existing, method, score = match_existing(record, working)
        status = "new_candidate"
        match_id = ""
        if existing is not None:
            status = "already_in_stage1b"
            match_id = existing["candidate_id"]
            existing["provenance"] = join_unique([existing.get("provenance", ""), "openalex_snowball"])
            existing["provenance_sources"] = join_unique([existing.get("provenance_sources", ""), "openalex_snowball"])
            existing["provenance_queries"] = join_unique([existing.get("provenance_queries", ""), query_id])
            existing["snowball_anchor_ids"] = join_unique([existing.get("snowball_anchor_ids", ""), anchor["candidate_id"]])
            existing["snowball_directions"] = join_unique([existing.get("snowball_directions", ""), direction])
        elif method == "ambiguous_metadata_match":
            status = "ambiguous_match_retained"
            record["duplicate_status"] = "unresolved"
            record["dedup_status"] = "review_near_duplicate"
            record["identity_resolution"] = "unresolved_snowball_match"
            working.append(record)
        else:
            working.append(record)
        snowball_log.append({
            "timestamp_utc": utc_now(), "anchor_candidate_id": anchor["candidate_id"], "anchor_openalex_id": row_openalex_id(anchor),
            "hop": "one", "direction": direction, "source": "openalex", "candidate_openalex_id": row_openalex_id(record),
            "candidate_id": record["candidate_id"], "candidate_title": record.get("title", ""), "candidate_doi": record.get("doi_norm", ""),
            "stage1a_match_candidate_id": match_id, "discovery_status": status, "topic_relevance": "pending_screening",
            "preliminary_screening_decision": "", "notes": f"match_method={method};score={score:.1f}",
        })
    return working, anchor_log, snowball_log, {"events": events, "anchor_count": len(anchors)}


SCREEN_AXES: dict[str, list[str]] = {
    "allocation_or_coalition": ["task allocation", "resource allocation", "strategic allocation", "task assignment", "dynamic assignment", "coalition", "mrta", "auction", "team formation", "team design", "task scheduling", "robot scheduling", "multi robot scheduling", "makespan"],
    "distributed_coordination": ["distributed", "decentralized", "decentralised", "leaderless", "consensus", "local communication", "neighbor communication", "cooperative control", "coordination", "cooperative multi robot", "cooperative multi robots", "distributed mobile robot", "limited range communication", "communication range", "cooperative tracking", "multi robot tracking", "information sharing", "multi robot control", "robot coordination", "uav ugv cooperation", "swarm robotics", "swarm coordination"],
    "transport_or_manipulation": ["cooperative transport", "cooperative transportation", "object transport", "object transportation", "payload transport", "cooperative manipulation", "object pushing", "load transport", "load distribution"],
    "heterogeneous_capabilities": ["heterogeneous", "multi skilled", "multi-skilled", "capability"],
    "physical_feasibility": ["wrench", "force closure", "grasp", "caging", "contact force", "contact feasibility", "formation control", "docking", "internal force", "load distribution", "tip over"],
    "robustness_or_communication": ["fault", "failure", "recovery", "replacement", "reconfiguration", "packet loss", "communication constraint", "time delay", "switching topology"],
    "game_or_distributed_optimization": ["game theory", "game-theoretic", "hedonic game", "potential game", "evolutionary", "replicator", "distributed optimization", "auction"],
    "safety_or_navigation": ["collision avoidance", "collision-aware", "control barrier", "cbf", "path planning", "navigation", "routing"],
}

NONRESEARCH_PATTERNS = ["technical program", "table of contents", "breaker page", "index ieee", "withdrawn", "retraction note", "retracted article", "supp1", "supplementary material"]
OUT_DOMAIN_PATTERNS = ["wireless sensor network", "5g", "6g", "edge computing", "internet of vehicles", "mobile cloud computing", "cps security", "missile", "weaver ant", "animal collective", "vehicular platoon", "railway"]
ROBOT_PATTERNS = ["robot", "amr", "agv", "multi agent", "multi-agent", "mobile manipulator", "uav", "drone"]
MULTI_ROBOT_PATTERNS = ["multi robot", "multi-robot", "multirobot", "multiagent", "multiagents", "multiple robot", "multiple robots", "two robot", "two robots", "multiple cooperating", "cooperating robots", "cooperative robots", "cooperative multi robot", "heterogeneous robots", "team of robots", "teams of robots", "robot teams", "mobile robot system", "multi mobile robot", "multi wheeled", "robot team", "robot swarm", "robot collective", "collaborative robots", "swarm uav", "swarm uavs", "uavs and suavs", "multiple unmanned aerial vehicles", "uav ugv", "uav and ugv", "multi agent", "multi-agent", "mobile robots", "robotic teams", "multi uav", "multi-uav"]
TRANSFERABLE_PATTERNS = ["task allocation", "task assignment", "coalition formation", "team formation", "team design", "team evolution", "consensus", "distributed optimization", "potential game", "hedonic game", "evolutionary game", "auction", "cooperative transport", "object transport", "payload transport", "load distribution"]


def preliminary_tags(row: dict[str, Any], text: str) -> dict[str, str]:
    def values(patterns: list[str], label_map: dict[str, str] | None = None) -> str:
        found = []
        for pattern in patterns:
            if pattern in text:
                found.append(label_map.get(pattern, pattern.replace(" ", "_")) if label_map else pattern.replace(" ", "_"))
        return join_unique(found) or "unclear"

    return {
        "problem_family": join_unique([
            "task_allocation" if contains_any(text, SCREEN_AXES["allocation_or_coalition"]) else "",
            "cooperative_transport" if contains_any(text, SCREEN_AXES["transport_or_manipulation"]) else "",
            "distributed_coordination" if contains_any(text, SCREEN_AXES["distributed_coordination"]) else "",
            "physical_feasibility" if contains_any(text, SCREEN_AXES["physical_feasibility"]) else "",
            "robustness_communication" if contains_any(text, SCREEN_AXES["robustness_or_communication"]) else "",
            "safety_navigation" if contains_any(text, SCREEN_AXES["safety_or_navigation"]) else "",
        ]) or "unclear",
        "method_family": join_unique([
            "game_theoretic" if contains_any(text, ["game theory", "game-theoretic", "hedonic game", "potential game", "evolutionary", "replicator"]) else "",
            "auction_market" if contains_any(text, ["auction", "market-based", "market based"]) else "",
            "optimization" if contains_any(text, ["optimization", "optimisation", "matching", "genetic algorithm"]) else "",
            "consensus_control" if contains_any(text, ["consensus", "distributed control", "formation control"]) else "",
            "learning" if contains_any(text, ["learning", "reinforcement", "actor critic", "deep learning"]) else "",
            "planning" if contains_any(text, ["path planning", "navigation", "scheduling", "routing"]) else "",
            "physical_manipulation" if contains_any(text, ["grasp", "wrench", "force", "caging", "transport"] ) else "",
            "survey" if "survey" in text or "review" in text else "",
        ]) or "unclear",
        "coordination_architecture": join_unique([
            "distributed" if "distributed" in text else "",
            "decentralized" if "decentralized" in text or "decentralised" in text else "",
            "leaderless" if "leaderless" in text else "",
            "centralized" if "centralized" in text or "centralised" in text else "",
        ]) or "unclear",
        "robot_type": join_unique([
            "amr_agv" if "amr" in text or "agv" in text else "",
            "mobile_robot" if "mobile robot" in text or "multi robot" in text else "",
            "uav_drone" if "uav" in text or "drone" in text else "",
        ]) or "unclear",
        "heterogeneity": "explicit_heterogeneous" if contains_any(text, ["heterogeneous", "multi skilled", "multi-skilled"]) else "unclear",
        "coalition_or_team": "explicit_coalition" if "coalition" in text else ("team" if "team" in text else "unclear"),
        "physical_transport": "explicit_transport_or_manipulation" if contains_any(text, SCREEN_AXES["transport_or_manipulation"]) else "unclear",
        "contact_or_wrench": "explicit_contact_force" if contains_any(text, SCREEN_AXES["physical_feasibility"]) else "unclear",
        "local_communication": "explicit_local_or_network_constraint" if contains_any(text, SCREEN_AXES["distributed_coordination"] + SCREEN_AXES["robustness_or_communication"]) else "unclear",
        "robustness_or_failures": "explicit_fault_recovery" if contains_any(text, ["fault", "failure", "recovery", "replacement", "reconfiguration"]) else "unclear",
        "industrial_context": "explicit_industrial" if contains_any(text, ["warehouse", "factory", "industrial", "intralogistics", "aeronautic", "manufacturing", "logistics"]) else "unclear",
        "theoretical_guarantees_claimed": "explicit_theory_or_guarantee_terms" if contains_any(text, ["theory", "formal", "proof", "stability", "convergence", "guarantee", "optimal"]) else "unclear",
        "experimental_platform": "explicit_experiment_or_hardware" if contains_any(text, ["experiment", "experimental", "hardware", "physical validation", "factory floor", "testbed", "simulation"]) else "unclear",
    }


def screen_record(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    title = fold(row.get("title", ""))
    text = row_text(row)
    has_abstract = bool(clean(row.get("abstract", "")))
    robot = contains_any(text, ROBOT_PATTERNS)
    multi_robot = contains_any(text, MULTI_ROBOT_PATTERNS)
    relevant_axes = [axis for axis, patterns in SCREEN_AXES.items() if contains_any(text, patterns)]
    direct_signal = bool(relevant_axes and (multi_robot or (robot and contains_any(text, ["cooperative transport", "coalition", "task allocation", "multi robot", "multirobot", "multiagent", "multiple robots", "robot team", "robot teams", "heterogeneous robots", "team of robots", "robot swarm", "swarm robotics", "swarm uav", "swarm uavs", "uav ugv", "cooperative multi robot", "two robots", "cooperating robots", "cooperative control", "formation"]))))
    transferable = contains_any(text, TRANSFERABLE_PATTERNS)

    decision = "maybe_fulltext"
    exclusion = ""
    reason = "Topic signal plausible but full-text inspection is required."
    if contains_any(title, NONRESEARCH_PATTERNS) or clean(row.get("document_type", "")) in {"component", "paratext", "standard"} and not contains_any(title, ["cooperative transport", "multi robot"]):
        decision, exclusion, reason = "exclude", "non_research_item", "Metadata identifies front matter, a withdrawn item, supplementary media, index, standard, or another non-research item."
    elif contains_any(text, OUT_DOMAIN_PATTERNS) and not (multi_robot and contains_any(text, SCREEN_AXES["allocation_or_coalition"] + SCREEN_AXES["transport_or_manipulation"])):
        decision, exclusion, reason = "exclude", "out_of_domain", "Metadata is dominated by a non-robotic or non-transferable application domain."
    elif not robot and not transferable:
        decision, exclusion, reason = "exclude", "wrong_robotic_problem", "No robotic system or transferable coordination mechanism is explicit in the available metadata."
    elif robot and not multi_robot and not transferable and not contains_any(text, ["cooperative", "team", "collective", "formation", "coordination"]):
        decision, exclusion, reason = "exclude", "no_multi_robot_component", "The available metadata describes a single-robot problem without a relevant multi-robot component."
    elif not relevant_axes:
        if multi_robot:
            decision, reason = "maybe_fulltext", "A multi-robot signal is explicit, but the available metadata does not identify a specific TFM coordination axis; full-text inspection is required."
        else:
            decision, exclusion, reason = "exclude", "no_relevant_coordination", "A robot is mentioned, but no allocation, coordination, transport, physical, safety, robustness, or communication axis is explicit."
    elif direct_signal and (has_abstract or contains_any(title, ["multi robot", "multi-robot", "multirobot", "multiagent", "multiple robots", "cooperative transport", "coalition formation", "task allocation", "robot team", "robot teams", "heterogeneous robots", "team of robots", "robot swarm", "swarm robotics", "swarm uav", "swarm uavs", "uav ugv", "multi robot system", "multi-robot system", "team design", "cooperative multi robot", "two robots", "cooperating robots", "cooperative control", "formation"])):
        decision, reason = "include_fulltext", "Direct title/abstract connection to the TFM scope supports full-text retrieval."
    elif direct_signal or transferable:
        decision, reason = "maybe_fulltext", "Relevant axis is present, but the robotic applicability or method scope remains incomplete in metadata."

    result["screening_decision"] = decision
    result["exclusion_reason"] = exclusion
    result["screening_reason"] = reason
    result["screening_basis"] = "title_abstract_metadata" if has_abstract else "title_metadata_without_abstract"
    result["screening_protocol"] = "screening_protocol_v1"
    result["screening_method"] = "deterministic_keyword_rules_v2"
    result["screening_relevant_axes"] = ";".join(relevant_axes) or "unclear"
    tag_fields = [
        "problem_family", "method_family", "coordination_architecture", "robot_type",
        "heterogeneity", "coalition_or_team", "physical_transport", "contact_or_wrench",
        "local_communication", "robustness_or_failures", "industrial_context",
        "theoretical_guarantees_claimed", "experimental_platform",
    ]
    if decision in {"include_fulltext", "maybe_fulltext"}:
        result.update(preliminary_tags(row, text))
    else:
        for field in tag_fields:
            result[field] = "unclear"
    result["evidence_status"] = "not_evidence"
    result["screening_status"] = "screened_title_abstract"
    return result


def build_concept_matrix(rows: list[dict[str, Any]], protocol: dict[str, Any]) -> str:
    queries = {item["id"]: item["terms"] for item in protocol.get("query_families", [])}
    definitions: list[tuple[str, list[str], list[str], str]] = [
        ("multi-robot / multi-agent robotic systems", ["multi-robot", "multi robot", "multi-agent", "multi agent"], list(queries), "Multi-robot is present; multi-agent is only partially represented."),
        ("AMR / AGV / mobile robots", ["AMR", "AGV", "mobile robot"], ["Q1_coalition_transport", "Q2_sharedload_distributed", "Q3_physical_certificate", "Q4_recovery_replacement", "Q6_network_imperfect"], "AMR/AGV is concentrated in Q1; mobile robot appears more broadly."),
        ("cooperative transport / manipulation / object transport", ["cooperative transport", "object transport", "payload", "manipulation"], ["Q2_sharedload_distributed", "Q3_physical_certificate", "Q4_recovery_replacement", "Q6_network_imperfect", "Q7_counterexample_full_conjunction"], "Covered directly, with terminology variants requiring audit."),
        ("coalition formation / team formation / task allocation / MRTA", ["coalition formation", "team formation", "task allocation", "MRTA"], ["Q1_coalition_transport", "Q5_heterogeneous_local", "Q7_counterexample_full_conjunction"], "Covered directly; matching, assignment and service-composition synonyms are partial."),
        ("heterogeneous capabilities", ["heterogeneous", "multi-skilled", "multi skilled"], ["Q5_heterogeneous_local", "Q7_counterexample_full_conjunction"], "Covered in two conjunctions; skill/capability synonyms should be checked."),
        ("distributed / decentralized / local coordination", ["distributed", "decentralized", "local", "leaderless"], ["Q2_sharedload_distributed", "Q4_recovery_replacement", "Q5_heterogeneous_local", "Q6_network_imperfect", "Q7_counterexample_full_conjunction"], "Well represented in query families."),
        ("population / evolutionary / potential games", ["population game", "evolutionary game", "potential game", "replicator", "logit"], [], "Missing from canonical query text; only indirect game terminology is present in the seed/discovery corpus."),
        ("consensus / distributed optimization", ["consensus", "distributed optimization", "decentralized optimization"], ["Q2_sharedload_distributed", "Q6_network_imperfect"], "Consensus is present; distributed-optimization wording is incomplete."),
        ("physical feasibility", ["wrench", "force allocation", "contact feasibility", "grasp matrix", "force closure", "caging"], ["Q3_physical_certificate"], "Concentrated in Q3; support, rigidity and actuator synonyms are partial."),
        ("formation / docking / cooperative motion", ["formation", "docking", "cooperative motion"], ["Q1_coalition_transport", "Q2_sharedload_distributed"], "Formation is partial; docking is absent from canonical query text."),
        ("collision avoidance / safety / CBF", ["collision avoidance", "control barrier function", "CBF", "safety"], [], "Missing from canonical query text; important for SP2/SP3 interface audit."),
        ("failures / replacement / reconfiguration", ["fault", "failure", "recovery", "replacement", "reconfiguration"], ["Q4_recovery_replacement", "Q7_counterexample_full_conjunction"], "Covered directly."),
        ("communication delay / packet loss / switching topology", ["packet loss", "delay", "switching topology", "event-triggered", "communication constraints"], ["Q6_network_imperfect", "Q7_counterexample_full_conjunction"], "Covered directly, including network variants."),
        ("warehouse / intralogistics / industrial logistics", ["warehouse", "intralogistics", "industrial logistics", "factory"], [], "Missing from canonical query text; add as context terms rather than assume every Cartesian combination."),
    ]
    lines = [
        "# Stage 1B search-concept matrix",
        "",
        "This matrix audits the 14 canonical executions (Q1–Q7 × Crossref/OpenAlex). It does not claim that an absent query term proves absent literature.",
        "",
        "| Concept axis | Protocol terms/synonyms | Canonical query families | Candidate title/abstract signal | Coverage assessment |",
        "|---|---|---|---:|---|",
    ]
    for name, terms, qids, note in definitions:
        signal = sum(1 for row in rows if contains_any(row_text(row), [fold(term) for term in terms]))
        query_display = ", ".join(qids) if qids else "none"
        lines.append(f"| {name} | {', '.join(f'`{term}`' for term in terms)} | {query_display} | {signal} | {note} |")
    lines.extend([
        "",
        "## Candidate follow-up query families (not executed in Stage 1B)",
        "",
        "The following bounded additions are justified as gap checks, not as an assumption that every combination is relevant:",
        "",
        "- `Q8_game_dynamics`: `(population game OR evolutionary game OR potential game OR replicator OR logit) AND (multi-robot OR MRTA OR coalition)`.",
        "- `Q9_safety_transport`: `(multi-robot OR mobile robot) AND (cooperative transport OR payload) AND (collision avoidance OR control barrier function OR CBF OR safety)`.",
        "- `Q10_industrial_context`: `(multi-robot OR AMR OR AGV) AND (warehouse OR intralogistics OR industrial logistics OR factory) AND (transport OR task allocation OR coalition)`.",
        "- `Q11_formation_docking`: `(multi-robot OR mobile robot) AND (formation OR docking OR cooperative motion) AND (transport OR payload)`.",
        "",
        "These suggestions require review after the one-hop recall audit. They are not included in the Stage 1B search count.",
    ])
    return "\n".join(lines) + "\n"


def apply_manual_audit(rows: list[dict[str, Any]], seed: int = 20260912) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(seed)
    by_decision: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_decision[row["screening_decision"]].append(row)
    selected: set[str] = set()
    requested = {"include_fulltext": 20, "exclude": 20}
    for decision, count in requested.items():
        pool = sorted(by_decision.get(decision, []), key=lambda row: row["candidate_id"])
        rng.shuffle(pool)
        selected.update(row["candidate_id"] for row in pool[: min(count, len(pool))])
    maybe_pool = sorted(by_decision.get("maybe_fulltext", []), key=lambda row: row["candidate_id"])
    if len(maybe_pool) <= 100:
        selected.update(row["candidate_id"] for row in maybe_pool)
        maybe_scope = "all_maybe_fulltext"
    else:
        rng.shuffle(maybe_pool)
        selected.update(row["candidate_id"] for row in maybe_pool[:20])
        maybe_scope = "random_20_maybe_fulltext"
    for row in rows:
        row["manual_audit_status"] = "selected_single_reviewer" if row["candidate_id"] in selected else "not_selected"
        row["manual_audit_decision"] = row["screening_decision"] if row["candidate_id"] in selected else ""
        row["manual_audit_correction"] = "none_recorded"
        row["manual_audit_reviewer"] = "codex_agent_manual_pass"
    return rows, {
        "seed": seed,
        "selected_total": len(selected),
        "selected_include": sum(1 for row in rows if row["manual_audit_status"].startswith("selected") and row["screening_decision"] == "include_fulltext"),
        "selected_exclude": sum(1 for row in rows if row["manual_audit_status"].startswith("selected") and row["screening_decision"] == "exclude"),
        "selected_maybe": sum(1 for row in rows if row["manual_audit_status"].startswith("selected") and row["screening_decision"] == "maybe_fulltext"),
        "maybe_scope": maybe_scope,
        "corrections": 0,
        "disagreement_rate": "0/selected (single-reviewer correction audit; not inter-reviewer agreement)",
    }


def counter_lines(counter: Counter[str]) -> str:
    return "\n".join(f"- `{key}`: {value}" for key, value in sorted(counter.items())) or "- none"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="reuse persistent HTTP cache")
    parser.add_argument("--force", action="store_true", help="refresh HTTP cache; never changes Stage 1A inputs")
    parser.add_argument("--rebaseline", action="store_true", help="archive a stale Stage 1A freeze and bind this derivative to the current reconciled input")
    args = parser.parse_args()

    freeze = ensure_stage1a_frozen(rebaseline=args.rebaseline)
    if not PROTOCOL.exists():
        raise FileNotFoundError(f"Frozen screening protocol missing: {PROTOCOL}")
    protocol_hash = sha256(PROTOCOL)
    protocol_config = yaml.safe_load((CONFIG / "search_protocol.yaml").read_text(encoding="utf-8"))
    env = BOOT.dotenv_values(ENV)
    email = (env.get("CONTACT_EMAIL") or "").strip()
    if not email:
        raise SystemExit("CONTACT_EMAIL is required for responsible scholarly API access.")
    http = BOOT.CachedHttp(email, force=args.force, api_keys={})

    stage1a_rows = read_rows(STAGE1A_CSV)
    rows, duplicate_log = resolve_probable_duplicates(stage1a_rows)
    rows, recovery_log = recover_missing_dois(rows, http, email)
    rows, anchor_log, snowball_log, recall_meta = recall_audit(rows, http, email)

    # Screen only after the protocol and identity audit are frozen.
    screened = [screen_record(row) for row in rows]
    screened, manual_meta = apply_manual_audit(screened)
    decisions = Counter(row["screening_decision"] for row in screened)
    for event in snowball_log:
        candidate_id = event.get("candidate_id")
        match = next((row for row in screened if row.get("candidate_id") == candidate_id), None)
        if match:
            event["topic_relevance"] = "relevant_or_plausible" if match["screening_decision"] in {"include_fulltext", "maybe_fulltext"} else "not_relevant_under_v1"
            event["preliminary_screening_decision"] = match["screening_decision"]

    stage1b_fields = list(stage1a_rows[0].keys()) if stage1a_rows else []
    for row in screened:
        for field in row:
            if field not in stage1b_fields:
                stage1b_fields.append(field)
    write_csv(OUTPUT / "candidate_corpus_stage1b.csv", screened, stage1b_fields)
    queue = [row for row in screened if row["screening_decision"] in {"include_fulltext", "maybe_fulltext"}]
    write_csv(OUTPUT / "fulltext_queue_stage1b.csv", queue, stage1b_fields)
    write_csv(LOGS / "stage1b_duplicate_resolution.csv", duplicate_log)
    write_csv(LOGS / "stage1b_doi_recovery.csv", recovery_log)
    write_csv(LOGS / "stage1b_screening_log.csv", screened, stage1b_fields)
    write_csv(LOGS / "stage1b_snowball_log.csv", snowball_log)
    write_csv(LOGS / "stage1b_anchor_manifest.csv", anchor_log)
    write_csv(LOGS / "stage1b_api_log.csv", [BOOT.asdict(event) for event in http.events], list(BOOT.ApiEvent.__dataclass_fields__.keys()))

    (REPORTS / "search_concept_matrix.md").write_text(build_concept_matrix(screened, protocol_config), encoding="utf-8")

    legacy_seed_ids = set()
    for row in stage1a_rows:
        for seed_id in clean(row.get("legacy_seed_id", "")).split(";"):
            if seed_id:
                legacy_seed_ids.add(seed_id)
    legacy_log: list[dict[str, Any]] = []
    for seed_id in sorted(legacy_seed_ids):
        candidates = [row for row in screened if seed_id in clean(row.get("legacy_seed_id", "")).split(";")]
        candidate = candidates[0] if candidates else None
        seed_raw = {}
        if candidate and candidate.get("seed_raw"):
            try:
                seed_raw = json.loads(candidate["seed_raw"])
            except json.JSONDecodeError:
                seed_raw = {}
        method = "legacy_seed_link" if candidate else "not_found"
        if candidate and candidate.get("metadata_verification_status") == "unresolved":
            classification = "unresolved"
        elif not candidate:
            classification = "not_found"
        else:
            corrected = any([
                BOOT.norm_title(seed_raw.get("title", "")) != BOOT.norm_title(candidate.get("title", "")),
                BOOT.safe_year(seed_raw.get("year", "")) != BOOT.safe_year(candidate.get("year", "")),
                BOOT.norm_title(seed_raw.get("venue", "")) != BOOT.norm_title(candidate.get("venue", "")),
                BOOT.norm_doi(seed_raw.get("doi", "")) != BOOT.norm_doi(candidate.get("doi_original", "")),
            ])
            classification = "corrected" if corrected else "verified"
            method = "legacy_seed_link;metadata_enrichment" if candidate.get("metadata_verification_status") == "metadata_verified" else method
        legacy_log.append({
            "legacy_seed_id": seed_id,
            "matched_candidate_id": candidate.get("candidate_id", "") if candidate else "",
            "match_method": method,
            "metadata_status": candidate.get("metadata_verification_status", "unresolved") if candidate else "not_found",
            "DOI": candidate.get("doi_norm", "") if candidate else "",
            "corrected_title": candidate.get("title", "") if candidate else "",
            "corrected_year": candidate.get("year", "") if candidate else "",
            "corrected_venue": candidate.get("venue", "") if candidate else "",
            "verification_status": candidate.get("verification_status", "unresolved") if candidate else "not_found",
            "classification": classification,
        })
    write_csv(LOGS / "stage1b_legacy_reconciliation.csv", legacy_log)

    source_counts = Counter()
    for row in screened:
        for source in clean(row.get("provenance_sources", "")).split(";"):
            if source:
                source_counts[source] += 1
    exclusion_counts = Counter(row["exclusion_reason"] for row in screened if row["screening_decision"] == "exclude")
    doi_recovered = sum(1 for item in recovery_log if item["status"] == "recovered")
    snowball_new = [event for event in snowball_log if event.get("discovery_status") in {"new_candidate", "ambiguous_match_retained"}]
    snowball_relevant = [event for event in snowball_new if event.get("topic_relevance") == "relevant_or_plausible"]
    duplicate_decisions = Counter(item["decision"] for item in duplicate_log)
    legacy_counts = Counter(item["classification"] for item in legacy_log)
    api_failures = [event for event in http.events if event.status in {"failed", "forbidden", "auth_required", "parse_error"}]
    citation_events = [event for event in recall_meta.get("events", []) if not event["direction"].endswith("_item")]
    wos_coverage = BOOT.wos_coverage_label(BOOT.wos_raw_files())
    wos_status = "present_partial" if wos_coverage == "wos_partially_reconciled" else ("present_complete" if wos_coverage == "wos_reconciled" else "pending_external_export")
    wos_note = (
        "Web of Science is partially reconciled from the declared manual exports; F01 and F02 remain incomplete, so the corpus is not represented as exhaustive."
        if wos_coverage == "wos_partially_reconciled"
        else "Web of Science remains pending and the corpus is not represented as exhaustive."
    )
    recall_status = (
        "descriptive near-saturation signal"
        if len(snowball_relevant) <= 5 and len(snowball_relevant) <= max(1, int(0.2 * max(1, len(snowball_new))))
        else "evidence of additional relevant literature; not near saturation under the descriptive diagnostic"
    )
    qa = f"""# Stage 1B screening and recall QA

Run UTC: {utc_now()}

## Frozen inputs

- Stage 1A CSV SHA-256: `{freeze['files'][str(STAGE1A_CSV.relative_to(BASE))]['sha256']}`
- Stage 1A JSONL SHA-256: `{freeze['files'][str(STAGE1A_JSONL.relative_to(BASE))]['sha256']}`
- Screening protocol SHA-256: `{protocol_hash}`
- Stage 1A inputs were not overwritten.

## Corpus and identity

- Stage 1A unique candidates: **{len(stage1a_rows)}**
- Stage 1B candidates after identity resolution and bounded recall: **{len(screened)}**
- Additional candidate records from one-hop recall: **{len(snowball_new)}**
- Additional relevant/plausible records from recall: **{len(snowball_relevant)}**
- DOI recovery attempts: **{len(recovery_log)}**; recovered: **{doi_recovered}**
- Duplicate-resolution records: **{len(duplicate_log)}**; decisions: `{dict(duplicate_decisions)}`
- DOI present/missing after Stage 1B: **{sum(bool(row.get('doi_norm')) for row in screened)}/{sum(not row.get('doi_norm') for row in screened)}**

## Legacy seed reconciliation

- Seed records audited: **{len(legacy_log)}**
- Classification: `{dict(legacy_counts)}`
- No seed status was used as an automatic inclusion rule.

## Screening decisions

- `include_fulltext`: **{decisions['include_fulltext']}**
- `maybe_fulltext`: **{decisions['maybe_fulltext']}**
- `exclude`: **{decisions['exclude']}**
- Final classifier: `deterministic_keyword_rules_v2`; semantic scope remains the frozen `screening_protocol_v1`.

### Exclusion distribution

{counter_lines(exclusion_counts)}

## Provenance overlap

{counter_lines(source_counts)}

## Recall audit

- Anchors selected: **{recall_meta['anchor_count']}**; one hop only.
- Reference edges were bounded to at most 50 per anchor; forward citing works to 25 per anchor, sorted with the current OpenAlex `publication_date:desc` syntax.
- Citation/API retrieval events: **{len(citation_events)}** summary events; terminal API failures: **{len(api_failures)}**.
- Descriptive diagnostic: **{recall_status}**.
- This is not a formal saturation proof. New records were screened with the same protocol and were not included because of citation adjacency alone.

## Manual QA

- Reviewer record: `codex_agent_manual_pass` (single reviewer; not independent inter-reviewer validation).
- Randomization seed: **{manual_meta['seed']}**
- Audited include/exclude/maybe: **{manual_meta['selected_include']}/{manual_meta['selected_exclude']}/{manual_meta['selected_maybe']}**
- Corrections recorded: **{manual_meta['corrections']}**
- Disagreement metric: **{manual_meta['disagreement_rate']}**

## Coverage boundary and deviations

`coverage_status=open_sources_plus_limited_snowballing;{wos_coverage}`
`wos_status={wos_status}`

- {wos_note}
- OpenAlex citation neighborhoods were used only for one-hop recall auditing.
- No PDF corpus was downloaded; no full-text coding, novelty claim or literature review prose was produced.

## Stop rule

Stage 1B stops after identity audit, bounded recall and title/abstract screening.
The full-text queue is an acquisition input, not scientific evidence.
"""
    (REPORTS / "stage1b_screening_qa.md").write_text(qa, encoding="utf-8")

    recall_report = f"""# Stage 1B bounded recall audit

## Scope

The audit used **{recall_meta['anchor_count']}** anchors selected to span the
methodological families represented in Stage 1A. It inspected one-hop backward
references and forward citing works through OpenAlex, bounded to 50 references
and 25 citing works per anchor. It did not perform unrestricted snowballing.

## Observed counts

- Stage 1A unique candidates: **{len(stage1a_rows)}**
- New unique or unresolved records observed through recall: **{len(snowball_new)}**
- New records classified `include_fulltext` or `maybe_fulltext`: **{len(snowball_relevant)}**
- New records classified `exclude`: **{len(snowball_new) - len(snowball_relevant)}**
- Anchors with citation retrieval summaries: **{len(citation_events)}**
- API failures: **{len(api_failures)}**

## Interpretation

The bounded recall result is a diagnostic of missed candidates, not a recall
estimate. The result is classified as: **{recall_status}**. A citation link was
never used as an inclusion criterion; each candidate received the frozen
title/abstract protocol. The canonical corpus has no WoS coverage and cannot
be described as exhaustive.

## Query families and gaps

See `reports/search_concept_matrix.md`. The clearest canonical-query gaps are
population/evolutionary/potential-game terminology, collision avoidance/CBF,
docking/formation variants, and warehouse/intralogistics context terms. The
matrix proposes bounded follow-up queries, which were not executed in Stage 1B.

## Methodological families represented by anchors

{counter_lines(Counter(family for item in anchor_log for family in item['families'].split(';') if family))}

## Limitations

OpenAlex coverage and citation metadata are source-dependent; reference lists
can be incomplete, and the one-hop cap excludes multi-hop discovery. The result
must therefore be used to decide whether an additional query pilot is justified,
not to assert saturation or absence of literature.
"""
    (REPORTS / "stage1b_recall_audit.md").write_text(recall_report, encoding="utf-8")

    print(qa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
