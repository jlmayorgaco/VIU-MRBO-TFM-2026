"""Build a local SQLite database for systematic literature review screening."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "cooperative_transport": (
        "cooperative transport",
        "cooperative transportation",
        "payload",
        "object transport",
        "load transport",
        "multi-robot manipulation",
        "cooperative manipulation",
    ),
    "coalition_allocation": (
        "coalition",
        "task allocation",
        "task assignment",
        "auction",
        "market-based",
        "contract net",
        "resource allocation",
    ),
    "distributed_control": (
        "distributed control",
        "decentralized control",
        "consensus",
        "formation control",
        "networked control",
        "event-triggered",
    ),
    "graph_networks": (
        "graph",
        "laplacian",
        "connectivity",
        "topology",
        "networked systems",
        "algebraic connectivity",
    ),
    "game_theory": (
        "game theory",
        "potential game",
        "differential game",
        "mean field game",
        "stackelberg",
        "evolutionary game",
    ),
    "geometry_rigidity": (
        "rigid formation",
        "rigidity",
        "bearing",
        "geometry",
        "topological",
        "configuration space",
    ),
    "warehouse_agv": (
        "agv",
        "automated guided vehicle",
        "warehouse",
        "logistics",
        "fleet",
        "autonomous mobile robot",
    ),
    "learning_marl": (
        "multi-agent reinforcement learning",
        "marl",
        "ctde",
        "graph neural",
        "gnn",
        "learning",
    ),
}

HIGH_PRIORITY_TAGS = {
    "cooperative_transport",
    "coalition_allocation",
    "distributed_control",
    "game_theory",
    "geometry_rigidity",
    "warehouse_agv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=ROOT / "output" / "literature" / "arxiv_full",
        help="arXiv corpus directory produced by collect_arxiv_pdfs.py.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite output path. Defaults to <corpus-dir>/literature.sqlite.",
    )
    parser.add_argument(
        "--candidates-csv",
        type=Path,
        default=None,
        help="Screening candidate CSV. Defaults to <corpus-dir>/screening_candidates.csv.",
    )
    parser.add_argument(
        "--counts-csv",
        type=Path,
        default=None,
        help="Topic/year counts CSV. Defaults to <corpus-dir>/topic_year_counts.csv.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for smoke tests.")
    parser.add_argument("--hash-pdfs", action="store_true", help="Compute SHA-256 for every PDF.")
    parser.add_argument("--extract-text", action="store_true", help="Extract PDF text with pypdf.")
    parser.add_argument(
        "--extract-priority",
        choices=("high", "medium", "low", "all"),
        default="all",
        help="Priority subset for --extract-text.",
    )
    parser.add_argument(
        "--text-max-pages",
        type=int,
        default=8,
        help="Max pages per PDF for optional text extraction. Use 0 for all pages.",
    )
    parser.add_argument(
        "--text-dir",
        type=Path,
        default=None,
        help="Text output directory. Defaults to <corpus-dir>/text/by-id.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_dir = args.corpus_dir
    db_path = args.db or corpus_dir / "literature.sqlite"
    candidates_csv = args.candidates_csv or corpus_dir / "screening_candidates.csv"
    counts_csv = args.counts_csv or corpus_dir / "topic_year_counts.csv"
    text_dir = args.text_dir or corpus_dir / "text" / "by-id"

    rows = load_manifest_rows(corpus_dir, limit=args.limit)
    papers, topic_rows = merge_rows(rows, hash_pdfs=args.hash_pdfs)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        create_schema(conn)
        insert_papers(conn, papers)
        insert_topics(conn, topic_rows)
        insert_screening_defaults(conn, papers)
        if args.extract_text:
            extract_texts(
                conn,
                papers,
                text_dir,
                max_pages=args.text_max_pages,
                priority_filter=args.extract_priority,
            )
        create_fts(conn)

    candidates = build_candidates(papers)
    write_candidates(candidates_csv, candidates)
    write_counts(counts_csv, topic_rows)
    summary = {
        "db": str(db_path),
        "papers": len(papers),
        "topic_links": len(topic_rows),
        "candidates_csv": str(candidates_csv),
        "counts_csv": str(counts_csv),
        "extract_text": bool(args.extract_text),
    }
    (corpus_dir / "review_db_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def load_manifest_rows(corpus_dir: Path, *, limit: int | None) -> list[dict[str, str]]:
    manifest_paths = sorted((corpus_dir / "metadata" / "by-topic-year").rglob("manifest.csv"))
    if (corpus_dir / "manifest.csv").exists():
        manifest_paths.insert(0, corpus_dir / "manifest.csv")
    rows: list[dict[str, str]] = []
    seen_topic_rows: set[str] = set()
    for path in manifest_paths:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                key = "|".join(
                    [
                        row.get("arxiv_id", ""),
                        row.get("topic", ""),
                        row.get("query_year", ""),
                        row.get("pdf_path", ""),
                    ]
                )
                if key in seen_topic_rows:
                    continue
                seen_topic_rows.add(key)
                rows.append(row)
                if limit is not None and len(rows) >= limit:
                    return rows
    return rows


def merge_rows(
    rows: list[dict[str, str]],
    *,
    hash_pdfs: bool = False,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    papers: dict[str, dict[str, Any]] = {}
    topic_rows: list[dict[str, Any]] = []
    for row in rows:
        arxiv_id = row.get("arxiv_id", "").strip()
        if not arxiv_id:
            continue
        paper = papers.setdefault(arxiv_id, normalize_paper_row(row))
        paper["matched_topics"].update(split_semicolon(row.get("matched_topics", "")))
        paper["matched_topic_years"].update(split_semicolon(row.get("matched_topic_years", "")))
        topic = row.get("topic") or first_item(row.get("matched_topics", ""))
        query_year = row.get("query_year", "")
        published_year = row.get("published_year", "") or row.get("published", "")[:4]
        if topic:
            topic_rows.append(
                {
                    "arxiv_id": arxiv_id,
                    "topic": topic,
                    "query_year": query_year,
                    "published_year": published_year,
                    "topic_pdf_path": row.get("pdf_path", ""),
                    "download_status": row.get("download_status", ""),
                    "organization_status": row.get("organization_status", ""),
                }
            )
    for paper in papers.values():
        paper["matched_topics"] = sorted(paper["matched_topics"])
        paper["matched_topic_years"] = sorted(paper["matched_topic_years"])
        paper["topic_count"] = len(paper["matched_topics"])
        pdf_path = Path(str(paper.get("canonical_pdf_path") or ""))
        paper["has_pdf"] = int(pdf_path.exists())
        paper["pdf_sha256"] = sha256_file(pdf_path) if hash_pdfs and pdf_path.exists() else ""
    return papers, topic_rows


def normalize_paper_row(row: dict[str, str]) -> dict[str, Any]:
    canonical_pdf_path = row.get("canonical_pdf_path") or row.get("pdf_path", "")
    return {
        "arxiv_id": row.get("arxiv_id", ""),
        "version": row.get("version", ""),
        "title": row.get("title", ""),
        "authors": row.get("authors", ""),
        "published": row.get("published", ""),
        "updated": row.get("updated", ""),
        "published_year": row.get("published_year", "") or row.get("published", "")[:4],
        "primary_category": row.get("primary_category", ""),
        "categories": row.get("categories", ""),
        "doi": row.get("doi", ""),
        "journal_ref": row.get("journal_ref", ""),
        "comment": row.get("comment", ""),
        "abs_url": row.get("abs_url", ""),
        "pdf_url": row.get("pdf_url", ""),
        "canonical_pdf_path": canonical_pdf_path,
        "pdf_size_bytes": int_or_none(row.get("pdf_size_bytes")),
        "summary": row.get("summary", ""),
        "matched_topics": set(),
        "matched_topic_years": set(),
        "topic_count": 0,
        "has_pdf": 0,
        "pdf_sha256": "",
    }


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS papers (
            arxiv_id TEXT PRIMARY KEY,
            version TEXT,
            title TEXT,
            authors TEXT,
            published TEXT,
            updated TEXT,
            published_year TEXT,
            primary_category TEXT,
            categories TEXT,
            doi TEXT,
            journal_ref TEXT,
            comment TEXT,
            abs_url TEXT,
            pdf_url TEXT,
            canonical_pdf_path TEXT,
            pdf_size_bytes INTEGER,
            pdf_sha256 TEXT,
            has_pdf INTEGER,
            summary TEXT,
            matched_topics TEXT,
            matched_topic_years TEXT,
            topic_count INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS paper_topics (
            arxiv_id TEXT,
            topic TEXT,
            query_year TEXT,
            published_year TEXT,
            topic_pdf_path TEXT,
            download_status TEXT,
            organization_status TEXT,
            PRIMARY KEY (arxiv_id, topic, query_year),
            FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
        );

        CREATE TABLE IF NOT EXISTS screening (
            arxiv_id TEXT PRIMARY KEY,
            stage TEXT DEFAULT 'title_abstract',
            decision TEXT DEFAULT 'unscreened',
            priority TEXT,
            reason_code TEXT,
            reviewer TEXT,
            notes TEXT,
            updated_at TEXT,
            FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
        );

        CREATE TABLE IF NOT EXISTS text_extractions (
            arxiv_id TEXT PRIMARY KEY,
            text_path TEXT,
            text_chars INTEGER,
            text_pages INTEGER,
            extraction_status TEXT,
            extracted_at TEXT,
            FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
        );
        """
    )


