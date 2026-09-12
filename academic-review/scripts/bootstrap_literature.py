from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import time
import unicodedata
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import pandas as pd
import requests
import yaml
from dotenv import dotenv_values
from rapidfuzz.fuzz import ratio

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / "inputs"
CACHE = BASE / "cache"
RAW = BASE / "data" / "raw"
INTERIM = BASE / "data" / "interim"
OUTPUT = BASE / "data" / "processed"
LOGS = BASE / "logs"
REPORTS = BASE / "reports"
CONFIG = BASE / "config" / "search_protocol.yaml"
ENV = BASE / ".env.literature"
OUTPUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)
INTERIM.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

NOW = datetime.now(timezone.utc)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm_doi(v: Any) -> str:
    if v is None:
        return ""
    s = str(v).strip().lower()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s)
    s = re.sub(r"^doi:\s*", "", s)
    return s.strip(" .;,)")


def norm_title(v: Any) -> str:
    if v is None:
        return ""
    s = unicodedata.normalize("NFKD", str(v))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_authors(v: Any) -> str:
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v).strip().lower())


def safe_year(v: Any) -> str:
    if v is None:
        return ""
    m = re.search(r"(?:19|20)\d{2}", str(v))
    return m.group(0) if m else ""


def stable_id(title: str, year: str, doi: str, authors: str = "", venue: str = "") -> str:
    base = f"doi:{doi}" if doi else f"tav:{norm_title(title)}|{year}|{norm_authors(authors)}|{norm_title(venue)}"
    return "C" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:12].upper()


def join_unique(values: Iterable[str]) -> str:
    out = []
    seen = set()
    for v in values:
        v = (v or "").strip()
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return ";".join(out)


def first_author(value: str) -> str:
    value = (value or "").split(";")[0].strip().lower()
    if not value:
        return ""
    if "," in value:
        surname, given = value.split(",", 1)
        initial = next((char for char in given if char.isalpha()), "")
        return f"{norm_title(surname)}|{initial}"
    tokens = [token for token in re.findall(r"[a-z]+", value) if token]
    return f"{tokens[-1]}|{tokens[0][0]}" if tokens else ""


def compatible_metadata(seed: dict[str, Any], candidate: dict[str, Any]) -> tuple[bool, float]:
    title_score = ratio(seed.get("title_norm", ""), candidate.get("title_norm", ""))
    if title_score < 94:
        return False, title_score
    sy, cy = safe_year(seed.get("year", "")), safe_year(candidate.get("year", ""))
    if sy and cy and abs(int(sy) - int(cy)) > 1:
        return False, title_score
    sa, ca = first_author(seed.get("authors", "")), first_author(candidate.get("authors", ""))
    if sa and ca and sa != ca:
        return False, title_score
    sv, cv = norm_title(seed.get("venue", "")), norm_title(candidate.get("venue", ""))
    if sv and cv and ratio(sv, cv) < 80:
        return False, title_score
    return title_score >= 98.5, title_score


@dataclass
class ApiEvent:
    source: str
    request_kind: str
    request_fingerprint: str
    status: str
    http_status: str = ""
    attempts: int = 0
    error: str = ""
    cache_file: str = ""
    url: str = ""
    params: str = ""
    elapsed_ms: int = 0
    retry_number: int = 0
    retrieved_at_utc: str = ""


@dataclass
class SearchEvent:
    query_id: str
    source: str
    exact_query: str
    timestamp_utc: str
    result_count: int = 0
    returned_count: int = 0
    pagination_mode: str = "single_page"
    filters: str = ""
    request_hash: str = ""
    status: str = ""
    error: str = ""


