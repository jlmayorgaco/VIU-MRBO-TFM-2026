"""Execute the reproducible multi-source literature campaign V2.

V1 remains an immutable input.  This campaign creates a derivative namespace
under ``academic-review/multisource-v2`` and records provider-specific
requests, raw responses, normalization, deduplication, source overlap and
marginal yield.  It deliberately does not access Google Scholar, Web of
Science, Scopus or IEEE Xplore: those sources receive manual query/export
packs instead.

Metadata records are never promoted to scientific evidence by this script.
Open-access URLs are leads for a later legal acquisition pass, not proof that
the full text has been read.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import requests
import yaml
from dotenv import dotenv_values


ACADEMIC_REVIEW = Path(__file__).resolve().parents[2]
V2_ROOT = ACADEMIC_REVIEW / "multisource-v2"
CONFIG = V2_ROOT / "config" / "multisource_v2.yaml"
V1_CORPUS = ACADEMIC_REVIEW / "data" / "processed" / "candidate_corpus_stage1c.csv"
V1_EVIDENCE = ACADEMIC_REVIEW / "data" / "processed" / "fulltext_evidence_matrix.csv"
ENV = ACADEMIC_REVIEW / ".env.literature"
RAW = V2_ROOT / "data" / "raw"
PROCESSED = V2_ROOT / "data" / "processed"
LOGS = V2_ROOT / "logs"
REPORTS = V2_ROOT / "reports"
MANIFESTS = V2_ROOT / "manifests"
MANUAL = V2_ROOT / "manual-packs"
for directory in (RAW, PROCESSED, LOGS, REPORTS, MANIFESTS, MANUAL):
    directory.mkdir(parents=True, exist_ok=True)


def load_bootstrap() -> Any:
    path = ACADEMIC_REVIEW / "scripts" / "bootstrap_literature.py"
    spec = importlib.util.spec_from_file_location("mrob_bootstrap_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load V1 normalization helpers from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BOOT = load_bootstrap()


def load_stage1b() -> Any:
    path = ACADEMIC_REVIEW / "scripts" / "stage1b.py"
    spec = importlib.util.spec_from_file_location("mrob_stage1b_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load V1 screening helpers from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


STAGE1B = load_stage1b()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_year(value: Any) -> str:
    return BOOT.safe_year(value)


def norm_doi(value: Any) -> str:
    return BOOT.norm_doi(value)


def norm_title(value: Any) -> str:
    return BOOT.norm_title(value)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    materialized = list(rows)
    if fields is None:
        names: list[str] = []
        for row in materialized:
            for name in row:
                if name not in names:
                    names.append(name)
        fields = names
    names = list(fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({name: row.get(name, "") for name in names})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def redacted_params(params: dict[str, Any]) -> str:
    safe = dict(params)
    for key in ("mailto", "api_key", "CORE_API_KEY", "SEMANTIC_SCHOLAR_API_KEY"):
        if key in safe:
            safe[key] = "[REDACTED]"
    return json.dumps(safe, ensure_ascii=False, sort_keys=True)


@dataclass
class ApiEvent:
    source: str
    request_kind: str
    query_id: str
    window_id: str
    status: str
    http_status: str = ""
    attempts: int = 0
    error: str = ""
    cache_file: str = ""
    url: str = ""
    params: str = ""
    elapsed_ms: int = 0
    retrieved_at_utc: str = ""


@dataclass
class SearchEvent:
    query_id: str
    window_id: str
    source: str
    exact_query: str
    endpoint: str
    status: str
    result_count: int = 0
    returned_count: int = 0
    request_hash: str = ""
    error: str = ""
    executed_at_utc: str = ""


class CachedClient:
    """Small source-aware HTTP client with persistent raw-response caching."""

    delays = {
        "crossref": 0.55,
        "openalex": 0.35,
        "arxiv": 3.1,
        "semantic_scholar": 0.6,
        "openaire": 0.6,
        "dblp": 0.35,
        "doaj": 0.6,
        "core": 0.6,
        "unpaywall": 0.25,
        "opencitations": 0.35,
    }

    def __init__(self, email: str, keys: dict[str, str], *, force: bool = False, arxiv_delay: float = 3.1):
        self.email = email
        self.keys = keys
        self.force = force
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"MROB-Academic-Review-V2/1.0 (mailto:{email})",
            "Accept": "application/json",
        })
        self.delays = dict(self.delays)
        self.delays["arxiv"] = max(3.0, float(arxiv_delay))
        self.last_request: dict[str, float] = {}
        self.blocked_sources: set[str] = set()
        self.events: list[ApiEvent] = []

    def _cache_file(self, source: str, url: str, params: dict[str, Any], extension: str) -> Path:
        fingerprint = hashlib.sha256(
            json.dumps({"url": url, "params": params}, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        directory = RAW / source
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{fingerprint}{extension}"

    def _headers(self, source: str) -> dict[str, str]:
        headers: dict[str, str] = {}
        if source == "semantic_scholar" and self.keys.get("SEMANTIC_SCHOLAR_API_KEY"):
            headers["x-api-key"] = self.keys["SEMANTIC_SCHOLAR_API_KEY"]
        if source == "core" and self.keys.get("CORE_API_KEY"):
            headers["Authorization"] = f"Bearer {self.keys['CORE_API_KEY']}"
        if source == "opencitations" and self.keys.get("OPENCITATIONS_ACCESS_TOKEN"):
            headers["authorization"] = self.keys["OPENCITATIONS_ACCESS_TOKEN"]
        return headers

    def _request(
        self,
        source: str,
        kind: str,
        url: str,
        params: dict[str, Any],
        query_id: str,
        window_id: str,
        *,
        accept: str,
        extension: str,
        max_attempts: int = 3,
    ) -> tuple[str | None, Path | None]:
        cache_file = self._cache_file(source, url, params, extension)
        params_text = redacted_params(params)
        if source in self.blocked_sources:
            self.events.append(ApiEvent(source, kind, query_id, window_id, "network_blocked", error="provider circuit breaker open after a connection failure", cache_file=str(cache_file.relative_to(V2_ROOT)), url=url, params=params_text, retrieved_at_utc=utc_now()))
            return None, cache_file
        if cache_file.exists() and not self.force:
            self.events.append(ApiEvent(source, kind, query_id, window_id, "cache_hit", cache_file=str(cache_file.relative_to(V2_ROOT)), url=url, params=params_text, retrieved_at_utc=utc_now()))
            return cache_file.read_text(encoding="utf-8"), cache_file

        last_error = ""
        for attempt in range(1, max_attempts + 1):
            gap = self.delays.get(source, 0.3) - (time.monotonic() - self.last_request.get(source, 0.0))
            if gap > 0:
                time.sleep(gap)
            started = time.monotonic()
            try:
                request_params = dict(params)
                if source == "crossref":
                    request_params.setdefault("mailto", self.email)
                if source == "unpaywall":
                    request_params.setdefault("email", self.email)
                response = self.session.get(
                    url,
                    params=request_params,
                    headers={**self._headers(source), "Accept": accept},
                    timeout=(5, 10),
                )
                self.last_request[source] = time.monotonic()
                elapsed = int((time.monotonic() - started) * 1000)
                status_code = str(response.status_code)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait = min(30.0, float(retry_after)) if retry_after else min(30.0, 2.0**attempt)
                    except ValueError:
                        wait = min(30.0, 2.0**attempt)
                    last_error = f"HTTP 429; retry_after={wait}"
                    self.events.append(ApiEvent(source, kind, query_id, window_id, "rate_limited", status_code, attempt, last_error, str(cache_file.relative_to(V2_ROOT)), url, params_text, elapsed, utc_now()))
                    # Stop the source after the first 429.  A campaign can be
                    # resumed later, but it must not hammer a public API while
                    # trying to finish an unrelated source.
                    self.blocked_sources.add(source)
                    return None, cache_file
                if response.status_code in {401, 403}:
                    state = "auth_required" if response.status_code == 401 else "forbidden"
                    self.events.append(ApiEvent(source, kind, query_id, window_id, state, status_code, attempt, f"SOURCE_{state.upper()}", str(cache_file.relative_to(V2_ROOT)), url, params_text, elapsed, utc_now()))
                    return None, cache_file
                if 500 <= response.status_code < 600:
                    last_error = f"HTTP {response.status_code}"
                    self.events.append(ApiEvent(source, kind, query_id, window_id, "retry", status_code, attempt, last_error, str(cache_file.relative_to(V2_ROOT)), url, params_text, elapsed, utc_now()))
                    time.sleep(min(15.0, 2.0**attempt))
                    continue
                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code}"
                    self.events.append(ApiEvent(source, kind, query_id, window_id, "failed", status_code, attempt, last_error, str(cache_file.relative_to(V2_ROOT)), url, params_text, elapsed, utc_now()))
                    return None, cache_file
                cache_file.write_text(response.text, encoding="utf-8")
                self.events.append(ApiEvent(source, kind, query_id, window_id, "ok", status_code, attempt, cache_file=str(cache_file.relative_to(V2_ROOT)), url=url, params=params_text, elapsed_ms=elapsed, retrieved_at_utc=utc_now()))
                return response.text, cache_file
            except requests.RequestException as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                elapsed = int((time.monotonic() - started) * 1000)
                network_failure = isinstance(exc, (requests.exceptions.ProxyError, requests.exceptions.ConnectionError, requests.exceptions.Timeout))
                if network_failure:
                    self.blocked_sources.add(source)
                state = "network_blocked" if network_failure else ("retry" if attempt < max_attempts else "failed")
                self.events.append(ApiEvent(source, kind, query_id, window_id, state, "", attempt, last_error, str(cache_file.relative_to(V2_ROOT)), url, params_text, elapsed, utc_now()))
                if network_failure:
                    return None, cache_file
                if attempt < max_attempts:
                    time.sleep(min(15.0, 2.0**attempt))
        return None, cache_file

    def json(self, source: str, kind: str, url: str, params: dict[str, Any], query_id: str, window_id: str) -> Any:
        text, cache_file = self._request(source, kind, url, params, query_id, window_id, accept="application/json", extension=".json")
        if text is None:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            # Preserve anti-bot/error HTML as a diagnostic, but do not let a
            # later --resume run treat it as a successful JSON cache hit.
            if cache_file is not None and cache_file.suffix == ".json" and cache_file.exists():
                cache_file.replace(cache_file.with_suffix(".html"))
            self.events.append(ApiEvent(source, kind, query_id, window_id, "parse_error", error=f"JSONDecodeError: {exc}", retrieved_at_utc=utc_now()))
            return None

    def xml(self, source: str, kind: str, url: str, params: dict[str, Any], query_id: str, window_id: str) -> str | None:
        text, _ = self._request(source, kind, url, params, query_id, window_id, accept="application/atom+xml, application/xml, text/xml", extension=".xml")
        return text


def value_of(value: Any) -> str:
    """Extract a scalar from common repository/JSON-LD value wrappers."""
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("$", "value", "text", "name", "content", "title"):
            if key in value:
                result = value_of(value[key])
                if result:
                    return result
    if isinstance(value, list):
        return value_of(value[0]) if value else ""
    return ""


def author_text(value: Any) -> str:
    if isinstance(value, list):
        names = [author_text(item) for item in value]
        return "; ".join(item for item in names if item)
    if isinstance(value, dict):
        name = value_of(value.get("name")) or " ".join(clean(value.get(k)) for k in ("given", "family") if clean(value.get(k)))
        return name.strip() or value_of(value)
    return value_of(value)


def record(
    source: str,
    query_id: str,
    window_id: str,
    *,
    title: Any,
    authors: Any = "",
    year: Any = "",
    doi: Any = "",
    source_id: Any = "",
    abstract: Any = "",
    venue: Any = "",
    url: Any = "",
    open_access_url: Any = "",
    citation_count: Any = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    title_text = html.unescape(clean(title))
    if not title_text:
        return None
    author_text_value = author_text(authors)
    year_text = safe_year(year)
    doi_text = norm_doi(doi)
    source_id_text = clean(source_id)
    venue_text = clean(venue)
    candidate_id = BOOT.stable_id(title_text, year_text, doi_text, author_text_value, venue_text)
    row: dict[str, Any] = {
        "candidate_id": candidate_id,
        "title": title_text,
        "title_norm": norm_title(title_text),
        "authors": author_text_value,
        "authors_norm": BOOT.norm_authors(author_text_value),
        "year": year_text,
        "venue": venue_text,
        "doi": doi_text,
        "doi_norm": doi_text,
        "abstract": re.sub(r"\s+", " ", html.unescape(clean(abstract))).strip(),
        "document_type": "",
        "source_ids": f"{source}:{source_id_text}" if source_id_text else "",
        "provenance": source,
        "provenance_sources": source,
        "provenance_queries": f"{query_id}:{window_id}",
        "verification_status": "metadata_verified" if source_id_text or doi_text else "metadata_partial",
        "metadata_verification_status": "metadata_verified" if title_text and (source_id_text or doi_text) else "metadata_partial",
        "evidence_status": "not_evidence",
        "screening_status": "pending",
        "legacy_seed_id": "",
        "wos_ut": "",
        "citation_count": clean(citation_count),
        "citation_count_source": source if clean(citation_count) else "",
        "retrieved_at_utc": utc_now(),
        "dedup_status": "unique",
        "duplicate_status": "unique",
        "dedup_parent_candidate_id": "",
        "notes": "",
        "source": source,
        "source_record_id": source_id_text,
        "query_id": query_id,
        "window_id": window_id,
        "source_url": clean(url),
        "open_access_url": clean(open_access_url),
    }
    if extra:
        row.update(extra)
    return row


def query_plan(config: dict[str, Any]) -> list[dict[str, Any]]:
    windows = config["date_windows"]
    plan: list[dict[str, Any]] = []
    for family in config["concept_lattice"]:
        selected = ["primary"] if family["window"] == "primary" else ["primary", "foundational"]
        for window_id in selected:
            window = windows[window_id]
            plan.append({
                "query_id": family["id"],
                "execution_id": f"{family['id']}_{window_id}",
                "window_id": window_id,
                "label": family["label"],
                "query": family["query"],
                "axes": ";".join(family.get("axes", [])),
                "from_year": int(window["from_year"]),
                "to_year": int(window["to_year"]),
            })
    return plan


def crossref_items(data: Any) -> tuple[list[dict[str, Any]], int]:
    message = (data or {}).get("message") or {}
    return list(message.get("items") or []), int(message.get("total-results") or 0)


def openalex_items(data: Any) -> tuple[list[dict[str, Any]], int]:
    payload = data or {}
    return list(payload.get("results") or []), int((payload.get("meta") or {}).get("count") or 0)


def semantic_items(data: Any) -> tuple[list[dict[str, Any]], int]:
    payload = data or {}
    return list(payload.get("data") or []), int(payload.get("total") or 0)


def parse_arxiv(xml_text: str | None) -> tuple[list[dict[str, Any]], int]:
    if not xml_text:
        return [], 0
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return [], 0
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = root.findall("a:entry", ns)
    items: list[dict[str, Any]] = []
    for entry in entries:
        authors = [clean(node.findtext("a:name", default="", namespaces=ns)) for node in entry.findall("a:author", ns)]
        link = next((node.attrib.get("href", "") for node in entry.findall("a:link", ns) if node.attrib.get("rel") == "alternate"), "")
        items.append({
            "id": clean(entry.findtext("a:id", default="", namespaces=ns)),
            "title": clean(entry.findtext("a:title", default="", namespaces=ns)),
            "summary": clean(entry.findtext("a:summary", default="", namespaces=ns)),
            "published": clean(entry.findtext("a:published", default="", namespaces=ns)),
            "authors": authors,
            "link": link,
        })
    total = len(items)
    return items, total


def arxiv_id(value: Any) -> str:
    match = re.search(r"(?:abs|pdf)/([^?#]+)", clean(value))
    return match.group(1).removesuffix(".pdf") if match else ""


def dblp_items(data: Any) -> tuple[list[dict[str, Any]], int]:
    hits = (((data or {}).get("result") or {}).get("hits") or {})
    docs = hits.get("hit") or []
    return [item.get("info") or {} for item in docs], int(hits.get("@total", 0) or 0)


def doaj_items(data: Any) -> tuple[list[dict[str, Any]], int]:
    payload = data or {}
    return list(payload.get("results") or []), int(payload.get("total", 0) or 0)


def core_items(data: Any) -> tuple[list[dict[str, Any]], int]:
    payload = data or {}
    return list(payload.get("results") or []), int(payload.get("totalHits") or payload.get("total") or 0)


def openaire_items(data: Any) -> tuple[list[dict[str, Any]], int]:
    payload = data or {}
    response = payload.get("response") or payload
    results = response.get("results") or {}
    raw = results.get("result") if isinstance(results, dict) else results
    if not isinstance(raw, list):
        raw = []
    header = response.get("header") or {}
    raw_total = value_of(header.get("numFound") or header.get("total"))
    try:
        total = int(raw_total or len(raw))
    except ValueError:
        total = len(raw)
    return raw, total


def openaire_result(item: dict[str, Any]) -> dict[str, Any]:
    metadata = item.get("metadata") or {}
    entity = metadata.get("oaf:entity") or metadata.get("entity") or {}
    result = entity.get("oaf:result") or entity.get("result") or metadata
    if isinstance(result, list):
        result = result[0] if result else {}
    if not isinstance(result, dict):
        result = {}
    title = value_of(result.get("title") or result.get("mainTitle") or item.get("title"))
    creators = result.get("creator") or result.get("creators") or result.get("author") or []
    identifiers = result.get("pid") or result.get("identifier") or result.get("identifiers") or []
    if isinstance(identifiers, dict):
        identifiers = [identifiers]
    doi = ""
    source_id = ""
    for identifier in identifiers if isinstance(identifiers, list) else []:
        text = value_of(identifier)
        scheme = clean(identifier.get("classid") if isinstance(identifier, dict) else "").lower()
        if "doi" in scheme or text.lower().startswith("10."):
            doi = norm_doi(text)
        source_id = source_id or text
    instance = result.get("instance") or result.get("instances") or {}
    if isinstance(instance, list):
        instance = instance[0] if instance else {}
    access_url = ""
    if isinstance(instance, dict):
        access_url = value_of(instance.get("webresource") or instance.get("url") or instance.get("ref"))
    return {
        "title": title,
        "authors": creators,
        "year": value_of(result.get("dateofacceptance") or result.get("dateofpublication") or result.get("publicationYear")),
        "doi": doi,
        "source_id": source_id or value_of(item.get("id")),
        "abstract": value_of(result.get("description") or result.get("abstract")),
        "venue": value_of(result.get("publisher") or result.get("journal")),
        "url": access_url,
        "open_access_url": access_url,
    }


def normalize_item(source: str, item: dict[str, Any], query_id: str, window_id: str) -> dict[str, Any] | None:
    if source == "crossref":
        title = value_of(item.get("title"))
        authors = item.get("author") or []
        issued = item.get("published-print") or item.get("published-online") or item.get("issued") or {}
        parts = issued.get("date-parts") or []
        year = parts[0][0] if parts and parts[0] else ""
        return record(source, query_id, window_id, title=title, authors=authors, year=year, doi=item.get("DOI"), source_id=item.get("DOI"), abstract=item.get("abstract"), venue=value_of(item.get("container-title")), url=f"https://doi.org/{item.get('DOI')}" if item.get("DOI") else "", citation_count=item.get("is-referenced-by-count"))
    if source == "openalex":
        authors = [((author.get("author") or {}).get("display_name") or "") for author in item.get("authorships") or []]
        primary = item.get("primary_location") or {}
        source_info = primary.get("source") or {}
        best = item.get("best_oa_location") or {}
        return record(source, query_id, window_id, title=item.get("display_name") or item.get("title"), authors=authors, year=item.get("publication_year"), doi=item.get("doi"), source_id=item.get("id"), venue=source_info.get("display_name"), url=item.get("doi") or item.get("id"), open_access_url=best.get("pdf_url") or best.get("landing_page_url") or "", citation_count=item.get("cited_by_count"))
    if source == "arxiv":
        identifier = arxiv_id(item.get("id"))
        doi = f"10.48550/arxiv.{identifier}" if identifier else ""
        return record(source, query_id, window_id, title=item.get("title"), authors=item.get("authors"), year=item.get("published"), doi=doi, source_id=identifier, abstract=item.get("summary"), url=item.get("link"), open_access_url=item.get("link"), extra={"arxiv_id": identifier})
    if source == "semantic_scholar":
        ext = item.get("externalIds") or {}
        oa = item.get("openAccessPdf") or {}
        return record(source, query_id, window_id, title=item.get("title"), authors=item.get("authors"), year=item.get("year"), doi=ext.get("DOI"), source_id=item.get("paperId"), abstract=item.get("abstract"), venue=item.get("venue"), url=item.get("url"), open_access_url=oa.get("url") or "", citation_count=item.get("citationCount"), extra={"semantic_paper_id": item.get("paperId"), "semantic_arxiv_id": ext.get("ArXiv") or ""})
    if source == "dblp":
        return record(source, query_id, window_id, title=item.get("title"), authors=item.get("authors") or item.get("author"), year=item.get("year"), doi=item.get("doi"), source_id=item.get("key") or item.get("ee"), venue=item.get("venue"), url=item.get("ee") or item.get("url"), open_access_url=item.get("ee") or "")
    if source == "doaj":
        bib = item.get("bibjson") or item
        identifiers = bib.get("identifier") or []
        doi = ""
        for identifier in identifiers if isinstance(identifiers, list) else []:
            if clean(identifier.get("type")).lower() == "doi":
                doi = identifier.get("id")
        links = bib.get("link") or []
        url = value_of(links[0]) if links else ""
        return record(source, query_id, window_id, title=bib.get("title"), authors=bib.get("author"), year=bib.get("year"), doi=doi, source_id=item.get("id") or doi, abstract=bib.get("abstract"), venue=(bib.get("journal") or {}).get("title"), url=url, open_access_url=url)
    if source == "core":
        return record(source, query_id, window_id, title=item.get("title"), authors=item.get("authors") or item.get("author"), year=item.get("yearPublished") or item.get("publishedDate"), doi=item.get("doi"), source_id=item.get("id"), abstract=item.get("abstract"), venue=item.get("publisher"), url=item.get("downloadUrl") or item.get("sourceFulltextUrls"), open_access_url=item.get("downloadUrl") or item.get("sourceFulltextUrls"))
    if source == "openaire":
        parsed = openaire_result(item)
        return record(source, query_id, window_id, **parsed)
    return None


def source_query(
    source: str,
    item: dict[str, Any],
    client: CachedClient,
    limit: int,
) -> tuple[Any, str, dict[str, Any]]:
    """Return payload, endpoint and request params for one source query."""
    query_id = item["query_id"]
    window = item["window_id"]
    query = item["query"]
    start = f"{item['from_year']}-01-01"
    end = f"{item['to_year']}-12-31"
    if source == "crossref":
        endpoint = "https://api.crossref.org/works"
        params = {
            "query.bibliographic": query,
            "rows": limit,
            "filter": f"from-pub-date:{start},until-pub-date:{end}",
            "select": "DOI,title,author,published-print,published-online,issued,container-title,type,is-referenced-by-count,abstract",
        }
        return client.json(source, "search", endpoint, params, query_id, window), endpoint, params
    if source == "openalex":
        endpoint = "https://api.openalex.org/works"
        params = {"search": query, "per-page": limit, "filter": f"from_publication_date:{start},to_publication_date:{end}"}
        if client.keys.get("OPENALEX_API_KEY"):
            params["api_key"] = client.keys["OPENALEX_API_KEY"]
        return client.json(source, "search", endpoint, params, query_id, window), endpoint, params
    if source == "arxiv":
        endpoint = "https://export.arxiv.org/api/query"
        tokens = [token for token in re.findall(r"[A-Za-z0-9-]+", query.lower()) if token not in {"and", "or", "the", "of"}]
        # Requiring every token makes arXiv's fielded search nearly empty for
        # interdisciplinary queries. Keep the first robot anchor mandatory and
        # use a concept disjunction for the remaining terms; the exact
        # scientific query remains in the source-independent query plan.
        anchor = tokens[0] if tokens else "robot"
        concepts = tokens[1:6]
        arxiv_query = f"all:{anchor} AND (" + " OR ".join(f"all:{token}" for token in concepts) + ")" if concepts else f"all:{anchor}"
        params = {"search_query": arxiv_query, "start": 0, "max_results": limit, "sortBy": "relevance", "sortOrder": "descending"}
        return client.xml(source, "search", endpoint, params, query_id, window), endpoint, params
    if source == "semantic_scholar":
        endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": query, "limit": min(100, limit), "year": f"{item['from_year']}-{item['to_year']}", "fields": "title,abstract,year,authors,venue,externalIds,citationCount,openAccessPdf,url,paperId"}
        return client.json(source, "search", endpoint, params, query_id, window), endpoint, params
    if source == "openaire":
        endpoint = "https://api.openaire.eu/search/publications"
        params = {"keywords": query, "page": 1, "size": limit, "format": "json", "fromDateAccepted": start, "toDateAccepted": end}
        return client.json(source, "search", endpoint, params, query_id, window), endpoint, params
    if source == "dblp":
        endpoint = "https://dblp.org/search/publ/api"
        params = {"q": query, "h": limit, "f": 0, "format": "json"}
        return client.json(source, "search", endpoint, params, query_id, window), endpoint, params
    if source == "doaj":
        endpoint = "https://doaj.org/api/search/articles/" + quote(query, safe="")
        params = {"pageSize": limit, "page": 1}
        return client.json(source, "search", endpoint, params, query_id, window), endpoint, params
    if source == "core":
        endpoint = "https://api.core.ac.uk/v3/search/works"
        params = {"q": query, "limit": limit, "scroll": "false"}
        return client.json(source, "search", endpoint, params, query_id, window), endpoint, params
    raise ValueError(f"Unsupported search source: {source}")


def search_source(source: str, plan: list[dict[str, Any]], client: CachedClient, limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    searches: list[dict[str, Any]] = []
    raw_count = 0
    for item in plan:
        payload, endpoint, params = source_query(source, item, client, limit)
        if source == "arxiv":
            items, reported = parse_arxiv(payload)
        elif source == "crossref":
            items, reported = crossref_items(payload)
        elif source == "openalex":
            items, reported = openalex_items(payload)
        elif source == "semantic_scholar":
            items, reported = semantic_items(payload)
        elif source == "openaire":
            items, reported = openaire_items(payload)
        elif source == "dblp":
            items, reported = dblp_items(payload)
        elif source == "doaj":
            items, reported = doaj_items(payload)
        elif source == "core":
            items, reported = core_items(payload)
        else:
            items, reported = [], 0
        for raw in items:
            normalized = normalize_item(source, raw, item["query_id"], item["window_id"])
            if normalized:
                records.append(normalized)
        raw_count += len(items)
        terminal = [event for event in client.events if event.source == source and event.query_id == item["query_id"] and event.window_id == item["window_id"]]
        status = "ok" if payload is not None else (terminal[-1].status if terminal else "failed")
        error = terminal[-1].error if terminal and status not in {"ok", "cache_hit"} else ""
        searches.append(asdict(SearchEvent(item["query_id"], item["window_id"], source, item["query"], endpoint, status, reported, len(items), request_hash(endpoint, params), error, utc_now())))
    return records, searches, raw_count


def request_hash(endpoint: str, params: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def identity_key(row: dict[str, Any]) -> str:
    doi = norm_doi(row.get("doi_norm") or row.get("doi"))
    if doi:
        return f"doi:{doi}"
    return f"tav:{norm_title(row.get('title'))}|{safe_year(row.get('year'))}"


def unique_by_source(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    for row in records:
        source = clean(row.get("source"))
        key = identity_key(row)
        if key in seen[source]:
            continue
        seen[source].add(key)
        grouped[source].append(row)
    return dict(grouped)


def v1_match(row: dict[str, Any], v1: list[dict[str, Any]], by_doi: dict[str, dict[str, Any]], by_title: dict[str, list[dict[str, Any]]]) -> tuple[bool, str]:
    doi = norm_doi(row.get("doi_norm") or row.get("doi"))
    if doi and doi in by_doi:
        return True, "doi_exact"
    title = norm_title(row.get("title"))
    if title and title in by_title:
        return True, "title_exact"
    for candidate in v1:
        compatible, score = BOOT.compatible_metadata(candidate, row)
        if compatible and score >= 98.5:
            return True, f"metadata_{score:.1f}"
    return False, "new"


def reconciliation(v1: list[dict[str, Any]], records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    combined = [dict(row) for row in v1] + [dict(row) for row in records]
    canon, edges = BOOT.merge_records(combined)
    by_doi = {norm_doi(row.get("doi_norm") or row.get("doi")): row for row in v1 if norm_doi(row.get("doi_norm") or row.get("doi"))}
    by_title: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in v1:
        if norm_title(row.get("title")):
            by_title[norm_title(row.get("title"))].append(row)
    rows: list[dict[str, Any]] = []
    for row in records:
        matched, method = v1_match(row, v1, by_doi, by_title)
        rows.append({
            "source": row.get("source", ""),
            "source_record_id": row.get("source_record_id", ""),
            "query_id": row.get("query_id", ""),
            "window_id": row.get("window_id", ""),
            "candidate_id": row.get("candidate_id", ""),
            "identity_key": identity_key(row),
            "v1_match": "yes" if matched else "no",
            "match_method": method,
            "title": row.get("title", ""),
            "doi": row.get("doi_norm", ""),
        })
    return canon, edges, rows


def overlap_and_marginal(records: list[dict[str, Any]], source_order: list[str], v1: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped = unique_by_source(records)
    keys = {source: {identity_key(row) for row in rows} for source, rows in grouped.items()}
    overlap: list[dict[str, Any]] = []
    for left in source_order:
        for right in source_order:
            overlap.append({"source_left": left, "source_right": right, "intersection_records": len(keys.get(left, set()) & keys.get(right, set()))})
    v1_keys = {identity_key(row) for row in v1}
    running: set[str] = set(v1_keys)
    marginal: list[dict[str, Any]] = []
    for source in source_order:
        source_keys = keys.get(source, set())
        new_v1 = len(source_keys - v1_keys)
        marginal.append({
            "source": source,
            "raw_records": sum(1 for row in records if row.get("source") == source),
            "unique_records_within_source": len(source_keys),
            "new_vs_v1": new_v1,
            "marginal_new_after_previous_sources": len(source_keys - running),
            "cumulative_union_including_v1": len(running | source_keys),
        })
        running |= source_keys
    source_presence: list[dict[str, Any]] = []
    for key in sorted(set().union(*keys.values()) if keys else set()):
        source_presence.append({"identity_key": key, "sources": ";".join(source for source in source_order if key in keys.get(source, set())), "source_count": sum(key in keys.get(source, set()) for source in source_order)})
    return overlap, marginal, source_presence


def generate_manual_packs(plan: list[dict[str, Any]], config: dict[str, Any]) -> None:
    fields = ["database", "execution_id", "query_id", "window_id", "exact_query", "from_year", "to_year", "field_scope", "export_format", "access_status", "notes"]
    for database, scope, fmt, notes in [
        ("google_scholar", "all fields; title/abstract screening", "BibTeX or CSV with title, authors, year, DOI, URL, abstract, citation count", "Manual browser search only; do not use an automated scraper."),
        ("web_of_science", "Topic plus title/abstract/keywords; document types Article or Proceedings Paper", "Plain Text or tab-delimited with full record and cited references", "Institutional session/export required; no credential automation."),
        ("scopus", "TITLE-ABS-KEY", "CSV or RIS including EID, DOI, abstracts, keywords and references if available", "Institutional/API entitlement required; preserve query and export date."),
        ("ieee_xplore", "Metadata/Abstract; All Metadata", "RIS or CSV including DOI, abstract, keywords and document type", "Institutional/API entitlement may be required; use IEEE export controls."),
    ]:
        rows = []
        for item in plan:
            rows.append({
                "database": database,
                "execution_id": item["execution_id"],
                "query_id": item["query_id"],
                "window_id": item["window_id"],
                "exact_query": item["query"],
                "from_year": item["from_year"],
                "to_year": item["to_year"],
                "field_scope": scope,
                "export_format": fmt,
                "access_status": "manual_pending",
                "notes": notes,
            })
        write_csv(MANUAL / f"{database}_query_pack.csv", rows, fields)
        readme = f"""# {database} manual pack

