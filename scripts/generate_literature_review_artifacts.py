"""Generate systematic literature review artifacts from the local review DB."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


CONCEPT_PATTERNS: dict[str, tuple[str, ...]] = {
    "cooperative_transport": (
        "cooperative transport",
        "cooperative transportation",
        "collective transport",
        "payload",
        "object transportation",
        "object transport",
        "load transport",
        "cooperative manipulation",
        "collaborative transport",
    ),
    "task_allocation_coalitions": (
        "task allocation",
        "task assignment",
        "coalition",
        "coalition formation",
        "cbba",
        "auction",
        "market",
        "bundle",
        "contract net",
    ),
    "distributed_control_consensus": (
        "distributed control",
        "decentralized control",
        "consensus",
        "event-triggered",
        "networked control",
        "distributed coordination",
        "local information",
    ),
    "formation_rigidity_geometry": (
        "formation control",
        "rigidity",
        "rigid formation",
        "bearing",
        "distance-based",
        "formation stabilization",
        "geometry",
        "shape formation",
    ),
    "graph_network_topology": (
        "graph",
        "laplacian",
        "topology",
        "connectivity",
        "voronoi",
        "network",
        "simplicial",
        "persistent homology",
    ),
    "game_theory_markets": (
        "game theory",
        "game-theoretic",
        "potential game",
        "stackelberg",
        "mean field",
        "evolutionary game",
        "payoff",
        "equilibrium",
        "replicator",
    ),
    "learning_marl_gnn": (
        "reinforcement learning",
        "multi-agent reinforcement learning",
        "marl",
        "q-learning",
        "graph neural",
        "gnn",
        "neural",
        "learning-based",
    ),
    "planning_mapf_navigation": (
        "path planning",
        "motion planning",
        "mapf",
        "multi-agent path finding",
        "navigation",
        "exploration",
        "coverage",
        "search and rescue",
    ),
    "warehouse_agv_logistics": (
        "warehouse",
        "agv",
        "automated guided vehicle",
        "autonomous mobile robot",
        "logistics",
        "manufacturing",
        "fleet",
    ),
    "robustness_safety_resilience": (
        "robust",
        "resilient",
        "fault",
        "attack",
        "safety",
        "barrier",
        "collision avoidance",
        "uncertainty",
        "disturbance",
    ),
    "communication_constraints": (
        "communication",
        "limited communication",
        "intermittent",
        "packet",
        "bandwidth",
        "message passing",
        "broadcast",
    ),
    "optimization_mpc": (
        "optimization",
        "model predictive control",
        "mpc",
        "mixed-integer",
        "convex",
        "subgradient",
        "primal-dual",
        "admm",
    ),
}

VALIDATION_PATTERNS: dict[str, tuple[str, ...]] = {
    "theory": ("theorem", "proof", "lyapunov", "stability", "convergence", "guarantee"),
    "simulation": ("simulation", "simulations", "numerical", "benchmark"),
    "real_robot": (
        "real robot",
        "real-robot",
        "hardware experiment",
        "physical experiment",
        "robot experiment",
        "robot experiments",
        "field trial",
        "real-world experiment",
        "experiments with real robots",
        "validated on robots",
    ),
    "open_source": (
        "open-source",
        "open source",
        "github",
        "source code",
        "code is available",
        "dataset is available",
        "publicly available",
    ),
    "survey": ("survey", "review", "overview", "tutorial"),
}

ARCHITECTURE_PATTERNS: dict[str, tuple[str, ...]] = {
    "distributed": ("distributed", "decentralized", "local information", "neighbor"),
    "centralized": ("centralized", "centralised", "central planner"),
    "hybrid": ("hybrid", "hierarchical", "leader", "macro-action", "centralized training"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT / "output" / "literature" / "arxiv_full" / "literature.sqlite",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "output" / "literature" / "arxiv_full" / "review",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=ROOT / "docs" / "literature" / "generated",
    )
    parser.add_argument("--top-n", type=int, default=40)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.docs_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    papers = [dict(row) for row in conn.execute("SELECT * FROM papers")]
    screening = {
        row["arxiv_id"]: dict(row)
        for row in conn.execute("SELECT * FROM screening")
    }
    text_info = {
        row["arxiv_id"]: dict(row)
        for row in conn.execute("SELECT * FROM text_extractions")
    }
    topic_rows = [dict(row) for row in conn.execute("SELECT * FROM paper_topics")]

    enriched = [enrich_paper(paper, screening.get(paper["arxiv_id"], {}), text_info.get(paper["arxiv_id"], {})) for paper in papers]
    high = [paper for paper in enriched if paper["priority"] == "high"]
    medium = [paper for paper in enriched if paper["priority"] == "medium"]
    low = [paper for paper in enriched if paper["priority"] == "low"]

    evidence_map = build_evidence_map(high)
    concept_counts = count_concepts(enriched)
    high_concept_counts = count_concepts(high)
    trends = trend_rows(enriched)
    author_rows = author_productivity(enriched)
    topic_year_summary = topic_year_rows(topic_rows)
    key_studies = sorted(high, key=lambda row: (-row["concept_score"], row["published_year"], row["title"]))[: args.top_n]

    write_csv(args.output_dir / "evidence_map_high_priority.csv", evidence_map)
    write_csv(args.output_dir / "concept_counts_all.csv", concept_counts)
    write_csv(args.output_dir / "concept_counts_high_priority.csv", high_concept_counts)
    write_csv(args.output_dir / "trend_by_year.csv", trends)
    write_csv(args.output_dir / "author_productivity.csv", author_rows)
    write_csv(args.output_dir / "topic_year_summary.csv", topic_year_summary)
    write_csv(args.output_dir / "key_studies.csv", key_studies)
    prisma_rows = draft_prisma_rows(papers, high, text_info)
    write_csv(args.output_dir / "prisma_flow_draft.csv", prisma_rows)

    report = render_report(
        papers=enriched,
        high=high,
        medium=medium,
        low=low,
        evidence_map=evidence_map,
        concept_counts=concept_counts,
        high_concept_counts=high_concept_counts,
        trends=trends,
        author_rows=author_rows,
        key_studies=key_studies,
        topic_rows=topic_rows,
        prisma_rows=prisma_rows,
    )
    report_path = args.docs_dir / "systematic_literature_review.md"
    report_path.write_text(report, encoding="utf-8")
    (args.output_dir / "systematic_literature_review.md").write_text(report, encoding="utf-8")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "papers": len(enriched),
        "high_priority": len(high),
        "medium_priority": len(medium),
        "low_priority": len(low),
        "report": str(report_path),
        "output_dir": str(args.output_dir),
    }
    (args.output_dir / "review_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def enrich_paper(paper: dict[str, Any], screening: dict[str, Any], text_info: dict[str, Any]) -> dict[str, Any]:
    text = text_for_paper(paper, text_info)
    haystack = normalize(" ".join([paper.get("title", ""), paper.get("summary", ""), text[:50000]]))
    concepts = [name for name, patterns in CONCEPT_PATTERNS.items() if any(pattern in haystack for pattern in patterns)]
    validations = [name for name, patterns in VALIDATION_PATTERNS.items() if any(pattern in haystack for pattern in patterns)]
    architectures = [name for name, patterns in ARCHITECTURE_PATTERNS.items() if any(pattern in haystack for pattern in patterns)]
    paper = dict(paper)
    paper["priority"] = screening.get("priority", "low")
    paper["concepts"] = concepts
    paper["validations"] = validations
    paper["architectures"] = architectures
    paper["concept_score"] = concept_score(paper, concepts, validations)
    paper["text_extraction_status"] = text_info.get("extraction_status", "")
    paper["text_chars"] = text_info.get("text_chars", "")
    return paper


def text_for_paper(paper: dict[str, Any], text_info: dict[str, Any]) -> str:
    path = Path(str(text_info.get("text_path", "")))
    if path.exists():
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
    return ""


def concept_score(paper: dict[str, Any], concepts: list[str], validations: list[str]) -> int:
    score = 2 * len(concepts) + len(validations)
    if "cs.RO" in str(paper.get("categories", "")):
        score += 3
    if "cooperative_transport" in concepts:
        score += 5
    if "task_allocation_coalitions" in concepts:
        score += 4
    if "distributed_control_consensus" in concepts:
        score += 4
    if "game_theory_markets" in concepts:
        score += 3
    if "formation_rigidity_geometry" in concepts:
        score += 3
    if "real_robot" in validations:
        score += 3
    if "theory" in validations:
        score += 2
    return score


def build_evidence_map(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for paper in sorted(papers, key=lambda row: (-row["concept_score"], row["published_year"], row["title"])):
        rows.append(
            {
                "arxiv_id": paper["arxiv_id"],
                "year": paper["published_year"],
                "title": paper["title"],
                "authors": paper["authors"],
                "primary_category": paper["primary_category"],
                "concepts": ";".join(paper["concepts"]),
                "validations": ";".join(paper["validations"]),
                "architectures": ";".join(paper["architectures"]),
                "concept_score": paper["concept_score"],
                "topics": paper["matched_topics"],
                "pdf_path": paper["canonical_pdf_path"],
                "abs_url": paper["abs_url"],
                "summary": paper["summary"],
            }
        )
    return rows


def count_concepts(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter()
    for paper in papers:
        counts.update(paper["concepts"])
    return [{"concept": concept, "records": count} for concept, count in counts.most_common()]


def trend_rows(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_year: dict[str, Counter[str]] = defaultdict(Counter)
    totals = Counter()
    for paper in papers:
        year = str(paper.get("published_year") or "unknown")
        totals[year] += 1
        by_year[year].update(paper["concepts"])
    concepts = list(CONCEPT_PATTERNS)
    rows = []
    for year in sorted(totals):
        row: dict[str, Any] = {"year": year, "records": totals[year]}
        for concept in concepts:
            row[concept] = by_year[year].get(concept, 0)
        rows.append(row)
    return rows


def author_productivity(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    author_counts: Counter[str] = Counter()
    high_counts: Counter[str] = Counter()
    concepts_by_author: dict[str, Counter[str]] = defaultdict(Counter)
    for paper in papers:
        authors = [author.strip() for author in str(paper.get("authors", "")).split(";") if author.strip()]
        for author in authors:
            author_counts[author] += 1
            if paper["priority"] == "high":
                high_counts[author] += 1
            concepts_by_author[author].update(paper["concepts"])
    rows = []
    for author, count in author_counts.most_common(50):
        rows.append(
            {
                "author": author,
                "records": count,
                "high_priority_records": high_counts.get(author, 0),
                "top_concepts": ";".join(concept for concept, _ in concepts_by_author[author].most_common(5)),
            }
        )
    return rows


def topic_year_rows(topic_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((row["topic"], row["published_year"]) for row in topic_rows)
    return [
        {"topic": topic, "year": year, "records": count}
        for (topic, year), count in sorted(counts.items())
    ]


def render_report(
    *,
    papers: list[dict[str, Any]],
    high: list[dict[str, Any]],
    medium: list[dict[str, Any]],
    low: list[dict[str, Any]],
    evidence_map: list[dict[str, Any]],
    concept_counts: list[dict[str, Any]],
    high_concept_counts: list[dict[str, Any]],
    trends: list[dict[str, Any]],
    author_rows: list[dict[str, Any]],
    key_studies: list[dict[str, Any]],
    topic_rows: list[dict[str, Any]],
    prisma_rows: list[dict[str, Any]],
) -> str:
    year_min = min(row["published_year"] for row in papers if row.get("published_year"))
    year_max = max(row["published_year"] for row in papers if row.get("published_year"))
    topic_count = len({row["topic"] for row in topic_rows})
    extracted = sum(1 for row in high if row.get("text_extraction_status") == "ok")
    top_concepts = high_concept_counts[:10]
    recent_rows = trends[-6:]
    lines = [
        "# Systematic literature review draft",
        "",
        f"Generated: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        "## Executive summary",
        "",
        (
            f"This review maps {len(papers)} unique arXiv records ({year_min}-{year_max}) "
            f"linked to {topic_count} search-topic slices. The triage layer identified "
            f"{len(high)} high-priority, {len(medium)} medium-priority, and {len(low)} "
            "low-priority records for the thesis question."
        ),
        "",
        (
            f"Full-text extraction was completed for {extracted} high-priority papers "
            "using the first pages of each PDF, while all records were classified from "
            "metadata, abstracts, and local topic labels. This is therefore a strong "
            "systematic mapping draft and a defensible starting point for a focused SLR, "
            "but not yet a final PRISMA review across IEEE/ACM/Scopus/Web of Science."
        ),
        "",
        "The evidence base is concentrated around distributed control, graph/network "
        "coordination, task allocation, cooperative transport, formation geometry, "
        "learning-based coordination, and warehouse/logistics robotics. The strongest "
        "thesis-relevant cluster is the intersection of multi-robot task allocation, "
        "coalition/payload constraints, distributed consensus/control, and cooperative "
        "transport.",
        "",
        "## Method",
        "",
        "The review follows the repository protocol in `docs/literature/systematic_review_protocol.md`. "
        "The search corpus was produced from arXiv API queries and organized by topic/year. "
        "Records were deduplicated by arXiv identifier, linked back to PDF paths, and inserted "
        "into `literature.sqlite`. Screening priority was assigned by transparent keyword rules "
        "over title, abstract, topic labels, and extracted text for high-priority records.",
        "",
        "The method intentionally separates three layers:",
        "",
        "1. Bibliographic corpus construction.",
        "2. Systematic mapping and triage.",
        "3. Focused full-text screening and evidence extraction.",
        "",
        "Only the first two layers and an initial high-priority full-text pass are complete in this draft.",
        "",
        "## Corpus profile",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| Unique records | {len(papers)} |",
        f"| High-priority records | {len(high)} |",
        f"| Medium-priority records | {len(medium)} |",
        f"| Low-priority records | {len(low)} |",
        f"| Topic/year links | {len(topic_rows)} |",
        f"| High-priority text extractions | {extracted} |",
        "",
        "### PRISMA-style flow draft",
        "",
        "| Stage | Records | Note |",
        "|---|---:|---|",
    ]
    for row in prisma_rows:
        lines.append(f"| {row['stage']} | {row['records']} | {escape_table(row['note'])} |")
    lines.extend(
        [
            "",
            "This is a PRISMA-style accounting table for the local arXiv corpus. It is not yet "
            "a final PRISMA flow diagram because non-arXiv databases and manual exclusion "
            "reasons have not been completed.",
            "",
        "### Dominant concepts in high-priority records",
        "",
        "| Concept | Records |",
        "|---|---:|",
        ]
    )
    for row in top_concepts:
        lines.append(f"| {label(row['concept'])} | {row['records']} |")
    lines.extend(
        [
            "",
            "### Recent growth pattern",
            "",
            "| Year | Records | Cooperative transport | Task allocation / coalitions | Distributed control | Learning / MARL / GNN | Robustness / safety |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in recent_rows:
        lines.append(
            "| {year} | {records} | {ct} | {ta} | {dc} | {lrn} | {rob} |".format(
                year=row["year"],
                records=row["records"],
                ct=row.get("cooperative_transport", 0),
                ta=row.get("task_allocation_coalitions", 0),
                dc=row.get("distributed_control_consensus", 0),
                lrn=row.get("learning_marl_gnn", 0),
                rob=row.get("robustness_safety_resilience", 0),
            )
        )
    lines.extend(
        [
            "",
            "## Thematic synthesis",
            "",
            "### 1. Distributed coordination is the organizing backbone",
            "",
            "The corpus shows that distributed and decentralized coordination remains the "
            "central architectural response to scale, communication limits, and robot-team "
            "heterogeneity. Classical consensus, event-triggered control, distributed "
            "optimization, and local-neighborhood policies appear repeatedly as mechanisms "
            "for replacing centralized assignment or planning. For the thesis, this supports "
            "a design stance in which allocation, quorum formation, and control should be "
            "expressed as local update laws rather than as a single monolithic optimizer.",
            "",
            "The strongest limitation is that many distributed-control papers prove convergence "
            "under idealized graph, sensing, or timing assumptions. That means they are useful "
            "for mathematical grounding, but must be filtered before being used as evidence "
            "for warehouse-scale cooperative transport.",
            "",
            "### 2. Cooperative transport is a multi-layer problem, not only a control problem",
            "",
            "High-priority transport papers consistently decompose the problem into coupled "
            "layers: task selection, robot coalition sizing, payload support geometry, path "
            "or trajectory generation, low-level tracking, and collision/communication "
            "constraints. Recent work on collective transport and assembly planning makes "
            "this explicit by combining task allocation, payload or subassembly constraints, "
            "geometric carrying configurations, and distributed execution.",
            "",
            "This directly motivates the TFM architecture: Smith-style population dynamics or "
            "market dynamics can handle allocation pressure, but they need a second layer that "
            "turns fractional or preference-like decisions into physically feasible robot "
            "coalitions and rigid/contact formations.",
            "",
            "### 3. Coalition formation and MRTA are the closest allocation literature",
            "",
            "The most thesis-relevant allocation literature lies around MRTA, CBBA-like consensus "
            "bundle methods, auctions/markets, coalition formation, and resource allocation. "
            "These methods are valuable because they already formalize scarce robots, task "
            "demands, changing payloads, and local communication. However, many MRTA papers "
            "stop at assignment and do not model the wrench, rigid formation, or contact "
            "feasibility layer needed for cooperative load transport.",
            "",
            "A useful gap statement is therefore: the literature often treats task allocation "
            "and cooperative transport control as adjacent but separate layers; fewer papers "
            "close the loop between distributed allocation, integer coalition feasibility, "
            "and physical formation/load constraints.",
            "",
            "### 4. Graph theory is the common language between communication, formation, and allocation",
            "",
            "Graph concepts appear in three roles. First, communication graphs encode who can "
            "exchange information. Second, rigidity and bearing/distance graphs encode whether "
            "a formation shape can be maintained. Third, task or environment graphs encode "
            "warehouse topology, exploration frontiers, or allocation structure. This is one "
            "of the strongest bridges for the thesis because it allows a single mathematical "
            "language to relate network connectivity, quorum construction, and formation "
            "validity.",
            "",
            "The review also indicates a risk: generic graph/network papers can be mathematically "
            "interesting but weakly transferable. They should be used only when their assumptions "
            "map clearly to robot communication, formation, or warehouse-task graphs.",
            "",
            "### 5. Game theory and market dynamics are useful when scarcity and incentives matter",
            "",
            "Game-theoretic papers contribute useful mechanisms for distributed resource allocation, "
            "payoff shaping, potential games, Stackelberg interactions, evolutionary dynamics, "
            "and mean-field abstractions. Their relevance is strongest when the robot team faces "
            "scarce capacity, heterogeneous costs, or competing task demands. This maps well to "
            "the Smith-QR direction because Smith dynamics can be interpreted as population/game "
            "dynamics over task alternatives.",
            "",
            "The evidence is less direct for physical transport. Many game-theoretic models are "
            "abstract and require an explicit bridge from payoff definitions to measurable robot "
            "quantities such as wrench deficit, travel cost, communication load, queue pressure, "
            "or payload risk.",
            "",
            "### 6. Learning methods are growing, but they do not replace structure",
            "",
            "MARL, graph neural networks, and learned decentralized policies appear strongly in "
            "recent high-priority records. The most relevant papers use learning to improve "
            "scalability, transfer, or local decision policies, often with graph encoders or "
            "hierarchical task-priority structures. The recurring pattern is not pure end-to-end "
            "learning, but structured learning: learning is embedded inside task allocation, "
            "message passing, graph abstraction, or hierarchical control.",
            "",
            "For the TFM, this suggests MARL should be treated as a comparator or extension, not "
            "as the core explanatory mechanism. A hand-designed distributed mechanism remains "
            "more auditable for thesis validation, while learning-based methods can benchmark "
            "adaptability under changing team size, object weights, and communication constraints.",
            "",
            "### 7. Robustness, safety, and communication are under-integrated",
            "",
            "Robustness appears through resilient consensus, fault/attack models, H-infinity or "
            "Lyapunov arguments, safety-critical control, collision avoidance, and communication "
            "constraints. However, the evidence map suggests these are often treated as separate "
            "problem families rather than integrated with transport allocation and formation.",
            "",
            "This is a defensible research gap for the thesis: a complete cooperative-transport "
            "architecture should jointly handle allocation scarcity, communication degradation, "
            "coalition closure, formation/contact feasibility, and robustness metrics.",
            "",
            "## Key high-priority studies",
            "",
            "| Year | arXiv | Study | Main concepts | Validation signals |",
            "|---:|---|---|---|---|",
        ]
    )
    for paper in key_studies[:25]:
        lines.append(
            "| {year} | {arxiv} | {title} | {concepts} | {validations} |".format(
                year=paper["published_year"],
                arxiv=paper["arxiv_id"],
                title=escape_table(shorten(paper["title"], 90)),
                concepts=escape_table(", ".join(label(item) for item in paper["concepts"][:4])),
                validations=escape_table(", ".join(label(item) for item in paper["validations"][:4])),
            )
        )
    lines.extend(
        [
            "",
            "## Author and community signals",
            "",
            "The author-productivity table should not be interpreted as impact ranking, because "
            "the corpus is arXiv-first and query-dependent. It is useful for identifying recurring "
            "research groups for citation chasing.",
            "",
            "| Author | Records | High-priority records | Main concepts |",
            "|---|---:|---:|---|",
        ]
    )
    for row in author_rows[:15]:
        lines.append(
            f"| {escape_table(row['author'])} | {row['records']} | {row['high_priority_records']} | {escape_table(row['top_concepts'])} |"
        )
    lines.extend(
        [
            "",
            "## Evidence gaps",
            "",
            "1. Integrated allocation-control gap: many papers solve assignment, consensus, or formation separately; fewer close the loop from allocation pressure to integer coalition closure and physical load feasibility.",
            "2. Physical feasibility gap: MRTA and market papers often do not model payload wrench, contact geometry, or rigid formation constraints.",
            "3. Communication realism gap: many distributed methods assume graph connectivity conditions that are cleaner than warehouse communication degradation.",
            "4. Evaluation gap: real-robot and open-source validations are present but much less frequent than simulations and theoretical demonstrations.",
            "5. Reproducibility gap: several papers report algorithms without enough code/data availability to support benchmark-level comparison.",
            "6. Learning-structure gap: learning methods scale well in some settings, but often require structured priors or retraining to transfer across robot count, object count, and payload distributions.",
            "",
            "## Implications for the TFM",
            "",
            "The review supports positioning Smith-QR as a layered distributed coordination architecture. Its most defensible novelty is not simply using distributed control or game dynamics, but integrating: allocation pressure, coalition closure, quorum feasibility, formation/contact constraints, and robustness evaluation under communication and resource degradation.",
            "",
            "The strongest comparison baselines should come from: CBBA/consensus bundle allocation, decentralized or distributed control, MARL/graph-learning transport policies, centralized or mixed-integer allocation/planning, and classic greedy warehouse dispatching.",
            "",
            "The thesis should avoid claiming that game theory alone solves cooperative transport. A stronger claim is that population/game dynamics provide an interpretable allocation layer that becomes useful when coupled to graph/quorum and physical feasibility mechanisms.",
            "",
            "## Limitations of this draft",
            "",
            "This document is generated from an arXiv-first local corpus. It is not yet a final PRISMA-complete review because IEEE Xplore, ACM Digital Library, Scopus/Web of Science, and backward/forward citation chasing have not been integrated. The candidate screening is a transparent keyword-based triage aid, not a substitute for final reviewer decisions. Full-text extraction was limited to high-priority records and to the first pages of each PDF.",
            "",
            "## Generated artifacts",
            "",
            "- `output/literature/arxiv_full/review/evidence_map_high_priority.csv`",
            "- `output/literature/arxiv_full/review/concept_counts_all.csv`",
            "- `output/literature/arxiv_full/review/concept_counts_high_priority.csv`",
            "- `output/literature/arxiv_full/review/trend_by_year.csv`",
            "- `output/literature/arxiv_full/review/author_productivity.csv`",
            "- `output/literature/arxiv_full/review/key_studies.csv`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def draft_prisma_rows(
    papers: list[dict[str, Any]],
    high: list[dict[str, Any]],
    text_info: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    extracted = sum(1 for row in text_info.values() if row.get("extraction_status") == "ok")
    missing = sum(1 for row in text_info.values() if row.get("extraction_status") == "missing_pdf")
    return [
        {
            "stage": "Records identified from local arXiv corpus",
            "records": len(papers),
            "note": "Deduplicated by arXiv identifier from available topic/year manifests.",
        },
        {
            "stage": "Records prioritized for title/abstract screening",
            "records": len(high),
            "note": "High-priority triage based on transparent keyword and topic rules.",
        },
        {
            "stage": "Reports retrieved for full-text triage",
            "records": extracted,
            "note": "PDF text extracted for high-priority records.",
        },
        {
            "stage": "Reports not retrieved",
            "records": missing,
            "note": "High-priority records without an available local PDF at extraction time.",
        },
        {
            "stage": "Studies included in narrative synthesis draft",
            "records": len(high),
            "note": "Provisional inclusion for mapping; final inclusion requires manual reason-coded screening.",
        },
    ]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def label(value: str) -> str:
    return value.replace("_", " ")


def shorten(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."


def escape_table(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