def request_hash(url: str, params: dict[str, Any]) -> str:
    key = json.dumps({"url": url, "params": params}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def log_params(params: dict[str, Any]) -> str:
    """Serialize request parameters without persisting contact/API secrets."""
    safe = dict(params)
    for key in ("mailto", "api_key", "OPENALEX_API_KEY", "SEMANTIC_SCHOLAR_API_KEY", "CORE_API_KEY"):
        if key in safe:
            safe[key] = "[REDACTED]"
    return json.dumps(safe, sort_keys=True, ensure_ascii=False)


def openalex_search_query(terms: str) -> str:
    """Translate the protocol's Boolean text into OpenAlex full-text syntax.

    The canonical query remains in ``SearchEvent.exact_query``. OpenAlex's
    ``search`` parameter is full-text search and rejects the protocol's
    Boolean/wildcard expression, so only source syntax is adapted here.
    """
    translated = re.sub(r"\b(?:AND|OR)\b", " ", terms, flags=re.IGNORECASE)
    translated = translated.replace("*", "")
    translated = re.sub(r"[\"()]", " ", translated)
    return re.sub(r"\s+", " ", translated).strip()


class CachedHttp:
    def __init__(self, email: str, *, force: bool = False, api_keys: dict[str, str] | None = None):
        self.email = email
        self.force = force
        self.api_keys = api_keys or {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"MROB-Academic-Review/1.0 (mailto:{email})",
            "Accept": "application/json",
        })
        self.events: list[ApiEvent] = []
        self.last_request_at: dict[str, float] = {}
        self.source_delay = {"crossref": 0.55, "openalex": 0.35}

    def _cache_path(self, source: str, key: str) -> Path:
        d = CACHE / source
        d.mkdir(parents=True, exist_ok=True)
        fp = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return d / f"{fp}.json"

    def get_json(self, source: str, kind: str, url: str, params: dict[str, Any] | None = None, max_attempts: int = 5) -> dict[str, Any] | None:
        params = params or {}
        key = json.dumps({"url": url, "params": params}, sort_keys=True, ensure_ascii=False)
        cache_path = self._cache_path(source, key)
        req_fp = cache_path.stem
        params_text = log_params(params)
        if cache_path.exists() and not self.force:
            try:
                data = json.loads(cache_path.read_text(encoding="utf-8"))
                status = "not_found" if data.get("_status") == 404 else "cache_hit"
                self.events.append(ApiEvent(source, kind, req_fp, status, http_status="404" if status == "not_found" else "", cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, retrieved_at_utc=utc_now()))
                return None if status == "not_found" else data
            except Exception as e:
                self.events.append(ApiEvent(source, kind, req_fp, "cache_corrupt", error=str(e), cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, retrieved_at_utc=utc_now()))

        last_error = ""
        for attempt in range(1, max_attempts + 1):
            delay = self.source_delay.get(source, 0.25)
            since = time.monotonic() - self.last_request_at.get(source, 0.0)
            if since < delay:
                time.sleep(delay - since)
            started = time.monotonic()
            try:
                request_params = dict(params)
                if source == "openalex" and self.api_keys.get("OPENALEX_API_KEY"):
                    request_params["api_key"] = self.api_keys["OPENALEX_API_KEY"]
                if source == "crossref":
                    request_params.setdefault("mailto", self.email)
                r = self.session.get(url, params=request_params, timeout=(30, 30))
                self.last_request_at[source] = time.monotonic()
                elapsed_ms = int((time.monotonic() - started) * 1000)
                if r.status_code == 429:
                    wait = r.headers.get("Retry-After")
                    try:
                        delay = min(60.0, float(wait)) if wait else min(30.0, 2 ** attempt + random.random())
                    except ValueError:
                        delay = min(30.0, 2 ** attempt + random.random())
                    last_error = f"429 rate limit; wait {delay}s"
                    self.events.append(ApiEvent(source, kind, req_fp, "retry", http_status="429", attempts=attempt, error=last_error, cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, elapsed_ms=elapsed_ms, retry_number=attempt, retrieved_at_utc=utc_now()))
                    time.sleep(delay)
                    continue
                if 500 <= r.status_code < 600:
                    last_error = f"HTTP {r.status_code}"
                    self.events.append(ApiEvent(source, kind, req_fp, "retry", http_status=str(r.status_code), attempts=attempt, error=last_error, cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, elapsed_ms=elapsed_ms, retry_number=attempt, retrieved_at_utc=utc_now()))
                    time.sleep(min(20.0, 2 ** attempt + random.random()))
                    continue
                if r.status_code in {401, 403}:
                    status = "auth_required" if r.status_code == 401 else "forbidden"
                    self.events.append(ApiEvent(source, kind, req_fp, status, http_status=str(r.status_code), attempts=attempt, error=f"SOURCE_{status.upper()}", cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, elapsed_ms=elapsed_ms, retrieved_at_utc=utc_now()))
                    return None
                if r.status_code == 404:
                    self.events.append(ApiEvent(source, kind, req_fp, "not_found", http_status="404", attempts=attempt, cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, elapsed_ms=elapsed_ms, retrieved_at_utc=utc_now()))
                    cache_path.write_text(json.dumps({"_status": 404, "_url": r.url}, ensure_ascii=False, indent=2), encoding="utf-8")
                    return None
                if 400 <= r.status_code < 500:
                    self.events.append(ApiEvent(source, kind, req_fp, "failed", http_status=str(r.status_code), attempts=attempt, error=f"HTTP {r.status_code}", cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, elapsed_ms=elapsed_ms, retrieved_at_utc=utc_now()))
                    return None
                r.raise_for_status()
                try:
                    data = r.json()
                except ValueError as e:
                    raw_path = RAW / source / f"{req_fp}.response"
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_path.write_bytes(r.content)
                    self.events.append(ApiEvent(source, kind, req_fp, "parse_error", http_status=str(r.status_code), attempts=attempt, error=f"PARSE_ERROR: {e}", cache_file=str(raw_path.relative_to(BASE)), url=url, params=params_text, elapsed_ms=elapsed_ms, retrieved_at_utc=utc_now()))
                    return None
                cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                self.events.append(ApiEvent(source, kind, req_fp, "ok", http_status=str(r.status_code), attempts=attempt, cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, elapsed_ms=elapsed_ms, retry_number=attempt - 1, retrieved_at_utc=utc_now()))
                return data
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                if attempt < max_attempts:
                    self.events.append(ApiEvent(source, kind, req_fp, "retry", attempts=attempt, error=last_error, cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, retry_number=attempt, retrieved_at_utc=utc_now()))
                    time.sleep(min(20.0, 2 ** attempt + random.random()))
        self.events.append(ApiEvent(source, kind, req_fp, "failed", attempts=max_attempts, error=last_error, cache_file=str(cache_path.relative_to(BASE)), url=url, params=params_text, retry_number=max_attempts - 1, retrieved_at_utc=utc_now()))
        return None