Generated at {utc_now()} from `config/multisource_v2.yaml`.

This pack is a reproducible query and export checklist. It is not evidence
that the database was queried. The V2 executor does not scrape or automate
authenticated sessions for this source. After a human export, place the raw
file in `../inputs/{database}/`, record its export timestamp and hash, and use
the existing ingestion/audit process before merging it into a future
derivative.
"""
        (MANUAL / f"{database}_README.md").write_text(readme, encoding="utf-8")


def fulltext_queue(v2_rows: list[dict[str, Any]], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create a bounded, honest deep-evidence queue.

    Existing verified Stage 3 objects are eligible for close reading. New V2
    records are only marked as candidates for later legal acquisition.
    """
    queue: list[dict[str, Any]] = []
    if V1_EVIDENCE.exists():
        evidence = read_csv(V1_EVIDENCE)
        verified = [row for row in evidence if row.get("evidence_strength") == "fulltext_verified"]
        verified.sort(key=lambda row: (0 if row.get("scientific_role") == "CORE" else 1, row.get("candidate_id", "")))
        for row in verified[:60]:
            queue.append({
                "candidate_id": row.get("candidate_id", ""),
                "title": row.get("title", ""),
                "doi": row.get("doi", ""),
                "source_basis": "V1_stage3_verified_fulltext",
                "deep_reading_status": "eligible_existing_fulltext",
                "fulltext_local_path": row.get("fulltext_local_path", ""),
                "evidence_strength": "fulltext_verified",
                "author_verification_required": "yes",
            })
    already = {row["candidate_id"] for row in queue}
    unique_new: dict[str, dict[str, Any]] = {}
    for row in records:
        if row.get("candidate_id") in already or not clean(row.get("open_access_url")):
            continue
        unique_new.setdefault(identity_key(row), row)
    for row in sorted(unique_new.values(), key=lambda candidate: (candidate.get("year", "9999"), candidate.get("title", "")))[ : max(0, 60 - len(queue))]:
        queue.append({
            "candidate_id": row.get("candidate_id", ""),
            "title": row.get("title", ""),
            "doi": row.get("doi_norm", ""),
            "source_basis": row.get("source", ""),
            "deep_reading_status": "pending_legal_fulltext_acquisition",
            "fulltext_local_path": "",
            "open_access_url": row.get("open_access_url", ""),
            "evidence_strength": "metadata_only",
            "author_verification_required": "yes",
        })
    return queue


