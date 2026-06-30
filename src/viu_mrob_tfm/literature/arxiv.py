"""arXiv metadata and PDF collection helpers.

The functions in this module intentionally use only the Python standard library
for HTTP and XML handling. That keeps the literature collector usable from a
fresh editable install of this project.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import yaml


ARXIV_API_URL = "https://export.arxiv.org/api/query"
DEFAULT_USER_AGENT = "viu-mrob-tfm-literature-collector/0.1"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


@dataclass(frozen=True)
class ArxivTopic:
    """A named arXiv query used to build a literature slice."""

    name: str
    query: str
    max_results: int | None = None


@dataclass(frozen=True)
class ArxivPaper:
    """Metadata needed to review and download one arXiv paper."""

    arxiv_id: str
    version: str | None
    title: str
    authors: tuple[str, ...]
    summary: str
    published: str
    updated: str
    primary_category: str
    categories: tuple[str, ...]
    abs_url: str
    pdf_url: str
    doi: str | None = None
    journal_ref: str | None = None
    comment: str | None = None

    def bibtex_key(self) -> str:
        """Return a stable, human-readable BibTeX key."""

        author = "anon"
        if self.authors:
            author = slugify(self.authors[0].split()[-1], max_length=24) or "anon"
        year = self.published[:4] if len(self.published) >= 4 else "nd"
        suffix = self.arxiv_id.replace("/", "_").replace(".", "")
        return f"{author}{year}arxiv{suffix}"


def load_topics(path: str | Path) -> list[ArxivTopic]:
    """Load literature topics from a YAML configuration file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    raw_topics = data.get("topics", [])
    topics: list[ArxivTopic] = []
    for item in raw_topics:
        name = str(item["name"]).strip()
        query = str(item["query"]).strip()
        max_results = item.get("max_results")
        topics.append(
            ArxivTopic(
                name=name,
                query=query,
                max_results=int(max_results) if max_results is not None else None,
            )
        )
    if not topics:
        raise ValueError(f"No topics found in {path}")
    return topics