def insert_papers(conn: sqlite3.Connection, papers: dict[str, dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """
        INSERT OR REPLACE INTO papers (
            arxiv_id, version, title, authors, published, updated, published_year,
            primary_category, categories, doi, journal_ref, comment, abs_url, pdf_url,
            canonical_pdf_path, pdf_size_bytes, pdf_sha256, has_pdf, summary,
            matched_topics, matched_topic_years, topic_count, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                paper["arxiv_id"],
                paper["version"],
                paper["title"],
                paper["authors"],
                paper["published"],
                paper["updated"],
                paper["published_year"],
                paper["primary_category"],
                paper["categories"],
                paper["doi"],
                paper["journal_ref"],
                paper["comment"],
                paper["abs_url"],
                paper["pdf_url"],
                paper["canonical_pdf_path"],
                paper["pdf_size_bytes"],
                paper["pdf_sha256"],
                paper["has_pdf"],
                paper["summary"],
                ";".join(paper["matched_topics"]),
                ";".join(paper["matched_topic_years"]),
                paper["topic_count"],
                now,
            )
            for paper in papers.values()
        ],
    )


def insert_topics(conn: sqlite3.Connection, topic_rows: list[dict[str, Any]]) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO paper_topics (
            arxiv_id, topic, query_year, published_year, topic_pdf_path,
            download_status, organization_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["arxiv_id"],
                row["topic"],
                row["query_year"],
                row["published_year"],
                row["topic_pdf_path"],
                row["download_status"],
                row["organization_status"],
            )
            for row in topic_rows
        ],
    )


def insert_screening_defaults(conn: sqlite3.Connection, papers: dict[str, dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """
        INSERT OR IGNORE INTO screening (
            arxiv_id, stage, decision, priority, reason_code, reviewer, notes, updated_at
        )
        VALUES (?, 'title_abstract', 'unscreened', ?, '', '', '', ?)
        """,
        [(paper["arxiv_id"], priority_for_paper(paper), now) for paper in papers.values()],
    )


def extract_texts(
    conn: sqlite3.Connection,
    papers: dict[str, dict[str, Any]],
    text_dir: Path,
    *,
    max_pages: int,
    priority_filter: str,
) -> None:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise SystemExit(f"pypdf is required for --extract-text: {exc}") from exc
    priorities = {
        arxiv_id: priority
        for arxiv_id, priority in conn.execute("SELECT arxiv_id, priority FROM screening")
    }
    rows = []
    for paper in papers.values():
        if priority_filter != "all" and priorities.get(paper["arxiv_id"]) != priority_filter:
            continue
        pdf_path = Path(str(paper.get("canonical_pdf_path") or ""))
        year = str(paper.get("published_year") or "unknown")
        target = text_dir / year / f"{safe_id(paper['arxiv_id'])}.txt"
        status = "missing_pdf"
        text = ""
        pages_read = 0
        if pdf_path.exists():
            try:
                reader = PdfReader(str(pdf_path))
                page_count = len(reader.pages)
                limit = page_count if max_pages == 0 else min(max_pages, page_count)
                chunks = []
                for page_index in range(limit):
                    chunks.append(reader.pages[page_index].extract_text() or "")
                text = "\n\n".join(chunks).strip()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
                pages_read = limit
                status = "ok"
            except Exception as exc:
                status = f"failed:{type(exc).__name__}"
        rows.append(
            (
                paper["arxiv_id"],
                str(target),
                len(text),
                pages_read,
                status,
                datetime.now(timezone.utc).isoformat(),
            )
        )
    conn.executemany(
        """
        INSERT OR REPLACE INTO text_extractions (
            arxiv_id, text_path, text_chars, text_pages, extraction_status, extracted_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def create_fts(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("DROP TABLE IF EXISTS papers_fts")
        conn.execute(
            """
            CREATE VIRTUAL TABLE papers_fts
            USING fts5(arxiv_id, title, summary, authors, matched_topics)
            """
        )
        conn.execute(
            """
            INSERT INTO papers_fts(arxiv_id, title, summary, authors, matched_topics)
            SELECT arxiv_id, title, summary, authors, matched_topics FROM papers
            """
        )
    except sqlite3.OperationalError:
        pass


def build_candidates(papers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for paper in papers.values():
        tags = keyword_tags(paper)
        score = relevance_score(paper, tags)
        candidates.append(
            {
                "priority": priority_for_score(score),
                "relevance_score": score,
                "tags": ";".join(tags),
                "arxiv_id": paper["arxiv_id"],
                "year": paper["published_year"],
                "title": paper["title"],
                "authors": paper["authors"],
                "primary_category": paper["primary_category"],
                "topics": ";".join(paper["matched_topics"]),
                "pdf_path": paper["canonical_pdf_path"],
                "abs_url": paper["abs_url"],
                "decision": "unscreened",
                "reason_code": "",
                "notes": "",
                "summary": paper["summary"],
            }
        )
    return sorted(candidates, key=lambda row: (-int(row["relevance_score"]), row["year"], row["title"]))


def write_candidates(path: Path, candidates: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "priority",
        "relevance_score",
        "tags",
        "arxiv_id",
        "year",
        "title",
        "authors",
        "primary_category",
        "topics",
        "pdf_path",
        "abs_url",
        "decision",
        "reason_code",
        "notes",
        "summary",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(candidates)


def write_counts(path: Path, topic_rows: list[dict[str, Any]]) -> None:
    counts = Counter((row["topic"], row["published_year"]) for row in topic_rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["topic", "published_year", "records"])
        writer.writeheader()
        for (topic, year), count in sorted(counts.items()):
            writer.writerow({"topic": topic, "published_year": year, "records": count})


def keyword_tags(paper: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            str(paper.get("title", "")),
            str(paper.get("summary", "")),
            " ".join(paper.get("matched_topics", [])),
        ]
    ).lower()
    tags = []
    for group, terms in KEYWORD_GROUPS.items():
        if any(term in text for term in terms):
            tags.append(group)
    return sorted(tags)


def relevance_score(paper: dict[str, Any], tags: list[str]) -> int:
    score = 2 * len(tags)
    score += sum(3 for tag in tags if tag in HIGH_PRIORITY_TAGS)
    topics = set(paper.get("matched_topics", []))
    if len(topics) > 1:
        score += min(5, len(topics))
    if "cs.RO" in str(paper.get("categories", "")):
        score += 3
    if "math.OC" in str(paper.get("categories", "")) or "eess.SY" in str(paper.get("categories", "")):
        score += 2
    return score


def priority_for_paper(paper: dict[str, Any]) -> str:
    return priority_for_score(relevance_score(paper, keyword_tags(paper)))


def priority_for_score(score: int) -> str:
    if score >= 13:
        return "high"
    if score >= 7:
        return "medium"
    return "low"


def split_semicolon(value: str) -> set[str]:
    return {item.strip() for item in str(value).split(";") if item.strip()}


def first_item(value: str) -> str:
    return next(iter(split_semicolon(value)), "")


def int_or_none(value: Any) -> int | None:
    try:
        text = str(value).strip()
        return int(text) if text else None
    except (TypeError, ValueError):
        return None


def safe_id(value: str) -> str:
    return value.replace("/", "_").replace("\\", "_")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