def coverage_report(
    campaign_id: str,
    plan: list[dict[str, Any]],
    source_order: list[str],
    source_states: list[dict[str, Any]],
    marginal: list[dict[str, Any]],
    v1_count: int,
    v2_count: int,
    canon_count: int,
    queue_count: int,
    screening_counts: dict[str, int],
    repair_rounds: int,
) -> str:
    lines = [
        "# Multisource V2 coverage and evidence report",
        "",
        f"Run UTC: {utc_now()}",
        f"Campaign: `{campaign_id}`",
        "",
        "## Scope",
        "",
        f"- Query executions planned: **{len(plan)}** across F1–F16 and configured date windows.",
        f"- V1 input candidates: **{v1_count}** (read-only input).",
        f"- V2 raw normalized records: **{v2_count}**.",
        f"- Reconciled derivative candidates: **{canon_count}**.",
        f"- Deep-evidence queue: **{queue_count}**; this is not a claim that all queued works were read.",
        f"- V2 title/abstract metadata screening: **{screening_counts.get('include_fulltext', 0)} include**, **{screening_counts.get('maybe_fulltext', 0)} maybe**, **{screening_counts.get('exclude', 0)} exclude**.",
        f"- Automatic repair rounds completed: **{repair_rounds}**; maximum allowed by protocol: **1**.",
        "",
        "## Source status",
        "",
        "| Source | Tier | Status | Raw | Unique | New vs V1 | Errors | Credential/access note |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for state in source_states:
        lines.append(f"| {state['source']} | {state['tier']} | {state['status']} | {state['raw_records']} | {state['unique_records']} | {state['new_vs_v1']} | {state['errors']} | {state['access_note']} |")
    lines += [
        "",
        "## Marginal yield",
        "",
        "The sequential marginal column is descriptive: it depends on the configured source order and uses DOI when present, otherwise normalized title plus year. It is not an estimate of database recall.",
        "",
        "| Source | Raw | Unique within source | New vs V1 | Marginal new after previous sources | Cumulative union incl. V1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in marginal:
        lines.append(f"| {row['source']} | {row['raw_records']} | {row['unique_records_within_source']} | {row['new_vs_v1']} | {row['marginal_new_after_previous_sources']} | {row['cumulative_union_including_v1']} |")
    lines += [
        "",
        "## Evidence boundary",
        "",
        "- Metadata discovery remains `evidence_status=not_evidence`; an OA URL is a retrieval lead only.",
        "- Existing V1 full-text objects are labelled as eligible for close reading, while new V2 records remain pending legal acquisition and author verification.",
        "- Google Scholar, WoS, Scopus and IEEE Xplore were not scraped or accessed automatically. Their packs are marked `manual_pending`.",
        "- CORE was attempted only when `CORE_API_KEY` was available; otherwise its state is `pending_credentials`.",
        "- A failed, empty or rate-limited API response is not interpreted as absence of literature.",
        "",
        "## Interpretation",
        "",
        "This campaign expands source diversity and auditability. It does not by itself establish saturation, novelty, convergence, optimality, mechanical feasibility or an integrated SP1–SP3 prior-art absence.",
    ]
    return "\n".join(lines) + "\n"


def write_source_reports(source_states: list[dict[str, Any]], searches: list[dict[str, Any]]) -> None:
    directory = REPORTS / "sources"
    directory.mkdir(parents=True, exist_ok=True)
    for state in source_states:
        source = state["source"]
        source_searches = [row for row in searches if row.get("source") == source]
        status_counts = Counter(row.get("status", "") for row in source_searches)
        queries = len(source_searches)
        lines = [
            f"# Source report: {source}",
            "",
            f"Generated UTC: {utc_now()}",
            "",
            f"- Tier: **{state.get('tier', '')}**",
            f"- Status: **{state.get('status', '')}**",
            f"- Access note: {state.get('access_note', '')}",
            f"- Planned/observed search events: **{queries}**",
            f"- Raw records: **{state.get('raw_records', 0)}**",
            f"- Unique records within source: **{state.get('unique_records', 0)}**",
            f"- New identity keys vs V1: **{state.get('new_vs_v1', 0)}**",
            f"- Terminal/error events: **{state.get('errors', 0)}**",
            "",
            "## Search event statuses",
            "",
        ]
        lines.extend(f"- `{status}`: {count}" for status, count in sorted(status_counts.items()) if status)
        if not status_counts:
            lines.append("- no search event; source was not automated in this run")
        lines += [
            "",
            "## Interpretation boundary",
            "",
            "Counts are provider responses after the configured query translation.",
            "A zero, failed, blocked or rate-limited response is not interpreted as absence of literature.",
            "Records remain metadata candidates and do not support detailed scientific claims without legal full-text acquisition and close reading.",
        ]
        (directory / f"{source}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_claim_ledger_v2(
    v1_count: int,
    raw_count: int,
    reconciled_count: int,
    unpaywall_count: int,
    citation_count: int,
    source_artifacts: str,
) -> None:
    rows = [
        {
            "claim_id": "V2-C01",
            "claim_text": f"La campaña V2 produjo {raw_count} registros normalizados y un derivado reconciliado de {reconciled_count} candidatos a partir de {v1_count} candidatos V1.",
            "claim_type": "review_descriptive",
            "support_status": "supported",
            "evidence_level": "artifact_derived",
            "source_artifacts": source_artifacts,
            "allowed_use": "describir el flujo y el tamaño del derivado",
            "notes": "No es una afirmación de recall, saturación ni impacto científico.",
        },
        {
            "claim_id": "V2-C02",
            "claim_text": "Las fuentes producen rendimientos marginales y solapamientos distintos bajo la celosía F1–F16.",
            "claim_type": "review_descriptive",
            "support_status": "supported",
            "evidence_level": "artifact_derived",
            "source_artifacts": "data/processed/source_marginal_yield.csv;data/processed/source_overlap_matrix.csv;logs/search_events.csv",
            "allowed_use": "comparar descriptivamente proveedores y priorizar revisión",
            "notes": "El rendimiento depende del orden de fuentes y no estima cobertura total.",
        },
        {
            "claim_id": "V2-C03",
            "claim_text": f"Se registraron {citation_count} aristas de una comprobación one-hop acotada sobre anclas DOI V1 mediante OpenCitations.",
            "claim_type": "citation_graph_descriptive",
            "support_status": "supported",
            "evidence_level": "artifact_derived",
            "source_artifacts": "data/processed/one_hop_citation_edges.csv;logs/api_events.csv",
            "allowed_use": "descubrimiento y priorización de lectura",
            "notes": "Una arista de citación no demuestra relevancia, soporte de claim ni novedad.",
        },
        {
            "claim_id": "V2-C04",
            "claim_text": f"Unpaywall devolvió {unpaywall_count} respuestas de enriquecimiento DOI dentro del límite configurado.",
            "claim_type": "access_descriptive",
            "support_status": "supported",
            "evidence_level": "artifact_derived",
            "source_artifacts": "data/processed/unpaywall_enrichment.csv;logs/api_events.csv",
            "allowed_use": "priorizar adquisición OA legal",
            "notes": "Una ubicación OA requiere verificación de identidad, licencia, versión y contenido.",
        },
        {
            "claim_id": "V2-C05",
            "claim_text": "Google Scholar, WoS, Scopus e IEEE Xplore no fueron automatizados; se generaron paquetes manuales de consulta/exportación.",
            "claim_type": "access_boundary",
            "support_status": "supported",
            "evidence_level": "protocol_and_artifact",
            "source_artifacts": "manual-packs/;reports/manual_access_boundary.md",
            "allowed_use": "declarar una limitación de cobertura",
            "notes": "La no automatización no equivale a ausencia de registros en esas bases.",
        },
    ]
    write_csv(PROCESSED / "claim_source_matrix_v2.csv", rows)
    lines = [
        "# V2 claim ledger",
        "",
        "Ledger reconstruido desde los artefactos de la campaña. Los claims son descriptivos del proceso y conservan una frontera explícita contra claims científicos fuertes.",
        "",
    ]
    for row in rows:
        lines += [
            f"## {row['claim_id']}",
            "",
            f"**Claim:** {row['claim_text']}",
            f"**Estado:** `{row['support_status']}`; nivel `{row['evidence_level']}`.",
            f"**Artefactos:** `{row['source_artifacts']}`",
            f"**Uso permitido:** {row['allowed_use']}",
            f"**Límite:** {row['notes']}",
            "",
        ]
    (REPORTS / "claim_ledger_v2.md").write_text("\n".join(lines), encoding="utf-8")


def write_figures(marginal: list[dict[str, Any]], overlap: list[dict[str, Any]], source_order: list[str]) -> None:
    """Render data-derived QA figures when matplotlib is available."""
    figures = V2_ROOT / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        (figures / "README.md").write_text("matplotlib is unavailable; regenerate figures from source_marginal_yield.csv and source_overlap_matrix.csv.\n", encoding="utf-8")
        return
    selected = [row for row in marginal if row.get("source") in source_order]
    labels = [row["source"] for row in selected]
    values = [int(row.get("marginal_new_after_previous_sources") or 0) for row in selected]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(labels, values, color="#2f6f9f")
    ax.set_ylabel("New identity keys after previous sources")
    ax.set_title("V2 source marginal yield (descriptive)")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(figures / "source_marginal_yield.png", dpi=160)
    plt.close(fig)

    matrix = np.zeros((len(source_order), len(source_order)), dtype=int)
    lookup = {(row["source_left"], row["source_right"]): int(row.get("intersection_records") or 0) for row in overlap}
    for i, left in enumerate(source_order):
        for j, right in enumerate(source_order):
            matrix[i, j] = lookup.get((left, right), 0)
    fig, ax = plt.subplots(figsize=(8.5, 7))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(source_order)), source_order, rotation=45, ha="right")
    ax.set_yticks(range(len(source_order)), source_order)
    ax.set_title("V2 source overlap by identity key")
    fig.colorbar(image, ax=ax, label="Intersection")
    fig.tight_layout()
    fig.savefig(figures / "source_overlap_heatmap.png", dpi=160)
    plt.close(fig)


