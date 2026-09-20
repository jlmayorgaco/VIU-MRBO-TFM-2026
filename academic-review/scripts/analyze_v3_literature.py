"""Generate conservative bibliometric and thematic analyses for V3.

The analytical corpus is the 244-item acquired reading queue. Topic, method,
architecture, application and validation signals are derived from titles and
locally extracted abstracts. Full-text term mentions are stored separately and
are never treated as proof that a method was implemented or validated.
"""

from __future__ import annotations

import csv
import hashlib
import html
import importlib.util
import json
import math
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
QUEUE = V3 / "data" / "priority_reading_queue_v3.csv"
AUDIT = V3 / "data" / "fulltext_adequacy_audit_v3.csv"

# Corrections are limited to bibliographic discrepancies checked against the
# version-of-record metadata. Keeping them here makes the derived chronology
# reproducible instead of silently editing generated CSV files.
YEAR_OVERRIDES = {
    "CF7C60AFD9DE7": "2022",  # De Ryck et al., J. Manufacturing Systems 62
}


THEMES = {
    "SP1_coalition_allocation": [r"coalition", r"task allocation", r"task assignment", r"role allocation", r"multi.robot team formation"],
    "SP2_physical_transport": [r"cooperative (object|payload|load) transport", r"collective transport", r"object transportation", r"payload transport", r"caging", r"non.prehensile", r"grasp", r"pushing", r"wrench", r"cooperative manipulation"],
    "SP3_planning_traffic": [r"multi.agent path finding", r"multi.robot path planning", r"traffic", r"congestion", r"collision avoidance", r"fleet management", r"routing", r"warehouse scheduling"],
    "TRANSVERSAL_resilience_communication": [r"fault toler", r"failure recovery", r"robot replacement", r"packet loss", r"communication", r"network delay", r"switching topology", r"resilien", r"scalab"],
}

METHODS = {
    "auction_market": [r"auction", r"market.based", r"contract net", r"consensus.based bundle", r"\bcbba\b"],
    "exact_optimization": [r"mixed.integer", r"integer linear", r"\bmilp\b", r"\bilp\b", r"branch.and.bound", r"set partition", r"linear programming"],
    "game_theoretic": [r"game.theoretic", r"potential game", r"coalitional game", r"hedonic", r"shapley", r"evolutionary game", r"population game", r"replicator dynamic", r"nash"],
    "evolutionary_metaheuristic": [r"genetic algorithm", r"\bnsga", r"particle swarm", r"ant colony", r"metaheuristic", r"evolutionary algorithm"],
    "learning_based": [r"reinforcement learning", r"deep learning", r"neural network", r"machine learning", r"multi.agent reinforcement"],
    "behavior_swarm": [r"behavior.based", r"behaviour.based", r"swarm robotics", r"stigmerg", r"pheromone", r"subsumption"],
    "consensus_distributed": [r"distributed optimization", r"distributed algorithm", r"decentralized", r"decentralised", r"consensus"],
    "model_predictive_control": [r"model predictive control", r"\bmpc\b"],
    "formation_control": [r"formation control", r"leader.follower", r"leaderless", r"virtual structure", r"rigidity"],
    "force_impedance_control": [r"force control", r"impedance control", r"admittance control", r"sliding mode", r"wrench distribution"],
    "safety_reactive": [r"control barrier function", r"\bcbf\b", r"velocity obstacle", r"\borca\b", r"reciprocal velocity", r"collision avoidance"],
    "graph_search_mapf": [r"conflict.based search", r"\bcbs\b", r"multi.agent path finding", r"\bmapf\b", r"a\*", r"dijkstra"],
}

ARCHITECTURES = {
    "centralized": [r"centralized", r"centralised", r"central coordinator", r"global information"],
    "distributed_decentralized": [r"distributed", r"decentralized", r"decentralised", r"peer.to.peer", r"neighbor", r"neighbour"],
    "leader_follower": [r"leader.follower", r"leader robot", r"master.slave"],
    "leaderless": [r"leaderless", r"without (a )?leader"],
    "hybrid": [r"hybrid (architecture|coordination|framework)", r"centralized.distributed", r"centralised.distributed"],
}