def build_api_url(
    query: str,
    *,
    start: int = 0,
    max_results: int = 100,
    sort_by: str = "relevance",
    sort_order: str = "descending",
) -> str:
    """Build one arXiv API URL."""

    params = {
        "search_query": query,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    return f"{ARXIV_API_URL}?{urlencode(params)}"


def build_submitted_date_query(query: str, year: int) -> str:
    """Constrain an arXiv query to papers submitted during one calendar year."""

    return f"({query}) AND submittedDate:[{year}01010000 TO {year}12312359]"


def fetch_atom_page(
    query: str,
    *,
    start: int,
    max_results: int,
    timeout_seconds: float,
    user_agent: str,
    retries: int = 3,
    sort_by: str = "relevance",
    sort_order: str = "descending",
) -> str:
    """Fetch a raw arXiv Atom page."""

    url = build_api_url(
        query,
        start=start,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    request = Request(url, headers={"User-Agent": user_agent})
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(30.0, 2.0 * attempt))
    if last_error is not None:
        raise last_error
    raise RuntimeError("arXiv request failed without an exception")


def iter_arxiv_papers(
    query: str,
    *,
    max_results: int,
    batch_size: int = 100,
    pause_seconds: float = 3.1,
    timeout_seconds: float = 60.0,
    user_agent: str = DEFAULT_USER_AGENT,
    retries: int = 3,
    sort_by: str = "relevance",
    sort_order: str = "descending",
) -> Iterable[ArxivPaper]:
    """Yield papers from an arXiv query using paginated API requests."""

    start = 0
    yielded = 0
    while yielded < max_results:
        page_size = min(batch_size, max_results - yielded)
        xml_text = fetch_atom_page(
            query,
            start=start,
            max_results=page_size,
            timeout_seconds=timeout_seconds,
            user_agent=user_agent,
            retries=retries,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        papers = parse_atom_feed(xml_text)
        if not papers:
            break
        for paper in papers:
            if yielded >= max_results:
                break
            yield paper
            yielded += 1
        start += len(papers)
        if yielded < max_results:
            time.sleep(pause_seconds)


def parse_atom_feed(xml_text: str) -> list[ArxivPaper]:
    """Parse arXiv Atom XML into normalized paper metadata."""

    root = ElementTree.fromstring(xml_text)
    papers: list[ArxivPaper] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        abs_url = _entry_id(entry)
        arxiv_id, version = _parse_arxiv_id(abs_url)
        links = entry.findall("atom:link", ATOM_NS)
        pdf_url = _pdf_url_from_links(links, arxiv_id, version)
        categories = tuple(
            category.attrib["term"]
            for category in entry.findall("atom:category", ATOM_NS)
            if category.attrib.get("term")
        )
        primary = entry.find("arxiv:primary_category", ATOM_NS)
        papers.append(
            ArxivPaper(
                arxiv_id=arxiv_id,
                version=version,
                title=normalize_space(_text(entry, "atom:title")),
                authors=tuple(
                    normalize_space(_text(author, "atom:name"))
                    for author in entry.findall("atom:author", ATOM_NS)
                ),
                summary=normalize_space(_text(entry, "atom:summary")),
                published=_text(entry, "atom:published"),
                updated=_text(entry, "atom:updated"),
                primary_category=primary.attrib.get("term", "") if primary is not None else "",
                categories=categories,
                abs_url=abs_url,
                pdf_url=pdf_url,
                doi=_optional_text(entry, "arxiv:doi"),
                journal_ref=_optional_text(entry, "arxiv:journal_ref"),
                comment=_optional_text(entry, "arxiv:comment"),
            )
        )
    return papers


def collect_arxiv_papers(
    topics: list[ArxivTopic],
    *,
    output_dir: str | Path,
    max_results_per_topic: int | None = None,
    max_results_per_topic_year: int | None = None,
    from_year: int | None = None,
    to_year: int | None = None,
    batch_size: int = 100,
    api_pause_seconds: float = 3.1,
    download_pause_seconds: float = 1.0,
    timeout_seconds: float = 60.0,
    download_pdfs: bool = True,
    overwrite: bool = False,
    user_agent: str = DEFAULT_USER_AGENT,
    selected_topics: set[str] | None = None,
    retries: int = 3,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    verbose: bool = True,
) -> dict[str, Any]:
    """Collect metadata and optionally PDFs for all configured topics."""

    base_dir = Path(output_dir)
    canonical_pdf_dir = base_dir / "pdfs" / "by-id"
    topic_pdf_dir = base_dir / "pdfs" / "by-topic-year"
    metadata_dir = base_dir / "metadata"
    base_dir.mkdir(parents=True, exist_ok=True)
    if download_pdfs:
        canonical_pdf_dir.mkdir(parents=True, exist_ok=True)
        topic_pdf_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict[str, Any]] = {}
    topic_counts: dict[str, int] = {}
    topic_year_counts: dict[str, int] = {}
    topic_year_rows: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_topic_rows: dict[str, list[dict[str, Any]]] = {}
    by_year_rows: dict[str, list[dict[str, Any]]] = {}
    download_counts = {"downloaded": 0, "existing": 0, "failed": 0, "skipped": 0}
    organization_counts = {
        "hardlinked": 0,
        "copied": 0,
        "existing": 0,
        "missing_source": 0,
        "skipped": 0,
    }
    started_at = datetime.now(timezone.utc).isoformat()
    total_pdf_bytes = 0
    counted_pdf_paths: set[Path] = set()
    processed_records = 0
    active_topics = [
        topic for topic in topics if selected_topics is None or topic.name in selected_topics
    ]
    if not active_topics:
        raise ValueError("No configured topics matched the requested topic filter")
    query_years = _query_years(from_year, to_year)

    for topic_index, topic in enumerate(active_topics):
        safe_topic = slugify(topic.name, max_length=80)
        topic_counts[topic.name] = 0
        for query_year_index, query_year in enumerate(query_years):
            query = (
                build_submitted_date_query(topic.query, query_year)
                if query_year is not None
                else topic.query
            )
            limit = _topic_limit(
                topic,
                query_year=query_year,
                max_results_per_topic=max_results_per_topic,
                max_results_per_topic_year=max_results_per_topic_year,
            )
            topic_year_key = f"{topic.name}:{query_year or 'all'}"
            topic_year_counts[topic_year_key] = 0
            if verbose:
                print(
                    f"[arxiv] topic={topic.name} query_year={query_year or 'all'} "
                    f"limit={limit}",
                    flush=True,
                )
            for paper in iter_arxiv_papers(
                query,
                max_results=limit,
                batch_size=batch_size,
                pause_seconds=api_pause_seconds,
                timeout_seconds=timeout_seconds,
                user_agent=user_agent,
                retries=retries,
                sort_by=sort_by,
                sort_order=sort_order,
            ):
                processed_records += 1
                topic_counts[topic.name] += 1
                topic_year_counts[topic_year_key] += 1
                published_year = publication_year(paper)
                row = manifest.setdefault(paper.arxiv_id, paper_to_manifest_row(paper))
                matched_topics = set(row["matched_topics"].split(";")) if row["matched_topics"] else set()
                matched_topic_years = (
                    set(row["matched_topic_years"].split(";")) if row["matched_topic_years"] else set()
                )
                matched_topics.add(topic.name)
                matched_topic_years.add(f"{topic.name}:{published_year}")
                row["matched_topics"] = ";".join(sorted(matched_topics))
                row["matched_topic_years"] = ";".join(sorted(matched_topic_years))

                canonical_path = canonical_pdf_dir / published_year / filename_for_paper(paper)
                topic_path = topic_pdf_dir / safe_topic / published_year / filename_for_paper(paper)
                download_status = "skipped"
                organization_status = "skipped"
                if download_pdfs:
                    download_status, canonical_path = download_pdf(
                        paper,
                        canonical_pdf_dir / published_year,
                        overwrite=overwrite,
                        timeout_seconds=timeout_seconds,
                        user_agent=user_agent,
                        retries=retries,
                    )
                    download_counts[download_status] = download_counts.get(download_status, 0) + 1
                    organization_status, topic_path = place_topic_pdf(
                        canonical_path,
                        topic_path,
                        overwrite=overwrite,
                    )
                    organization_counts[organization_status] = organization_counts.get(
                        organization_status, 0
                    ) + 1
                    resolved_canonical = canonical_path.resolve() if canonical_path.exists() else canonical_path
                    if canonical_path.exists() and resolved_canonical not in counted_pdf_paths:
                        total_pdf_bytes += canonical_path.stat().st_size
                        counted_pdf_paths.add(resolved_canonical)
                    time.sleep(download_pause_seconds)
                else:
                    download_counts["skipped"] += 1
                    organization_counts["skipped"] += 1

                row["canonical_pdf_path"] = str(canonical_path)
                row["pdf_path"] = str(topic_path if download_pdfs else canonical_path)
                row["pdf_size_bytes"] = _file_size(canonical_path)
                row["download_status"] = merge_download_status(
                    row.get("download_status", ""),
                    download_status,
                )
                row["organization_status"] = merge_download_status(
                    row.get("organization_status", ""),
                    organization_status,
                )

                topic_row = dict(row)
                topic_row.update(
                    {
                        "topic": topic.name,
                        "query_year": str(query_year or ""),
                        "published_year": published_year,
                        "pdf_path": str(topic_path),
                        "download_status": download_status,
                        "organization_status": organization_status,
                    }
                )
                key = (topic.name, published_year)
                topic_year_rows.setdefault(key, []).append(topic_row)
                by_topic_rows.setdefault(topic.name, []).append(topic_row)
                by_year_rows.setdefault(published_year, []).append(topic_row)
                write_manifest_csv(
                    metadata_dir / "by-topic-year" / safe_topic / published_year / "manifest.csv",
                    topic_year_rows[key],
                )
                write_manifest_jsonl(
                    metadata_dir / "by-topic-year" / safe_topic / published_year / "manifest.jsonl",
                    topic_year_rows[key],
                )
                write_event(
                    metadata_dir / "events.jsonl",
                    {
                        "arxiv_id": paper.arxiv_id,
                        "topic": topic.name,
                        "query_year": query_year,
                        "published_year": published_year,
                        "download_status": download_status,
                        "organization_status": organization_status,
                        "canonical_pdf_path": str(canonical_path),
                        "pdf_path": str(topic_path),
                    },
                )
                write_status(
                    base_dir / "status.json",
                    {
                        "started_at": started_at,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "output_dir": str(base_dir),
                        "processed_records": processed_records,
                        "unique_papers_seen": len(manifest),
                        "download_counts": download_counts,
                        "organization_counts": organization_counts,
                        "topic_counts": topic_counts,
                        "topic_year_counts": topic_year_counts,
                        "canonical_pdf_dir": str(canonical_pdf_dir),
                        "topic_pdf_dir": str(topic_pdf_dir),
                        "estimated_unique_pdf_bytes_seen": total_pdf_bytes,
                    },
                )
                if verbose:
                    title_preview = safe_console_text(paper.title[:90])
                    print(
                        f"[arxiv] {download_status:10s} {topic.name} "
                        f"{published_year} {paper.arxiv_id} {title_preview}",
                        flush=True,
                    )
            if query_year_index < len(query_years) - 1:
                time.sleep(api_pause_seconds)
        if topic_index < len(active_topics) - 1:
            time.sleep(api_pause_seconds)

    rows = sorted(manifest.values(), key=lambda item: (item["published"], item["arxiv_id"]))
    write_manifest_csv(base_dir / "manifest.csv", rows)
    write_manifest_jsonl(base_dir / "manifest.jsonl", rows)
    write_bibtex(base_dir / "references_arxiv.bib", rows)
    for topic_name, rows_for_topic in by_topic_rows.items():
        write_manifest_csv(metadata_dir / "by-topic" / slugify(topic_name, max_length=80) / "manifest.csv", rows_for_topic)
        write_manifest_jsonl(metadata_dir / "by-topic" / slugify(topic_name, max_length=80) / "manifest.jsonl", rows_for_topic)
    for year, rows_for_year in by_year_rows.items():
        write_manifest_csv(metadata_dir / "by-year" / year / "manifest.csv", rows_for_year)
        write_manifest_jsonl(metadata_dir / "by-year" / year / "manifest.jsonl", rows_for_year)
    summary = {
        "output_dir": str(base_dir),
        "canonical_pdf_dir": str(canonical_pdf_dir),
        "topic_pdf_dir": str(topic_pdf_dir),
        "metadata_dir": str(metadata_dir),
        "topics": topic_counts,
        "topic_years": topic_year_counts,
        "unique_papers": len(rows),
        "download_counts": download_counts,
        "organization_counts": organization_counts,
        "manifest_csv": str(base_dir / "manifest.csv"),
        "manifest_jsonl": str(base_dir / "manifest.jsonl"),
        "bibtex": str(base_dir / "references_arxiv.bib"),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    (base_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def download_pdf(
    paper: ArxivPaper,
    pdf_dir: Path,
    *,
    overwrite: bool = False,
    timeout_seconds: float = 60.0,
    user_agent: str = DEFAULT_USER_AGENT,
    retries: int = 3,
) -> tuple[str, Path]:
    """Download one PDF and return a status plus its final path."""

    pdf_dir.mkdir(parents=True, exist_ok=True)
    target = pdf_dir / filename_for_paper(paper)
    if target.exists() and not overwrite:
        return "existing", target
    tmp_target = target.with_suffix(".pdf.tmp")
    request = Request(paper.pdf_url, headers={"User-Agent": user_agent})
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                with tmp_target.open("wb") as handle:
                    shutil.copyfileobj(response, handle)
            if not _looks_like_pdf(tmp_target):
                tmp_target.unlink(missing_ok=True)
                return "failed", target
            tmp_target.replace(target)
            return "downloaded", target
        except (HTTPError, URLError, TimeoutError, OSError):
            tmp_target.unlink(missing_ok=True)
            if attempt < retries:
                time.sleep(min(30.0, 2.0 * attempt))
    return "failed", target


def place_topic_pdf(source: Path, target: Path, *, overwrite: bool = False) -> tuple[str, Path]:
    """Place a topic/year PDF using a hardlink when possible and copy fallback."""

    if not source.exists():
        return "missing_source", target
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not overwrite:
            return "existing", target
        target.unlink()
    try:
        os.link(source, target)
        return "hardlinked", target
    except OSError:
        shutil.copy2(source, target)
        return "copied", target


def filename_for_paper(paper: ArxivPaper) -> str:
    """Return a deterministic, filesystem-safe PDF filename."""

    safe_id = paper.arxiv_id.replace("/", "_")
    version = paper.version or "latest"
    title = slugify(paper.title, max_length=80)
    return f"{safe_id}{version}__{title}.pdf"


def paper_to_manifest_row(paper: ArxivPaper) -> dict[str, Any]:
    """Convert paper metadata into a CSV/JSONL row."""

    return {
        "arxiv_id": paper.arxiv_id,
        "version": paper.version or "",
        "title": paper.title,
        "authors": "; ".join(paper.authors),
        "published": paper.published,
        "updated": paper.updated,
        "primary_category": paper.primary_category,
        "categories": ";".join(paper.categories),
        "doi": paper.doi or "",
        "journal_ref": paper.journal_ref or "",
        "comment": paper.comment or "",
        "abs_url": paper.abs_url,
        "pdf_url": paper.pdf_url,
        "canonical_pdf_path": "",
        "pdf_path": "",
        "pdf_size_bytes": "",
        "download_status": "",
        "organization_status": "",
        "matched_topics": "",
        "matched_topic_years": "",
        "topic": "",
        "query_year": "",
        "published_year": publication_year(paper),
        "summary": paper.summary,
    }


def write_manifest_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write the normalized manifest as CSV."""

    columns = manifest_columns(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def manifest_columns(rows: list[dict[str, Any]]) -> list[str]:
    """Return stable manifest columns while preserving any extra metadata."""

    base_columns = [
        "arxiv_id",
        "version",
        "title",
        "authors",
        "published",
        "updated",
        "primary_category",
        "categories",
        "doi",
        "journal_ref",
        "comment",
        "abs_url",
        "pdf_url",
        "canonical_pdf_path",
        "pdf_path",
        "pdf_size_bytes",
        "download_status",
        "organization_status",
        "matched_topics",
        "matched_topic_years",
        "topic",
        "query_year",
        "published_year",
        "summary",
    ]
    extras = sorted({key for row in rows for key in row}.difference(base_columns))
    return base_columns + extras


def write_manifest_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write the normalized manifest as JSON Lines."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_event(path: Path, event: dict[str, Any]) -> None:
    """Append one progress event."""

    path.parent.mkdir(parents=True, exist_ok=True)
    item = {"timestamp": datetime.now(timezone.utc).isoformat()} | event
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n")


def write_status(path: Path, status: dict[str, Any]) -> None:
    """Write the current collector status atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def write_bibtex(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write a BibTeX file that can be curated into the thesis references."""

    entries: list[str] = []
    for row in rows:
        authors = " and ".join(part.strip() for part in row["authors"].split(";") if part.strip())
        year = str(row["published"])[:4] or "n.d."
        key = _bibtex_key_from_row(row)
        fields = {
            "title": row["title"],
            "author": authors or "Unknown",
            "year": year,
            "eprint": row["arxiv_id"],
            "archivePrefix": "arXiv",
            "primaryClass": row["primary_category"],
            "url": row["abs_url"],
        }
        if row.get("doi"):
            fields["doi"] = row["doi"]
        body = ",\n".join(f"  {name} = {{{_escape_bibtex(value)}}}" for name, value in fields.items())
        entries.append(f"@misc{{{key},\n{body}\n}}")
    path.write_text("\n\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")


def normalize_space(text: str) -> str:
    """Collapse whitespace in arXiv text fields."""

    return " ".join(text.split())


def publication_year(paper: ArxivPaper) -> str:
    """Return the best available publication year for a paper."""

    for value in (paper.published, paper.updated):
        match = re.match(r"(\d{4})", value or "")
        if match:
            return match.group(1)
    return "unknown"


def merge_download_status(previous: Any, current: str) -> str:
    """Keep the strongest status when a paper appears in many topics."""

    order = {
        "downloaded": 5,
        "existing": 4,
        "hardlinked": 4,
        "copied": 4,
        "skipped": 3,
        "failed": 2,
        "missing_source": 1,
        "": 0,
    }
    previous_text = str(previous or "")
    return current if order.get(current, 0) >= order.get(previous_text, 0) else previous_text


def safe_console_text(text: str) -> str:
    """Return text that cannot crash legacy Windows redirected stdout."""

    return text.encode("ascii", errors="replace").decode("ascii")


def slugify(text: str, *, max_length: int = 96) -> str:
    """Create a conservative ASCII slug for filenames and keys."""

    normalized = normalize_space(text).lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    if len(normalized) > max_length:
        normalized = normalized[:max_length].rstrip("-")
    return normalized or "untitled"


def _query_years(from_year: int | None, to_year: int | None) -> list[int | None]:
    if from_year is None and to_year is None:
        return [None]
    current_year = datetime.now(timezone.utc).year
    start = from_year if from_year is not None else 1991
    end = to_year if to_year is not None else current_year
    if start > end:
        raise ValueError(f"from_year must be <= to_year, got {start} > {end}")
    return list(range(start, end + 1))


def _topic_limit(
    topic: ArxivTopic,
    *,
    query_year: int | None,
    max_results_per_topic: int | None,
    max_results_per_topic_year: int | None,
) -> int:
    if query_year is not None and max_results_per_topic_year is not None:
        return max_results_per_topic_year
    if max_results_per_topic is not None:
        return max_results_per_topic
    if topic.max_results is not None:
        return topic.max_results
    return 100


def _file_size(path: Path) -> int | str:
    return path.stat().st_size if path.exists() else ""


def _entry_id(entry: ElementTree.Element) -> str:
    value = _text(entry, "atom:id")
    if not value:
        raise ValueError("arXiv entry without atom:id")
    return value


def _parse_arxiv_id(abs_url: str) -> tuple[str, str | None]:
    path = urlparse(abs_url).path
    if "/abs/" in path:
        raw_id = path.split("/abs/", 1)[1]
    elif "/pdf/" in path:
        raw_id = path.split("/pdf/", 1)[1]
    else:
        raw_id = path.strip("/")
    raw_id = raw_id.removesuffix(".pdf")
    match = re.search(r"(v\d+)$", raw_id)
    if match:
        return raw_id[: -len(match.group(1))], match.group(1)
    return raw_id, None


def _pdf_url_from_links(
    links: list[ElementTree.Element],
    arxiv_id: str,
    version: str | None,
) -> str:
    for link in links:
        if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
            href = link.attrib.get("href")
            if href:
                return href
    version_suffix = version or ""
    return f"https://arxiv.org/pdf/{arxiv_id}{version_suffix}"


def _text(entry: ElementTree.Element, selector: str) -> str:
    element = entry.find(selector, ATOM_NS)
    return element.text.strip() if element is not None and element.text else ""


def _optional_text(entry: ElementTree.Element, selector: str) -> str | None:
    value = _text(entry, selector)
    return value or None


def _looks_like_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 128:
        return False
    with path.open("rb") as handle:
        return handle.read(5) == b"%PDF-"


def _bibtex_key_from_row(row: dict[str, Any]) -> str:
    authors = [part.strip() for part in str(row["authors"]).split(";") if part.strip()]
    author = "anon"
    if authors:
        author = slugify(authors[0].split()[-1], max_length=24)
    year = str(row["published"])[:4] or "nd"
    suffix = str(row["arxiv_id"]).replace("/", "_").replace(".", "")
    return f"{author}{year}arxiv{suffix}"


def _escape_bibtex(value: Any) -> str:
    text = str(value)
    return text.replace("\\", "\\textbackslash{}").replace("{", "\\{").replace("}", "\\}")