def write_deep_evidence_report(queue: list[dict[str, Any]]) -> None:
    close_reading_path = ACADEMIC_REVIEW / "data" / "processed" / "prior_art_close_reading.csv"
    close_reading_count = len(read_csv(close_reading_path)) if close_reading_path.exists() else 0
    existing = sum(1 for row in queue if row.get("deep_reading_status") == "eligible_existing_fulltext")
    pending = sum(1 for row in queue if row.get("deep_reading_status") == "pending_legal_fulltext_acquisition")
    report = f"""# Deep-evidence V2 boundary

Generated UTC: {utc_now()}

- Bounded queue target: **60** records.
- Queue rows linked to existing V1 verified full text: **{existing}**.
- Queue rows awaiting legal V2 full-text acquisition: **{pending}**.
- Existing manually documented close readings inherited from V1: **{close_reading_count}**.

The queue is a prioritization artifact, not proof that every row was closely
read. The inherited close-reading ledger remains the only set with explicit
source-specific support/limit prose. Structural coding or an OA URL cannot be
promoted to a detailed method, result, stability, optimality or novelty claim
without author verification of the local text.
"""
    (REPORTS / "deep_evidence_boundary.md").write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="reuse successful raw responses")
    parser.add_argument("--force", action="store_true", help="refresh cached responses")
    parser.add_argument("--sources", default="", help="comma-separated source subset; default is all configured sources")
    parser.add_argument("--limit-per-query", type=int, default=25)
    parser.add_argument("--skip-citations", action="store_true", help="skip Tier-B citation enrichment")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    env = dotenv_values(ENV)
    email = clean(env.get("CONTACT_EMAIL") or "")
    if not email:
        raise SystemExit("CONTACT_EMAIL is required for responsible scholarly API access.")
    keys = {name: clean(env.get(name) or os.environ.get(name) or "") for name in [
        "OPENALEX_API_KEY", "SEMANTIC_SCHOLAR_API_KEY", "CORE_API_KEY", "OPENCITATIONS_ACCESS_TOKEN",
    ]}
    plan = query_plan(config)
    requested_sources = [source.strip() for source in args.sources.split(",") if source.strip()] if args.sources else []
    source_order = [source for source, details in config["sources"].items() if details.get("enabled") and details.get("kind") not in {"oa_enrichment", "citation_graph"}]
    if requested_sources:
        source_order = [source for source in source_order if source in requested_sources]
    client = CachedClient(email, keys, force=args.force or not args.resume, arxiv_delay=float(config["execution"].get("arxiv_delay_seconds", 3.1)))
    all_records: list[dict[str, Any]] = []
    search_logs: list[dict[str, Any]] = []
    source_states: list[dict[str, Any]] = []
    v1 = read_csv(V1_CORPUS) if V1_CORPUS.exists() else []

    for source in source_order:
        details = config["sources"][source]
        credential = details.get("credential")
        if credential and not keys.get(credential, ""):
            source_states.append({"source": source, "tier": details.get("tier", ""), "status": "pending_credentials", "raw_records": 0, "unique_records": 0, "new_vs_v1": 0, "errors": 0, "access_note": f"{credential} absent"})
            continue
        try:
            records, searches, raw_count = search_source(source, plan, client, max(1, min(100, args.limit_per_query)))
        except Exception as exc:
            records, searches, raw_count = [], [], 0
            search_logs.append(asdict(SearchEvent("", "", source, "", "", "adapter_error", error=f"{type(exc).__name__}: {exc}", executed_at_utc=utc_now())))
        all_records.extend(records)
        search_logs.extend(searches)
        source_unique = unique_by_source(records).get(source, [])
        errors = sum(1 for event in client.events if event.source == source and event.status in {"failed", "forbidden", "auth_required", "parse_error", "network_blocked", "rate_limited"})
        statuses = {event.status for event in client.events if event.source == source}
        status = "ok" if records or (statuses and statuses <= {"ok", "cache_hit"}) else ("partial" if statuses else "failed")
        if errors:
            if not records and "rate_limited" in statuses:
                status = "rate_limited"
            elif not records and "network_blocked" in statuses:
                status = "network_blocked"
            else:
                status = "partial" if records else "failed"
        source_states.append({"source": source, "tier": details.get("tier", ""), "status": status, "raw_records": raw_count, "unique_records": len(source_unique), "new_vs_v1": 0, "errors": errors, "access_note": "public API attempted"})

    # Apply the frozen V1 deterministic title/abstract screen to the new
    # metadata only. This is a triage state, never scientific evidence.
    screened_records = [STAGE1B.screen_record(row) for row in all_records]
    screening_counts = dict(Counter(row.get("screening_decision", "") for row in screened_records))
    all_records = screened_records

    # Tier B: enrich a bounded set of DOI records with OA and citation data.
    enrichment_records: list[dict[str, Any]] = []
    if config["sources"].get("unpaywall", {}).get("enabled"):
        doi_rows: dict[str, dict[str, Any]] = {}
        for row in all_records:
            doi = norm_doi(row.get("doi_norm"))
            if doi:
                doi_rows.setdefault(doi, row)
        for doi, row in list(doi_rows.items())[: int(config["execution"].get("max_unpaywall_records", 500))]:
            data = client.json("unpaywall", "oa_enrichment", f"https://api.unpaywall.org/v2/{quote(doi, safe='')}", {}, "UNPAYWALL", "all")
            if not isinstance(data, dict):
                continue
            best = data.get("best_oa_location") or {}
            enrichment_records.append({"source": "unpaywall", "doi": doi, "candidate_id": row.get("candidate_id", ""), "is_oa": data.get("is_oa", ""), "oa_status": data.get("oa_status", ""), "best_oa_url": best.get("url_for_pdf") or best.get("url") or "", "license": best.get("license") or "", "host_type": best.get("host_type") or "", "version": best.get("version") or ""})

    citation_rows: list[dict[str, Any]] = []
    if not args.skip_citations and config["sources"].get("opencitations", {}).get("enabled"):
        anchors: list[dict[str, Any]] = []
        for row in v1:
            if norm_doi(row.get("doi_norm")):
                anchors.append(row)
        anchors = anchors[: int(config["execution"].get("max_citation_anchors", 20))]
        for anchor in anchors:
            doi = norm_doi(anchor.get("doi_norm"))
            for direction in ("references", "citations"):
                data = client.json("opencitations", f"one_hop_{direction}", f"https://api.opencitations.net/index/v2/{direction}/doi:{quote(doi, safe='')}", {}, "ONEHOP", "all")
                if isinstance(data, list):
                    for edge in data:
                        citation_rows.append({"anchor_candidate_id": anchor.get("candidate_id", ""), "anchor_doi": doi, "direction": direction, "oci": value_of(edge.get("oci")), "citing": value_of(edge.get("citing")), "cited": value_of(edge.get("cited")), "creation": value_of(edge.get("creation")), "timespan": value_of(edge.get("timespan")), "source": "opencitations"})

    canon, dedup_edges, reconciliation_rows = reconciliation(v1, all_records)
    # Tier-B services enrich DOI/citation metadata and are intentionally not
    # mixed into the discovery-source marginal-yield denominator.
    overlap, marginal, presence = overlap_and_marginal(all_records, source_order, v1)
    v1_keys = {identity_key(row) for row in v1}
    for state in source_states:
        marginal_row = next((row for row in marginal if row["source"] == state["source"]), None)
        if marginal_row:
            state["new_vs_v1"] = marginal_row["new_vs_v1"]

    generate_manual_packs(plan, config)
    queue = fulltext_queue(canon, all_records)

    plan_fields = ["execution_id", "query_id", "window_id", "label", "query", "axes", "from_year", "to_year"]
    write_csv(PROCESSED / "query_plan.csv", plan, plan_fields)
    write_csv(PROCESSED / "candidate_records_v2.csv", all_records)
    write_csv(PROCESSED / "candidate_corpus_v2_reconciled.csv", canon)
    write_csv(PROCESSED / "deep_evidence_queue.csv", queue)
    write_csv(PROCESSED / "fulltext_queue_v2_screened.csv", [row for row in all_records if row.get("screening_decision") in {"include_fulltext", "maybe_fulltext"} and clean(row.get("open_access_url"))])
    write_csv(PROCESSED / "unpaywall_enrichment.csv", enrichment_records)
    write_csv(PROCESSED / "one_hop_citation_edges.csv", citation_rows)
    write_csv(LOGS / "api_events.csv", [asdict(event) for event in client.events], list(ApiEvent.__dataclass_fields__.keys()))
    write_csv(LOGS / "search_events.csv", search_logs, list(SearchEvent.__dataclass_fields__.keys()))
    write_csv(LOGS / "reconciliation_log.csv", reconciliation_rows)
    write_csv(LOGS / "dedup_edges.csv", dedup_edges, ["candidate_id", "source", "query", "relation"])
    write_csv(PROCESSED / "source_overlap_matrix.csv", overlap)
    write_csv(PROCESSED / "source_marginal_yield.csv", marginal)
    write_csv(PROCESSED / "source_presence.csv", presence)

    source_states.extend([
        {"source": "unpaywall", "tier": "B", "status": "partial" if enrichment_records else "failed_or_empty", "raw_records": len(enrichment_records), "unique_records": len(enrichment_records), "new_vs_v1": 0, "errors": sum(1 for event in client.events if event.source == "unpaywall" and event.status in {"failed", "forbidden", "auth_required", "parse_error", "network_blocked", "rate_limited"}), "access_note": "DOI enrichment; not a discovery source"},
        {"source": "opencitations", "tier": "B", "status": "partial" if citation_rows else "failed_or_empty", "raw_records": len(citation_rows), "unique_records": len(citation_rows), "new_vs_v1": 0, "errors": sum(1 for event in client.events if event.source == "opencitations" and event.status in {"failed", "forbidden", "auth_required", "parse_error", "network_blocked", "rate_limited"}), "access_note": "bounded one-hop graph on V1 DOI anchors"},
    ])
    # The Tier-B rows are bounded enrichments, not an additional discovery
    # corpus. Make that explicit in their status labels.
    for state in source_states:
        if state["source"] in {"unpaywall", "opencitations"} and state["errors"] == 0 and state["raw_records"]:
            state["status"] = "ok_bounded"
    for source in ("google_scholar", "web_of_science", "scopus", "ieee_xplore"):
        source_states.append({"source": source, "tier": "manual", "status": "manual_pending", "raw_records": 0, "unique_records": 0, "new_vs_v1": 0, "errors": 0, "access_note": "manual query/export pack generated; no automation"})
    (REPORTS / "coverage_report.md").write_text(coverage_report(config["campaign_id"], plan, source_order, source_states, marginal, len(v1), len(all_records), len(canon), len(queue), screening_counts, 0), encoding="utf-8")
    (REPORTS / "manual_access_boundary.md").write_text("""# Manual-access boundary

The V2 executor intentionally does not scrape Google Scholar or automate
authenticated Web of Science, Scopus or IEEE Xplore sessions. Query and export
instructions are in `manual-packs/`. This is an access boundary, not a claim
that those databases contain no additional records.

The WoS in-app browser session remains available for a human institutional
export. No credentials were entered by this campaign.
""", encoding="utf-8")
    write_source_reports(source_states, search_logs)
    write_claim_ledger_v2(
        len(v1),
        len(all_records),
        len(canon),
        len(enrichment_records),
        len(citation_rows),
        "data/processed/candidate_records_v2.csv;data/processed/candidate_corpus_v2_reconciled.csv",
    )
    write_figures(marginal, overlap, source_order)
    write_deep_evidence_report(queue)

    generated = [
        path
        for path in V2_ROOT.rglob("*")
        if path.is_file()
        and path.name != "campaign_manifest.json"
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    ]
    manifest = {
        "campaign_id": config["campaign_id"],
        "protocol_version": config["protocol_version"],
        "created_at_utc": utc_now(),
        "status": "completed_with_explicit_access_boundaries",
        "v1_input": {"path": str(V1_CORPUS.relative_to(ACADEMIC_REVIEW)), "sha256": sha256(V1_CORPUS) if V1_CORPUS.exists() else "missing", "rows": len(v1)},
        "query_plan_rows": len(plan),
        "sources_attempted": source_order,
        "sources_not_automated": ["google_scholar", "web_of_science", "scopus", "ieee_xplore"],
        "repair_rounds_completed": 0,
        "counts": {"raw_records": len(all_records), "reconciled_candidates": len(canon), "deep_evidence_queue": len(queue), "screened_fulltext_queue": sum(1 for row in all_records if row.get("screening_decision") in {"include_fulltext", "maybe_fulltext"} and clean(row.get("open_access_url"))), "screening": screening_counts, "unpaywall_rows": len(enrichment_records), "one_hop_edges": len(citation_rows)},
        "artifacts": {str(path.relative_to(V2_ROOT)): sha256(path) for path in sorted(generated)},
        "limitations": [
            "A provider error, empty response or missing credential is not evidence of zero literature.",
            "Search endpoints and coverage change over time; repeat runs are bound to the recorded timestamps and raw-response hashes.",
            "New metadata and OA URLs require legal acquisition and close reading before scientific claims.",
        ],
    }
    (MANIFESTS / "campaign_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print((REPORTS / "coverage_report.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
