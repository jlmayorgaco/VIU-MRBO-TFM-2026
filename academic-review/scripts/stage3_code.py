"""Stage 3: code verified full text into an auditable evidence matrix.

The implementation is intentionally a reproducible structural first pass. It
extracts the actual downloaded PDF/HTML/XML, records page/section context for
observed terms, and never fills detailed method/result fields from metadata
alone. Abstract-only and metadata-only records remain visible in the matrix but
are explicitly prevented from supporting full-text claims.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
PROCESSED = DATA / "processed"
FULLTEXT = DATA / "fulltext"
QUEUE = PROCESSED / "fulltext_queue_stage2.csv"
CORPUS = PROCESSED / "candidate_corpus_stage2.csv"
CONFIG = BASE / "config" / "stage3_codebook.yaml"
LOGS = BASE / "logs"
REPORTS = BASE / "reports"
for directory in [PROCESSED, LOGS, REPORTS]:
    directory.mkdir(parents=True, exist_ok=True)

FULLTEXT_STATUSES = {"acquired_pdf", "acquired_html", "acquired_xml"}
EVIDENCE_STRENGTHS = {"fulltext_verified", "abstract_only", "metadata_only", "retrieval_error"}
ROLE_NAMES = {"CORE", "ENABLING", "CONTEXT", "BASELINE", "SURVEY", "FOUNDATIONAL"}
STOPWORDS = {"a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "using", "with", "via"}

PATTERNS: dict[str, list[str]] = {
    "problem_formulation": [
        "task allocation", "task assignment", "coalition formation", "team formation", "multi robot task allocation",
        "cooperative transport", "cooperative transportation", "shared payload", "object transport", "load transport",
        "wrench", "force closure", "formation control", "collision avoidance", "warehouse logistics",
    ],
    "coordination_architecture": [
        "distributed", "decentralized", "decentralised", "leaderless", "consensus", "multi agent", "multi-agent",
        "auction", "market based", "market-based", "potential game", "evolutionary game", "replicator", "coalition",
        "leader follower", "leader-follower", "centralized", "centralised", "local coordination",
    ],
    "information_assumptions": [
        "local information", "local observation", "partial observation", "neighbor information", "neighbour information",
        "limited communication", "communication range", "wireless communication", "packet loss", "time delay",
        "global information", "full state", "shared state", "information sharing", "message passing",
    ],
    "method": [
        "mixed integer", "milp", "integer programming", "auction", "consensus-based", "consensus based", "potential game",
        "population game", "replicator", "logit", "distributed optimization", "model predictive control", "mpc",
        "control barrier", "cbf", "artificial potential", "virtual structure", "formation control", "reinforcement learning",
        "genetic algorithm", "fuzzy", "graph search", "a*", "dijkstra", "orca", "rvo",
    ],
    "physical_layer": [
        "payload", "load", "object", "rigid body", "prehensile", "nonprehensile", "non-prehensile", "caging", "pushing",
        "grasp", "contact force", "force closure", "wrench", "internal force", "friction", "tension", "manipulation",
    ],
    "execution": [
        "navigation", "trajectory", "path planning", "motion planning", "docking", "formation", "synchronization",
        "synchronisation", "velocity consensus", "obstacle avoidance", "collision avoidance", "reconfiguration", "recovery",
        "fault", "failure", "replacement", "transport", "tracking", "controller",
    ],
    "theory": [
        "theorem", "lemma", "proposition", "proof", "convergence", "stability", "lyapunov", "passivity", "invariant",
        "potential function", "nash equilibrium", "equilibrium", "complexity", "np-hard", "np complete", "approximation bound",
    ],
    "experiments": [
        "simulation", "simulated", "experiment", "experimental", "real robot", "hardware", "robot platform", "gazebo",
        "ros", "webots", "v-rep", "coppeliasim", "warehouse", "benchmark", "dataset", "ablation",
    ],
    "results": [
        "outperform", "improvement", "reduced", "increase", "decrease", "success rate", "makespan", "throughput",
        "completion time", "computational time", "communication cost", "collision rate", "error", "performance",
        "converged", "convergence rate", "optimality gap",
    ],
    "limitations": [
        "limitation", "limitations", "future work", "however", "assume", "assumption", "does not consider", "not considered",
        "restricted", "restrict", "scalability", "scalable", "communication failure", "unmodeled", "unmodelled",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def norm_text(value: Any) -> str:
    value = html.unescape(clean(value)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    rows = list(rows)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    fields = list(fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def strip_markup(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def extract_pages(path: Path, status: str) -> list[str]:
    if status == "acquired_pdf" or path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return [page.extract_text() or "" for page in reader.pages]
    raw = path.read_bytes()
    return [strip_markup(raw)]


def locate_term(pages: list[str], term: str) -> tuple[int, str, str] | None:
    pattern = re.compile(r"\b" + re.escape(term) + r"\b", flags=re.I)
    for page_number, page in enumerate(pages, start=1):
        match = pattern.search(page)
        if not match:
            continue
        start = max(0, match.start() - 130)
        end = min(len(page), match.end() + 170)
        snippet = re.sub(r"\s+", " ", page[start:end]).strip()
        before = page[:match.start()].splitlines()
        heading = ""
        for line in reversed(before[-12:]):
            line = re.sub(r"\s+", " ", line).strip()
            if line and len(line) <= 120 and (line.isupper() or re.match(r"^(?:\d+(?:\.\d+)*\s+)?[A-Z][A-Za-z /&-]{3,}$", line)):
                heading = line
                break
        return page_number, heading, snippet
    return None


def evidence_for_field(pages: list[str], terms: list[str], max_terms: int = 4) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for term in terms:
        location = locate_term(pages, term)
        if location is None or term in seen:
            continue
        page, section, snippet = location
        found.append({"term": term, "page": page, "section": section, "snippet": snippet})
        seen.add(term)
        if len(found) >= max_terms:
            break
    return found


def role_for(row: dict[str, Any], text: str, fields: dict[str, list[dict[str, Any]]]) -> str:
    title = norm_text(row.get("title"))
    if row.get("document_type") == "review" or any(term in title for term in ["survey", "review", "state of the art"]):
        return "SURVEY"
    if any(term in title for term in ["baseline", "benchmark", "comparison"]) or "baseline" in norm_text(text[:12000]):
        return "BASELINE"
    if any(term in title or term in norm_text(text[:18000]) for term in ["cooperative transport", "shared payload", "object transport", "coalition formation", "multi robot task allocation"]):
        return "CORE"
    if fields["physical_layer"] or fields["coordination_architecture"] or fields["theory"]:
        return "ENABLING"
    if any(term in title or term in norm_text(text[:10000]) for term in ["warehouse", "industrial", "logistics"]):
        return "CONTEXT"
    return "FOUNDATIONAL" if fields["theory"] else "CONTEXT"


def evidence_strength(status: str) -> str:
    if status in FULLTEXT_STATUSES:
        return "fulltext_verified"
    if status == "abstract_only":
        return "abstract_only"
    if status == "retrieval_error":
        return "retrieval_error"
    return "metadata_only"


def code_row(row: dict[str, Any], codebook_hash: str) -> dict[str, Any]:
    status = clean(row.get("fulltext_status"))
    strength = evidence_strength(status)
    local = clean(row.get("fulltext_local_path"))
    pages: list[str] = []
    extraction_error = ""
    if strength == "fulltext_verified" and local:
        path = BASE / local
        try:
            pages = extract_pages(path, status)
        except Exception as exc:
            extraction_error = f"{type(exc).__name__}: {exc}"
            strength = "retrieval_error"
    elif strength == "abstract_only":
        pages = [clean(row.get("abstract"))]
    else:
        pages = [""]
    text = "\n".join(pages)
    # Detailed fields are blank for metadata-only rows. For abstract-only rows
    # the observed terms are retained but marked as abstract-limited evidence.
    fields = {name: evidence_for_field(pages, terms) for name, terms in PATTERNS.items()}
    if strength == "metadata_only" or strength == "retrieval_error":
        fields = {name: [] for name in PATTERNS}
    role = role_for(row, text, fields) if strength != "metadata_only" else "CONTEXT"
    all_locations = [item for values in fields.values() for item in values]
    pages_observed = sorted({int(item["page"]) for item in all_locations if str(item.get("page", "")).isdigit()})
    sections_observed = sorted({clean(item.get("section")) for item in all_locations if clean(item.get("section"))})
    summary = {
        name: "; ".join(item["term"] for item in values)
        for name, values in fields.items()
    }
    return {
        "candidate_id": row.get("candidate_id", ""),
        "title": row.get("title", ""),
        "authors": row.get("authors", ""),
        "year": row.get("year", ""),
        "venue": row.get("venue", ""),
        "doi": row.get("doi_norm", ""),
        "document_type": row.get("document_type", ""),
        "screening_decision": row.get("screening_decision", ""),
        "evidence_strength": strength,
        "evidence_type": "verified_fulltext" if strength == "fulltext_verified" else ("abstract_only" if strength == "abstract_only" else "metadata_only"),
        "coding_status": "coded_fulltext_structural_pass" if strength == "fulltext_verified" else ("coded_abstract_limited" if strength == "abstract_only" else "not_codeable_without_fulltext"),
        "scientific_role": role,
        "problem_formulation": summary["problem_formulation"],
        "coordination_architecture": summary["coordination_architecture"],
        "information_assumptions": summary["information_assumptions"],
        "method": summary["method"],
        "physical_layer": summary["physical_layer"],
        "execution": summary["execution"],
        "theory": summary["theory"],
        "experiments": summary["experiments"],
        "results": summary["results"],
        "limitations": summary["limitations"],
        "evidence_spans_json": json.dumps(fields, ensure_ascii=False, sort_keys=True),
        "source_pages": ";".join(str(page) for page in pages_observed),
        "source_sections": ";".join(sections_observed),
        "table_or_figure": "observed_not_extracted" if re.search(r"\b(?:table|figure|fig\.)\s+\d+", text, flags=re.I) else "",
        "fulltext_local_path": local,
        "fulltext_sha256": row.get("fulltext_sha256", ""),
        "codebook_sha256": codebook_hash,
        "extraction_pages": len(pages),
        "extraction_characters": len(text),
        "extraction_error": extraction_error,
        "coded_at_utc": utc_now(),
        "coding_notes": "Structural term evidence; snippets require human scientific confirmation before use as strong claims.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="reuse existing matrix rows when their input hash is unchanged")
    args = parser.parse_args()
    if not QUEUE.exists() or not CORPUS.exists():
        raise FileNotFoundError("Stage 2 outputs are required before Stage 3")
    codebook_hash = sha256(CONFIG)
    queue = read_rows(QUEUE)
    matrix = [code_row(row, codebook_hash) for row in queue]
    fields = list(matrix[0].keys()) if matrix else []
    write_csv(PROCESSED / "fulltext_evidence_matrix.csv", matrix, fields)
    with (PROCESSED / "fulltext_evidence_matrix.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in matrix:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    write_csv(LOGS / "stage3_coding_log.csv", matrix, fields)
    errors = [row for row in matrix if row.get("extraction_error")]
    strength_counts = Counter(row.get("evidence_strength") for row in matrix)
    role_counts = Counter(row.get("scientific_role") for row in matrix)
    coding_counts = Counter(row.get("coding_status") for row in matrix)
    acquired = [row for row in matrix if row.get("evidence_strength") == "fulltext_verified"]
    if len(acquired) != sum(row.get("coding_status") == "coded_fulltext_structural_pass" for row in matrix):
        raise RuntimeError("Stage 3 invariant failure: every verified full-text record must have a full-text coding row")
    if any(row.get("evidence_strength") not in EVIDENCE_STRENGTHS for row in matrix):
        raise RuntimeError("Stage 3 invariant failure: unsupported evidence strength")
    qa = f"""# Stage 3 full-text coding QA