def load_seed() -> list[dict[str, Any]]:
    p = INPUT / "legacy" / "legacy_seed_references.csv"
    df = pd.read_csv(p, dtype=str).fillna("")
    out = []
    for _, r in df.iterrows():
        title = r["title"].strip()
        authors = r.get("authors", "")
        venue = r.get("venue", "")
        doi = norm_doi(r.get("doi", ""))
        year = safe_year(r.get("year", ""))
        raw = {str(k): str(v) for k, v in r.to_dict().items()}
        out.append({
            "candidate_id": stable_id(title, year, doi, authors, venue),
            "title": title,
            "title_original": title,
            "title_norm": norm_title(title),
            "authors": authors,
            "authors_original": authors,
            "authors_norm": norm_authors(authors),
            "year": year,
            "year_original": r.get("year", ""),
            "venue": venue,
            "venue_original": venue,
            "doi": doi,
            "doi_original": r.get("doi", ""),
            "doi_norm": doi,
            "abstract": "",
            "document_type": "",
            "source_ids": "",
            "provenance": "legacy_review",
            "provenance_sources": "legacy_review",
            "provenance_queries": "legacy_seed",
            "verification_status": "unverified_seed",
            "metadata_verification_status": "not_checked",
            "evidence_status": "not_evidence",
            "screening_status": "pending",
            "legacy_seed_id": r.get("legacy_seed_id", ""),
            "wos_ut": "",
            "citation_count": "",
            "citation_count_source": "",
            "retrieved_at_utc": "",
            "duplicate_status": "unique",
            "dedup_status": "unique",
            "dedup_parent_candidate_id": "",
            "notes": r.get("notes", ""),
            "seed_raw": json.dumps(raw, ensure_ascii=False, sort_keys=True),
        })
    return out


def crossref_item_to_record(item: dict[str, Any], query_id: str) -> dict[str, Any]:
    title = " ".join(item.get("title") or []).strip()
    doi = norm_doi(item.get("DOI", ""))
    issued = item.get("published-print") or item.get("published-online") or item.get("issued") or {}
    parts = issued.get("date-parts") or []
    raw_year = parts[0][0] if parts and parts[0] else ""
    year = safe_year(raw_year)
    authors = []
    for a in item.get("author") or []:
        name = " ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
        if name:
            authors.append(name)
    venue = " ".join(item.get("container-title") or []).strip()
    return {
            "candidate_id": stable_id(title, year, doi, "; ".join(authors), venue),
            "title": title,
            "title_original": title,
            "title_norm": norm_title(title),
            "authors": "; ".join(authors),
            "authors_original": "; ".join(authors),
            "authors_norm": norm_authors("; ".join(authors)),
            "year": year,
            "year_original": year,
            "venue": venue,
            "venue_original": venue,
            "doi": doi,
            "doi_original": item.get("DOI", ""),
            "doi_norm": doi,
        "abstract": re.sub(r"<[^>]+>", " ", item.get("abstract", "") or "").strip(),
        "document_type": item.get("type", "") or "",
        "source_ids": f"crossref:{doi}" if doi else "",
            "provenance": "crossref",
            "provenance_sources": "crossref",
            "provenance_queries": query_id,
            "verification_status": "metadata_verified" if doi and title else "metadata_partial",
            "metadata_verification_status": "metadata_verified" if doi and title else "metadata_partial",
            "evidence_status": "not_evidence",
            "screening_status": "pending",
        "legacy_seed_id": "",
        "wos_ut": "",
        "citation_count": item.get("is-referenced-by-count", ""),
        "citation_count_source": "crossref" if item.get("is-referenced-by-count") is not None else "",
        "retrieved_at_utc": utc_now(),
            "duplicate_status": "unique",
            "dedup_status": "unique",
        "dedup_parent_candidate_id": "",
        "notes": "",
    }