VALIDATION = {
    "simulation": [r"simulation", r"simulated", r"gazebo", r"webots", r"v.rep", r"coppeliasim", r"stage simulator"],
    "physical_experiment": [r"physical robot", r"real robot", r"experimental validation", r"hardware experiment", r"prototype", r"testbed"],
    "formal_analysis": [r"theorem", r"proof", r"lyapunov", r"stability analysis", r"convergence proof", r"complexity analysis"],
    "industrial_case": [r"industrial case", r"factory", r"warehouse", r"logistics", r"manufacturing"],
}

APPLICATIONS = {
    "warehouse_logistics": [r"warehouse", r"logistics", r"intralogistics", r"material handling", r"order picking"],
    "cooperative_transport_manipulation": [r"object transport", r"payload transport", r"collective transport", r"cooperative manipulation", r"shared load"],
    "aerial_uav": [r"\buav", r"aerial robot", r"drone", r"quadrotor"],
    "underwater_marine": [r"underwater", r"marine robot", r"auv"],
    "search_rescue_exploration": [r"search and rescue", r"exploration", r"reconnaissance", r"surveillance"],
    "construction_agriculture": [r"construction", r"agricultur", r"harvest", r"farm"],
}


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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_extractor() -> Any:
    source = BASE / "scripts" / "audit_v3_fulltexts.py"
    spec = importlib.util.spec_from_file_location("v3_analysis_extractor", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load extractor from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def abstract_from_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    matches = list(re.finditer(r"\babstract\b", normalized, flags=re.I))
    early_limit = min(15000, int(len(normalized) * 0.25))
    for match in [item for item in matches if item.start() <= early_limit][:3]:
        tail = normalized[match.end():match.end() + 7000]
        end = re.search(
            r"\b(?:1\s*[.]?\s*)?introduction\b|\bkeywords?\b|"
            r"this is a preview of subscription content|access this article|"
            r"access this chapter|\bcopyright\b",
            tail,
            flags=re.I,
        )
        candidate = tail[:end.start()] if end else tail[:3500]
        words = candidate.split()
        if 40 <= len(words) <= 500:
            return " ".join(words[:350])
    return ""


def body_without_references(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    matches = list(re.finditer(r"\b(?:references|bibliography)\b", normalized, flags=re.I))
    late = [match for match in matches if match.start() >= len(normalized) * 0.45]
    return normalized[:late[-1].start()] if late else normalized


def signals(text: str, vocabulary: dict[str, list[str]]) -> list[str]:
    normalized = normalize_text(text)
    return [label for label, patterns in vocabulary.items() if any(re.search(pattern, normalized, flags=re.I) for pattern in patterns)]


def period(year: str) -> str:
    try:
        number = int(year)
    except ValueError:
        return "unknown"
    if number <= 2010:
        return "<=2010"
    if number <= 2016:
        return "2011-2016"
    if number <= 2021:
        return "2017-2021"
    return "2022-2026"


def parse_authors(value: str) -> list[str]:
    if ";" in value:
        return [clean(item) for item in value.split(";") if clean(item)]
    if " and " in value.lower():
        return [clean(item) for item in re.split(r"\s+and\s+", value, flags=re.I) if clean(item)]
    return [clean(value)] if clean(value) else []


def canonical_venue(value: str) -> str:
    normalized = re.sub(r"\s+", " ", html.unescape(clean(value))).strip()
    aliases = {
        "ieee access": "IEEE Access",
        "journal of intelligent & robotic systems": "Journal of Intelligent & Robotic Systems",
        "journal of intelligent and robotic systems": "Journal of Intelligent & Robotic Systems",
        "lecture notes in computer science": "Lecture Notes in Computer Science",
        "frontiers in robotics and ai": "Frontiers in Robotics and AI",
        "robotics and autonomous systems": "Robotics and Autonomous Systems",
        "arxiv (cornell university)": "arXiv",
        "arxiv": "arXiv",
    }
    return aliases.get(normalized.casefold(), normalized)


def analyze_row(row: dict[str, str], audit: dict[str, str], extractor: Any) -> dict[str, str]:
    path = BASE / clean(row.get("fulltext_local_path"))
    raw_text = ""
    extraction_note = ""
    try:
        raw_text, _ = extractor.extract_text(path)
    except Exception as exc:
        extraction_note = f"{type(exc).__name__}: {exc}"
    abstract = abstract_from_text(raw_text) if raw_text else ""
    title_abstract = f"{clean(row.get('title'))}. {abstract}"
    body = body_without_references(raw_text)
    candidate_id = clean(row.get("candidate_id"))
    year = YEAR_OVERRIDES.get(candidate_id, clean(row.get("year")))
    return {
        "candidate_id": candidate_id,
        "title": clean(row.get("title")),
        "authors": clean(row.get("authors")),
        "year": year,
        "period": period(year),
        "venue": clean(row.get("venue")),
        "doi": clean(row.get("doi")),
        "document_type": clean(row.get("document_type")),
        "scientific_role_structural": clean(row.get("scientific_role_structural")),
        "priority_tier": clean(row.get("priority_tier")),
        "text_adequacy": clean(audit.get("v3_text_adequacy")),
        "close_reading_eligibility": clean(audit.get("close_reading_eligibility")),
        "abstract_extracted": abstract,
        "abstract_extracted_word_count": str(len(abstract.split())),
        "theme_signals_title_abstract": ";".join(signals(title_abstract, THEMES)) or "CONTEXT_other",
        "method_focus_title_abstract": ";".join(signals(title_abstract, METHODS)),
        "architecture_signals_title_abstract": ";".join(signals(title_abstract, ARCHITECTURES)),
        "validation_signals_title_abstract": ";".join(signals(title_abstract, VALIDATION)),
        "application_signals_title_abstract": ";".join(signals(title_abstract, APPLICATIONS)),
        "method_mentions_fulltext_not_implementation_evidence": ";".join(signals(body, METHODS)),
        "architecture_mentions_fulltext_not_implementation_evidence": ";".join(signals(body, ARCHITECTURES)),
        "validation_mentions_fulltext_not_implementation_evidence": ";".join(signals(body, VALIDATION)),
        "extraction_note": extraction_note,
        "coding_note": "Title/abstract signals support descriptive mapping only; full-text mentions do not prove implementation, guarantee or performance.",
    }


def explode_counts(rows: list[dict[str, str]], field: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(item for item in clean(row.get(field)).split(";") if item)
    return counts


def method_lifecycle(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for method in METHODS:
        years = sorted(int(row["year"]) for row in rows if row["year"].isdigit() and method in row["method_focus_title_abstract"].split(";"))
        bins = Counter(row["period"] for row in rows if method in row["method_focus_title_abstract"].split(";"))
        total = len(years)
        recent = bins["2022-2026"]
        if total >= 2 and years and years[0] >= 2020:
            status = "emerging_in_selected_corpus"
        elif total >= 3 and recent == 0:
            status = "legacy_no_recent_title_abstract_signal"
        elif total >= 3 and years and years[0] <= 2016 and recent > 0:
            status = "persistent_or_repurposed"
        else:
            status = "sparse_or_indeterminate"
        output.append({
            "method": method,
            "first_year": years[0] if years else "",
            "last_year": years[-1] if years else "",
            "total_title_abstract_signals": total,
            "count_le_2010": bins["<=2010"],
            "count_2011_2016": bins["2011-2016"],
            "count_2017_2021": bins["2017-2021"],
            "count_2022_2026": recent,
            "recent_share": f"{recent / total:.3f}" if total else "",
            "descriptive_status": status,
            "interpretation_limit": "Corpus signal, not proof that a method emerged, died, or dominates the field.",
        })
    return sorted(output, key=lambda item: (-int(item["total_title_abstract_signals"]), item["method"]))


def cooccurrence(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        labels = sorted(set(item for item in clean(row.get(field)).split(";") if item))
        counts.update(combinations(labels, 2))
    return [{"left": left, "right": right, "paper_count": count} for (left, right), count in counts.most_common()]


def category_by_period(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    periods = ["<=2010", "2011-2016", "2017-2021", "2022-2026", "unknown"]
    denominators = Counter(row["period"] for row in rows)
    categories = sorted({item for row in rows for item in clean(row.get(field)).split(";") if item})
    output: list[dict[str, Any]] = []
    for category in categories:
        for time_bin in periods:
            count = sum(row["period"] == time_bin and category in clean(row.get(field)).split(";") for row in rows)
            denominator = denominators[time_bin]
            output.append({
                "category": category,
                "period": time_bin,
                "paper_count": count,
                "period_denominator": denominator,
                "period_share": f"{count / denominator:.3f}" if denominator else "",
            })
    return output


def make_figures(rows: list[dict[str, str]], lifecycle: list[dict[str, Any]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    figures = V3 / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    yearly = Counter(int(row["year"]) for row in rows if row["year"].isdigit())
    years = list(range(min(yearly), max(yearly) + 1))
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(years, [yearly[year] for year in years], color="#2C7FB8")
    ax.set_xlabel("Año")
    ax.set_ylabel("Documentos en el corpus analítico")
    ax.set_title("Evolución temporal del corpus adquirido V3")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "annual_publications_v3.png", dpi=180)
    plt.close(fig)

    active = [row for row in lifecycle if int(row["total_title_abstract_signals"]) >= 2]
    labels = [row["method"].replace("_", " ") for row in active]
    periods = ["<=2010", "2011-2016", "2017-2021", "2022-2026"]
    keys = ["count_le_2010", "count_2011_2016", "count_2017_2021", "count_2022_2026"]
    fig, ax = plt.subplots(figsize=(11, max(4.8, len(active) * 0.45)))
    left = [0] * len(active)
    colors = ["#D9D9D9", "#A6CEE3", "#1F78B4", "#33A02C"]
    for label, key, color in zip(periods, keys, colors):
        values = [int(row[key]) for row in active]
        ax.barh(labels, values, left=left, label=label, color=color)
        left = [a + b for a, b in zip(left, values)]
    ax.set_xlabel("Documentos con señal en título/resumen")
    ax.set_title("Familias metodológicas por periodo (mapeo descriptivo)")
    ax.legend(frameon=False)
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(figures / "method_evolution_v3.png", dpi=180)
    plt.close(fig)


def main() -> None:
    queue = read_csv(QUEUE)
    audit = {clean(row.get("candidate_id")): row for row in read_csv(AUDIT)}
    extractor = load_extractor()
    with ThreadPoolExecutor(max_workers=12) as executor:
        rows = list(executor.map(lambda row: analyze_row(row, audit.get(clean(row.get("candidate_id")), {}), extractor), queue))
    corpus_path = V3 / "data" / "analytic_corpus_v3.csv"
    write_csv(corpus_path, rows, list(rows[0]))

    year_counts = Counter(row["year"] or "unknown" for row in rows)
    write_csv(V3 / "data" / "year_counts_v3.csv", [{"year": key, "count": value} for key, value in sorted(year_counts.items())], ["year", "count"])
    for name, field in {
        "theme_counts_v3.csv": "theme_signals_title_abstract",
        "method_counts_v3.csv": "method_focus_title_abstract",
        "architecture_counts_v3.csv": "architecture_signals_title_abstract",
        "validation_counts_v3.csv": "validation_signals_title_abstract",
        "application_counts_v3.csv": "application_signals_title_abstract",
    }.items():
        counts = explode_counts(rows, field)
        write_csv(V3 / "data" / name, [{"category": key, "paper_count": value, "denominator": len(rows), "share": f"{value / len(rows):.3f}"} for key, value in counts.most_common()], ["category", "paper_count", "denominator", "share"])

    authors: Counter[str] = Counter()
    coauthors: Counter[tuple[str, str]] = Counter()
    venues: Counter[str] = Counter()
    for row in rows:
        paper_authors = parse_authors(row["authors"])
        authors.update(paper_authors)
        coauthors.update(combinations(sorted(set(paper_authors)), 2))
        if row["venue"]:
            venues[canonical_venue(row["venue"])] += 1
    write_csv(V3 / "data" / "top_authors_v3.csv", [{"author": key, "paper_count": value} for key, value in authors.most_common()], ["author", "paper_count"])
    write_csv(V3 / "data" / "top_venues_v3.csv", [{"venue": key, "paper_count": value} for key, value in venues.most_common()], ["venue", "paper_count"])
    write_csv(V3 / "data" / "top_coauthor_pairs_v3.csv", [{"author_left": pair[0], "author_right": pair[1], "paper_count": count} for pair, count in coauthors.most_common()], ["author_left", "author_right", "paper_count"])
    lifecycle = method_lifecycle(rows)
    write_csv(V3 / "data" / "method_lifecycle_v3.csv", lifecycle, list(lifecycle[0]))
    pairs = cooccurrence(rows, "method_focus_title_abstract")
    write_csv(V3 / "data" / "method_cooccurrence_v3.csv", pairs, ["left", "right", "paper_count"])
    combinations_rows = Counter(row["theme_signals_title_abstract"] for row in rows)
    write_csv(V3 / "data" / "theme_combinations_v3.csv", [{"theme_combination": key, "paper_count": value} for key, value in combinations_rows.most_common()], ["theme_combination", "paper_count"])
    for filename, field in {
        "theme_period_v3.csv": "theme_signals_title_abstract",
        "method_period_v3.csv": "method_focus_title_abstract",
        "application_period_v3.csv": "application_signals_title_abstract",
    }.items():
        period_rows = category_by_period(rows, field)
        write_csv(V3 / "data" / filename, period_rows, ["category", "period", "paper_count", "period_denominator", "period_share"])
    make_figures(rows, lifecycle)

    methods = explode_counts(rows, "method_focus_title_abstract")
    themes = explode_counts(rows, "theme_signals_title_abstract")
    architectures = explode_counts(rows, "architecture_signals_title_abstract")
    validations = explode_counts(rows, "validation_signals_title_abstract")
    applications = explode_counts(rows, "application_signals_title_abstract")
    known_years = [int(row["year"]) for row in rows if row["year"].isdigit()]
    integrations = {
        "SP1+SP2": sum("SP1_coalition_allocation" in row["theme_signals_title_abstract"].split(";") and "SP2_physical_transport" in row["theme_signals_title_abstract"].split(";") for row in rows),
        "SP1+SP3": sum("SP1_coalition_allocation" in row["theme_signals_title_abstract"].split(";") and "SP3_planning_traffic" in row["theme_signals_title_abstract"].split(";") for row in rows),
        "SP2+SP3": sum("SP2_physical_transport" in row["theme_signals_title_abstract"].split(";") and "SP3_planning_traffic" in row["theme_signals_title_abstract"].split(";") for row in rows),
        "SP1+SP2+SP3": sum(all(label in row["theme_signals_title_abstract"].split(";") for label in ["SP1_coalition_allocation", "SP2_physical_transport", "SP3_planning_traffic"]) for row in rows),
    }
    report = V3 / "reports" / "advanced_mapping_results_v3.md"
    report.write_text(
        "# Advanced descriptive mapping results V3\n\n"
        "These are corpus-level title/abstract signals. They describe the acquired analytical set and do not establish method implementation, superiority, novelty or field-wide prevalence.\n\n"
        f"- Analytical records: {len(rows)}\n"
        f"- Date range: {min(known_years)}–{max(known_years)} ({sum(1 for row in rows if not row['year'].isdigit())} unknown year)\n"
        f"- Initially close-readable full texts: {sum(row['close_reading_eligibility'] == 'eligible' for row in rows)}\n"
        f"- Distinct parsed authors: {len(authors)}\n"
        f"- Distinct venues: {len(venues)}\n\n"
        "## Themes\n\n" + "\n".join(f"- `{key}`: {value}" for key, value in themes.most_common())
        + "\n\n## Method focus\n\n" + ("\n".join(f"- `{key}`: {value}" for key, value in methods.most_common()) or "- No method signal in title/abstract")
        + "\n\n## Architecture\n\n" + ("\n".join(f"- `{key}`: {value}" for key, value in architectures.most_common()) or "- No architecture signal")
        + "\n\n## Validation\n\n" + ("\n".join(f"- `{key}`: {value}" for key, value in validations.most_common()) or "- No validation signal")
        + "\n\n## Applications\n\n" + ("\n".join(f"- `{key}`: {value}" for key, value in applications.most_common()) or "- No application signal")
        + "\n\n## Cross-interface signals\n\n" + "\n".join(f"- `{key}`: {value}" for key, value in integrations.items())
        + "\n\n## Top authors in this corpus\n\n" + "\n".join(f"- {key}: {value}" for key, value in authors.most_common(20))
        + "\n\n## Recurrent coauthor pairs in this corpus\n\n" + "\n".join(f"- {left} + {right}: {value}" for (left, right), value in coauthors.most_common(20))
        + "\n\n## Top venues in this corpus\n\n" + "\n".join(f"- {key}: {value}" for key, value in venues.most_common(20))
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "queue_sha256": sha256(QUEUE),
        "audit_sha256": sha256(AUDIT),
        "analytic_corpus_sha256": sha256(corpus_path),
        "records": len(rows),
        "eligible_fulltexts": sum(row["close_reading_eligibility"] == "eligible" for row in rows),
        "coding_basis": "title_and_locally_extracted_abstract; fulltext mentions stored separately",
    }
    (V3 / "manifests" / "v3_analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(rows), "authors": len(authors), "venues": len(venues), "methods": dict(methods.most_common())}, sort_keys=True))


if __name__ == "__main__":
    main()