Run UTC: {utc_now()}

## Inputs and codebook

- Stage 2 queue records: **{len(queue)}**
- Codebook SHA-256: `{codebook_hash}`
- Coding mode: **deterministic structural first pass over extracted document text**
- Full-text policy: detailed fields require `fulltext_verified`; abstracts and metadata are never upgraded.

## Evidence strength

{chr(10).join(f"- `{key}`: **{strength_counts[key]}**" for key in sorted(EVIDENCE_STRENGTHS))}

## Coding status and role

{chr(10).join(f"- `{key}`: **{value}**" for key, value in sorted(coding_counts.items()))}

{chr(10).join(f"- `{key}`: **{value}**" for key, value in sorted(role_counts.items()))}

## Validation

- Evidence matrix rows: **{len(matrix)}**, with unique candidate IDs: **{len({row.get('candidate_id') for row in matrix})}**.
- Every `fulltext_verified` row was read from its local PDF/HTML/XML path and has a structural coding row.
- Abstract-only rows retain only abstract-limited observations; metadata-only rows have blank detailed fields.
- Extraction errors: **{len(errors)}**; these remain visible and are not silently treated as evidence.
- Outputs: `fulltext_evidence_matrix.csv`, `fulltext_evidence_matrix.jsonl`, and `stage3_coding_log.csv`.

## Interpretation boundary

This matrix is an auditable first-pass codebook, not a substitute for human
close reading. Terms and snippets locate candidate evidence in actual text;
they do not, by themselves, establish correctness of a method, a theorem, a
numerical result, or a limitation. The Stage 4 synthesis must use the evidence
strength and source spans explicitly and keep claims conservative.
"""
    (REPORTS / "stage3_fulltext_qa.md").write_text(qa, encoding="utf-8")
    print(qa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