def openalex_item_to_record(item: dict[str, Any], query_id: str) -> dict[str, Any]:
    title = item.get("display_name") or item.get("title") or ""
    doi = norm_doi(item.get("doi", ""))
    year = safe_year(item.get("publication_year", ""))
    authors = []
    for au in item.get("authorships") or []:
        name = ((au.get("author") or {}).get("display_name") or "").strip()
        if name:
            authors.append(name)
    primary = item.get("primary_location") or {}
    source = primary.get("source") or {}
    venue = source.get("display_name") or ""
    ids = item.get("ids") or {}
    openalex_id = ids.get("openalex") or item.get("id") or ""
    return {
            "candidate_id": stable_id(title, year, doi, "; ".join(authors), venue),
            "title": title,
            "title_original": title,
            "title_norm": norm_title(title),
            "authors": "; ".join(authors),
            "authors_original": "; ".join(authors),
            "authors_norm": norm_authors("; ".join(authors)),
            "year": year,
            "year_original": year,
            "venue": venue,
            "venue_original": venue,
            "doi": doi,
            "doi_original": item.get("doi", ""),
        "doi_norm": doi,
        "abstract": "",  # OpenAlex inverted abstract is intentionally not reconstructed in Stage 1 baseline.
        "document_type": item.get("type", "") or "",
        "source_ids": f"openalex:{openalex_id}" if openalex_id else "",
            "provenance": "openalex",
            "provenance_sources": "openalex",
            "provenance_queries": query_id,
            "verification_status": "metadata_verified" if title and (doi or openalex_id) else "metadata_partial",
            "metadata_verification_status": "metadata_verified" if title and (doi or openalex_id) else "metadata_partial",
            "evidence_status": "not_evidence",
            "screening_status": "pending",
        "legacy_seed_id": "",
        "wos_ut": "",
        "citation_count": item.get("cited_by_count", ""),
        "citation_count_source": "openalex" if item.get("cited_by_count") is not None else "",
        "retrieved_at_utc": utc_now(),
            "duplicate_status": "unique",
            "dedup_status": "unique",
        "dedup_parent_candidate_id": "",
        "notes": "",
    }


def enrich_seeds(records: list[dict[str, Any]], http: CachedHttp, email: str) -> list[dict[str, Any]]:
    enriched = []
    for rec in records:
        doi = rec["doi_norm"]
        item = None
        if doi:
            data = http.get_json("crossref", "seed_doi", f"https://api.crossref.org/works/{quote(doi, safe='')}", params={"mailto": email})
            if data and isinstance(data.get("message"), dict):
                item = data["message"]
        if not item and rec["title"]:
            data = http.get_json("crossref", "seed_title", "https://api.crossref.org/works", params={"query.bibliographic": rec["title"], "rows": 3, "mailto": email})
            items = ((data or {}).get("message") or {}).get("items") or []
            if items:
                best = max(items, key=lambda x: ratio(norm_title(x.get("title", [""])[0] if x.get("title") else ""), rec["title_norm"]))
                candidate = crossref_item_to_record(best, "legacy_seed_verify")
                accepted, score = compatible_metadata(rec, candidate)
                if accepted:
                    item = best
                elif score >= 94:
                    rec = rec.copy()
                    rec["duplicate_status"] = "needs_review"
                    rec["dedup_status"] = "review_near_duplicate"
                    rec["notes"] = join_unique([rec.get("notes", ""), f"Crossref title candidate held for review (score={score:.1f})"])
        if item:
            cr = crossref_item_to_record(item, "legacy_seed_verify")
            merged = rec.copy()
            for k in ["title", "title_norm", "authors", "year", "venue", "doi", "doi_norm", "document_type", "citation_count", "citation_count_source", "retrieved_at_utc"]:
                if cr.get(k):
                    merged[k] = cr[k]
            # A seed's verification state records its provenance boundary. API
            # metadata enrichment may update only the metadata-specific state.
            merged["verification_status"] = rec.get("verification_status", "unverified_seed")
            merged["metadata_verification_status"] = cr["metadata_verification_status"]
            merged["evidence_status"] = "not_evidence"
            merged["screening_status"] = "pending"
            merged["provenance"] = join_unique([rec.get("provenance", "legacy_review"), "crossref"])
            merged["provenance_sources"] = join_unique([rec["provenance_sources"], "crossref"])
            merged["provenance_queries"] = join_unique([rec["provenance_queries"], "legacy_seed_verify"])
            merged["source_ids"] = join_unique([rec.get("source_ids", ""), cr.get("source_ids", "")])
            enriched.append(merged)
        else:
            rec = rec.copy()
            rec["metadata_verification_status"] = "unresolved"
            rec["verification_status"] = "unverified_seed"
            rec["evidence_status"] = "not_evidence"
            rec["screening_status"] = "pending"
            enriched.append(rec)
    return enriched


def discover_open(protocol: dict[str, Any], http: CachedHttp, email: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    out: list[dict[str, Any]] = []
    search_logs: list[dict[str, Any]] = []
    raw_source_counts: dict[str, int] = {"crossref": 0, "openalex": 0}
    for q in protocol.get("query_families", []):
        qid, terms = q["id"], q["terms"]
        cr_url = "https://api.crossref.org/works"
        cr_params = {"query.bibliographic": terms, "rows": 25, "mailto": email, "select": "DOI,title,author,published-print,published-online,issued,container-title,type,is-referenced-by-count,abstract"}
        cr = http.get_json("crossref", "discovery", cr_url, params=cr_params)
        cr_items = (((cr or {}).get("message") or {}).get("items") or [])
        cr_total = int((((cr or {}).get("message") or {}).get("total-results") or 0))
        cr_status = "ok" if cr is not None else "failed_or_empty"
        search_logs.append(asdict(SearchEvent(qid, "crossref", terms, utc_now(), cr_total, len(cr_items), "single_page", "rows=25", request_hash(cr_url, cr_params), cr_status)))
        raw_source_counts["crossref"] += len(cr_items)
        for item in cr_items:
            rec = crossref_item_to_record(item, qid)
            if rec["title"]:
                out.append(rec)
        oa_url = "https://api.openalex.org/works"
        oa_query = openalex_search_query(terms)
        oa_params: dict[str, Any] = {"search": oa_query, "per-page": 25}
        if http.api_keys.get("OPENALEX_API_KEY"):
            oa_params["api_key"] = http.api_keys["OPENALEX_API_KEY"]
        oa = http.get_json("openalex", "discovery", oa_url, params=oa_params)
        oa_items = ((oa or {}).get("results") or [])
        oa_meta = (oa or {}).get("meta") or {}
        oa_total = int(oa_meta.get("count") or 0)
        oa_status = "ok" if oa is not None else "failed_or_empty"
        search_logs.append(asdict(SearchEvent(qid, "openalex", terms, utc_now(), oa_total, len(oa_items), "single_page", "per-page=25;openalex_query_translation=boolean_to_full_text", request_hash(oa_url, oa_params), oa_status)))
        raw_source_counts["openalex"] += len(oa_items)
        for item in oa_items:
            rec = openalex_item_to_record(item, qid)
            if rec["title"]:
                out.append(rec)
    return out, search_logs, raw_source_counts


def read_table_guess(path: Path) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-16", "cp1252", "latin-1"]
    seps = ["\t", ",", ";"]
    last = None
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(path, dtype=str, encoding=enc, sep=sep, engine="python").fillna("")
                if df.shape[1] >= 3:
                    return df
            except Exception as e:
                last = e
    raise RuntimeError(f"Could not parse {path}: {last}")


def first_col(row: pd.Series, names: list[str]) -> str:
    cmap = {str(c).strip().lower(): c for c in row.index}
    for n in names:
        c = cmap.get(n.lower())
        if c is not None:
            v = str(row[c]).strip()
            if v and v.lower() != "nan":
                return v
    return ""


def ingest_wos() -> list[dict[str, Any]]:
    out = []
    for p in sorted((INPUT / "wos").glob("*")):
        if not p.is_file() or p.name.lower().startswith("readme"):
            continue
        if p.suffix.lower() not in {".txt", ".tsv", ".csv"}:
            continue
        df = read_table_guess(p)
        for _, row in df.iterrows():
            title = first_col(row, ["TI", "Article Title", "Title"])
            if not title:
                continue
            doi = norm_doi(first_col(row, ["DI", "DOI"] ))
            year = safe_year(first_col(row, ["PY", "Publication Year", "Year"] ))
            ut = first_col(row, ["UT", "Accession Number", "UT (Unique WOS ID)"])
            out.append({
                "candidate_id": stable_id(title, year, doi),
                "title": title,
                "title_norm": norm_title(title),
                "authors": first_col(row, ["AU", "Authors", "Author Full Names"]),
                "year": year,
                "venue": first_col(row, ["SO", "Source Title", "Publication Name"]),
                "doi": doi,
                "doi_norm": doi,
                "abstract": first_col(row, ["AB", "Abstract"]),
                "document_type": first_col(row, ["DT", "Document Type"]),
                "source_ids": f"wos:{ut}" if ut else "",
                "provenance_sources": f"wos:{p.name}",
                "provenance_queries": "wos_export",
                "verification_status": "metadata_verified",
                "legacy_seed_id": "",
                "wos_ut": ut,
                "citation_count": first_col(row, ["TC", "Times Cited, WoS Core", "Times Cited"]),
                "citation_count_source": "wos" if first_col(row, ["TC", "Times Cited, WoS Core", "Times Cited"]) else "",
                "retrieved_at_utc": utc_now(),
                "dedup_status": "unique",
                "dedup_parent_candidate_id": "",
                "notes": "",
            })
    return out


def merge_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    # Exact DOI merge first. Non-DOI matches require compatible title, year,
    # first author and venue; ambiguous pairs are retained for review.
    canon: list[dict[str, Any]] = []
    by_doi: dict[str, int] = {}
    prov_edges: list[dict[str, str]] = []

    def merge_into(dst: dict[str, Any], src: dict[str, Any]) -> None:
        for key in ["title", "title_norm", "authors", "authors_norm", "year", "venue", "doi", "doi_norm", "abstract", "document_type", "wos_ut", "source_ids"]:
            if not dst.get(key) and src.get(key):
                dst[key] = src[key]
        # Enrichment may improve metadata, but never promotes a seed to an
        # evidence or screening state.
        if src.get("verification_status") == "metadata_verified" and dst.get("verification_status") in {"unverified_seed", "metadata_partial", "unresolved"}:
            if dst.get("verification_status") != "unverified_seed":
                dst["verification_status"] = "metadata_verified"
        if src.get("metadata_verification_status") == "metadata_verified":
            dst["metadata_verification_status"] = "metadata_verified"
        dst["evidence_status"] = dst.get("evidence_status") or "not_evidence"
        dst["screening_status"] = dst.get("screening_status") or "pending"
        dst["provenance"] = join_unique([dst.get("provenance", ""), src.get("provenance", "")])
        dst["provenance_sources"] = join_unique([dst.get("provenance_sources", ""), src.get("provenance_sources", "")])
        dst["provenance_queries"] = join_unique([dst.get("provenance_queries", ""), src.get("provenance_queries", "")])
        dst["legacy_seed_id"] = join_unique([dst.get("legacy_seed_id", ""), src.get("legacy_seed_id", "")])
        dst["seed_raw"] = dst.get("seed_raw") or src.get("seed_raw", "")
        # Preserve WoS citation count if available; else retain existing.
        if src.get("citation_count_source") == "wos":
            dst["citation_count"] = src.get("citation_count", "")
            dst["citation_count_source"] = "wos"
        elif not dst.get("citation_count") and src.get("citation_count"):
            dst["citation_count"] = src.get("citation_count", "")
            dst["citation_count_source"] = src.get("citation_count_source", "")

    for rec in records:
        rec = rec.copy()
        doi = rec.get("doi_norm", "")
        if doi and doi in by_doi:
            idx = by_doi[doi]
            parent = canon[idx]["candidate_id"]
            merge_into(canon[idx], rec)
            prov_edges.append({"candidate_id": parent, "source": rec.get("provenance_sources", ""), "query": rec.get("provenance_queries", ""), "relation": "exact_doi_merge"})
            continue

        # High-confidence non-DOI merge only with compatible metadata.
        merged = False
        tn = rec.get("title_norm", "")
        if tn:
            for idx, ex in enumerate(canon):
                if not ex.get("title_norm"):
                    continue
                compatible, sim = compatible_metadata(ex, rec)
                if sim >= 94 and not compatible:
                    prov_edges.append({"candidate_id": ex["candidate_id"], "source": rec.get("provenance_sources", ""), "query": rec.get("provenance_queries", ""), "relation": f"possible_duplicate_{sim:.1f}"})
                if compatible:
                    # Refuse auto-merge when both have distinct non-empty DOIs.
                    if doi and ex.get("doi_norm") and doi != ex.get("doi_norm"):
                        continue
                    parent = ex["candidate_id"]
                    merge_into(ex, rec)
                    prov_edges.append({"candidate_id": parent, "source": rec.get("provenance_sources", ""), "query": rec.get("provenance_queries", ""), "relation": f"title_merge_{sim:.1f}"})
                    if doi and not ex.get("doi_norm"):
                        ex["doi"] = ex["doi_norm"] = doi
                        by_doi[doi] = idx
                    merged = True
                    break
        if merged:
            continue
        idx = len(canon)
        canon.append(rec)
        if doi:
            by_doi[doi] = idx
        prov_edges.append({"candidate_id": rec["candidate_id"], "source": rec.get("provenance_sources", ""), "query": rec.get("provenance_queries", ""), "relation": "discovered"})

    # Flag probable duplicates for manual QA, without merging.
    for i, a in enumerate(canon):
        if a.get("dedup_status") != "unique":
            continue
        for j in range(i + 1, len(canon)):
            b = canon[j]
            if a.get("doi_norm") and b.get("doi_norm") and a["doi_norm"] == b["doi_norm"]:
                continue
            if not a.get("title_norm") or not b.get("title_norm"):
                continue
            compatible, sim = compatible_metadata(a, b)
            if sim >= 94 and not compatible:
                a["duplicate_status"] = "needs_review"
                b["duplicate_status"] = "needs_review"
                a["dedup_status"] = "review_near_duplicate"
                b["dedup_status"] = "review_near_duplicate"
                prov_edges.append({"candidate_id": a["candidate_id"], "source": b.get("provenance_sources", ""), "query": b.get("provenance_queries", ""), "relation": f"possible_duplicate_{sim:.1f}"})
    return canon, prov_edges


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0].keys()) if rows else [])
    if not fields:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def counter_lines(counter: dict[str, int]) -> str:
    if not counter:
        return "- none"
    return "\n".join(f"- `{key}`: {value}" for key, value in sorted(counter.items()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["open", "wos", "all"], default="open")
    ap.add_argument("--resume", action="store_true", help="reuse cached responses")
    ap.add_argument("--force", action="store_true", help="refresh cached responses")
    args = ap.parse_args()

    protocol = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    env = dotenv_values(ENV)
    email = (env.get("CONTACT_EMAIL") or protocol.get("contact_email") or "").strip()
    if not email:
        raise SystemExit("CONTACT_EMAIL is required for responsible scholarly API access.")

    seed_records = load_seed()
    records = seed_records
    api_keys = {key: str(env.get(key) or os.environ.get(key) or "").strip() for key in ["OPENALEX_API_KEY", "SEMANTIC_SCHOLAR_API_KEY", "CORE_API_KEY"]}
    http = CachedHttp(email, force=args.force, api_keys=api_keys)
    search_logs: list[dict[str, Any]] = []
    raw_source_counts: dict[str, int] = {"legacy_review": len(seed_records)}
    deviations: list[str] = []
    if args.mode in {"open", "all"}:
        records = enrich_seeds(records, http, email)
        discovered, search_logs, discovery_counts = discover_open(protocol, http, email)
        records += discovered
        raw_source_counts.update(discovery_counts)
    if args.mode in {"wos", "all"}:
        wos = ingest_wos()
        if not wos:
            print("No authentic WoS exports found; continuing without WoS records.")
            deviations.append("No authentic WoS export was present; corpus coverage is open_discovery_only.")
        else:
            raw_source_counts["wos"] = len(wos)
        records += wos

    canon, edges = merge_records(records)
    canon.sort(key=lambda r: (safe_year(r.get("year", "")) or "9999", r.get("title_norm", "")))
    corpus_fields = list(seed_records[0].keys()) if seed_records else []
    for record in canon:
        for field in record:
            if field not in corpus_fields:
                corpus_fields.append(field)
    write_csv(OUTPUT / "candidate_corpus_stage1a.csv", canon, corpus_fields)
    write_jsonl(OUTPUT / "candidate_corpus_stage1a.jsonl", canon)
    write_csv(LOGS / "stage1a_api_log.csv", [asdict(e) for e in http.events], list(ApiEvent.__dataclass_fields__.keys()))
    write_csv(LOGS / "stage1a_search_log.csv", search_logs, list(SearchEvent.__dataclass_fields__.keys()))
    write_csv(LOGS / "stage1a_dedup_log.csv", edges, ["candidate_id", "source", "query", "relation"])

    wos_files = [p for p in (INPUT / "wos").glob("*") if p.is_file() and not p.name.lower().startswith("readme")]
    legacy = sum(1 for r in canon if r.get("legacy_seed_id"))
    verified = sum(1 for r in canon if r.get("metadata_verification_status") == "metadata_verified")
    unresolved = sum(1 for r in canon if r.get("metadata_verification_status") in {"unresolved", "not_checked", "metadata_partial"})
    near = sum(1 for r in canon if r.get("duplicate_status") == "needs_review")
    doi_present = sum(1 for r in canon if r.get("doi_norm"))
    exact_duplicates = sum(1 for e in edges if e.get("relation") == "exact_doi_merge" or e.get("relation", "").startswith("title_merge_"))
    api_failures = sum(1 for e in http.events if e.status in {"failed", "forbidden", "auth_required", "parse_error"})
    years = [int(r["year"]) for r in canon if safe_year(r.get("year", ""))]
    year_counts: dict[str, int] = {}
    venue_counts: dict[str, int] = {}
    provenance_counts: dict[str, int] = {}
    for record in canon:
        year_value = safe_year(record.get("year", "")) or "(missing)"
        year_counts[year_value] = year_counts.get(year_value, 0) + 1
        venue = record.get("venue") or "(missing)"
        venue_counts[venue] = venue_counts.get(venue, 0) + 1
        for source in (record.get("provenance_sources") or "").split(";"):
            if source:
                provenance_counts[source] = provenance_counts.get(source, 0) + 1
    if not wos_files:
        deviations.append("wos_status=pending_external_export.")
    if args.force:
        deviations.append("--force bypassed successful HTTP cache entries for this run.")
    qa = f"""# Stage 1A candidate-corpus QA

Run UTC: {utc_now()}

- Mode: `{args.mode}`
- Legacy seeds imported: **{len(seed_records)}**
- Canonical candidates carrying legacy seed provenance: **{legacy}**
- Raw records entering reconciliation: **{len(records)}**
- Records after normalization/reconciliation: **{len(canon)}**
- DOI present/missing: **{doi_present}/{len(canon) - doi_present}**
- Exact duplicates merged: **{exact_duplicates}**
- Probable duplicates held for review: **{near}**
- Unique final candidates: **{len(canon)}**
- Metadata-verified candidates: **{verified}**
- Unresolved or insufficiently verified records: **{unresolved}**
- API failures: **{api_failures}**
- Year coverage: **{min(years) if years else 'n/a'}–{max(years) if years else 'n/a'}**
- Authentic WoS raw files present: **{len(wos_files)}**
- API events logged: **{len(http.events)}**
- Resume requested: **{args.resume}**

## Coverage label

`corpus_coverage={'wos_reconciled_or_present' if wos_files else 'open_discovery_only'}`  
`wos_status={'present' if wos_files else 'pending_external_export'}`

## Raw records retrieved by source

{counter_lines(raw_source_counts)}

## Publication years

{counter_lines(year_counts)}

## Main venues

{counter_lines(dict(sorted(venue_counts.items(), key=lambda item: (-item[1], item[0]))[:20]))}

## Provenance-bearing final candidates

{counter_lines(provenance_counts)}

## Queries executed

{chr(10).join(f"- `{entry['query_id']}` / `{entry['source']}`: returned {entry['returned_count']} of reported {entry['result_count']}; status `{entry['status']}`" for entry in search_logs) or '- none'}

## Deviations

{chr(10).join(f"- {item}" for item in sorted(set(deviations))) or '- none'}

## Stop rule

This is a candidate bibliographic corpus only. It is not screened/full-text
evidence and must not be used to finalize novelty or gap claims.
"""
    (REPORTS / "stage1a_qa.md").write_text(qa, encoding="utf-8")
    if not wos_files:
        tmpl = BASE / "templates" / "WOS_PENDING_TEMPLATE.md"
        if tmpl.exists():
            (REPORTS / "WOS_PENDING.md").write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
    provenance = f"""# Stage 1A provenance summary

Coverage: `{'open_discovery_only' if not wos_files else 'wos_reconciled_or_present'}`  
WoS status: `{'pending_external_export' if not wos_files else 'present'}`

## Source provenance counts

{counter_lines(provenance_counts)}

## API events

- Total events: {len(http.events)}
- Failures (`failed`, `forbidden`, `auth_required`, `parse_error`): {api_failures}
- Cache hits: {sum(1 for e in http.events if e.status == 'cache_hit')}

## Search protocol

- Query families executed: {len(search_logs)} source-query executions.
- Queries are preserved in `logs/stage1a_search_log.csv` with exact text,
  request hash, result count and returned count.

## Interpretation boundary

The 32 legacy rows remain seeds with `verification_status=unverified_seed`,
`evidence_status=not_evidence` and `screening_status=pending`. Metadata
enrichment does not promote them to evidence. No screening, full-text review,
deep reading, snowballing or novelty analysis was performed.
"""
    (REPORTS / "stage1a_provenance_summary.md").write_text(provenance, encoding="utf-8")
    print(qa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
