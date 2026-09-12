"""Stage 2: acquire and validate legal/open full text for the Stage 1C queue.

This stage is deliberately conservative. It uses only public metadata/API
routes and public URLs exposed by OpenAlex, Crossref, or a DOI landing page.
No credentials, institutional proxy, paywall bypass, or robots restriction
override is used. A downloaded object is kept only after a title/DOI identity
check; a mismatched object is never promoted to evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.util
import json
import re
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, urlparse

import requests
import yaml


BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
PROCESSED = DATA / "processed"
QUEUE = PROCESSED / "fulltext_queue_stage1c.csv"
CORPUS = PROCESSED / "candidate_corpus_stage1c.csv"
FULLTEXT = DATA / "fulltext"
CACHE = BASE / "cache" / "fulltext"
LOGS = BASE / "logs"
REPORTS = BASE / "reports"
MANIFESTS = BASE / "manifests"
CONFIG = BASE / "config" / "stage2_acquisition.yaml"
ENV = BASE / ".env.literature"
for directory in [FULLTEXT, CACHE, LOGS, REPORTS, MANIFESTS]:
    directory.mkdir(parents=True, exist_ok=True)

ALLOWED_STATUSES = {
    "acquired_pdf",
    "acquired_html",
    "acquired_xml",
    "abstract_only",
    "unavailable_legally",
    "retrieval_error",
}
OPEN_HOSTS = {
    "arxiv.org",
    "export.arxiv.org",
    "pmc.ncbi.nlm.nih.gov",
    "europepmc.org",
    "europepmc.org",
    "doaj.org",
    "journals.plos.org",
    "mdpi.com",
    "frontiersin.org",
    "biomedcentral.com",
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "of", "on", "or",
    "the", "to", "using", "with", "via", "based", "approach", "method", "system", "systems",
}


def load_bootstrap():
    path = BASE / "scripts" / "bootstrap_literature.py"
    spec = importlib.util.spec_from_file_location("bootstrap_for_stage2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load shared literature helpers from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BOOT = load_bootstrap()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_file(path)


def norm_doi(value: Any) -> str:
    value = clean(value).lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.strip(" .;,)\"'")


def norm_text(value: Any) -> str:
    value = html.unescape(clean(value)).lower()
    value = re.sub(r"https?://doi\.org/", "doi:", value)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def title_tokens(value: Any) -> set[str]:
    return {token for token in norm_text(value).split() if len(token) > 2 and token not in STOPWORDS}


def title_overlap(expected: str, observed: str) -> float:
    left, right = title_tokens(expected), title_tokens(observed)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left)


def openalex_id(row: dict[str, Any]) -> str:
    for item in clean(row.get("source_ids")).split(";"):
        if item.startswith("openalex:"):
            value = item.split(":", 1)[1].strip()
            return value.rsplit("/", 1)[-1]
    return ""


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    rows = list(rows)
    if fields is None:
        ordered: list[str] = []
        for row in rows:
            for key in row:
                if key not in ordered:
                    ordered.append(key)
        fields = ordered
    fields = list(fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def ensure_stage1c_frozen() -> dict[str, Any]:
    manifest_path = MANIFESTS / "stage1c_freeze_manifest.json"
    if not QUEUE.exists() or not CORPUS.exists():
        raise FileNotFoundError("Stage 1C candidate corpus and queue are required inputs")
    observed = {
        str(QUEUE.relative_to(BASE)): {"bytes": QUEUE.stat().st_size, "sha256": sha256_path(QUEUE)},
        str(CORPUS.relative_to(BASE)): {"bytes": CORPUS.stat().st_size, "sha256": sha256_path(CORPUS)},
    }
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("files") != observed:
            raise RuntimeError(f"Stage 1C input changed after freeze: expected {manifest.get('files')}, observed {observed}")
        return manifest
    manifest = {
        "created_at_utc": utc_now(),
        "status": "immutable_input",
        "files": observed,
        "note": "Stage 2 must never overwrite Stage 1C corpus or queue.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_openalex_locations(work: dict[str, Any]) -> list[dict[str, Any]]:
    locations: list[dict[str, Any]] = []
    work_oa = work.get("open_access") or {}
    work_is_oa = bool(work_oa.get("is_oa"))
    for location in work.get("locations") or []:
        if not isinstance(location, dict):
            continue
        landing = clean(location.get("landing_page_url"))
        pdf = clean(location.get("pdf_url"))
        license_name = clean(location.get("license"))
        is_oa = bool(location.get("is_oa")) or work_is_oa or bool(license_name)
        source = location.get("source") or {}
        source_name = clean(source.get("display_name") or source.get("host_organization_name")) if isinstance(source, dict) else ""
        for url, hint in [(pdf, "pdf"), (landing, "landing")]:
            if not url:
                continue
            # OpenAlex returns non-OA locations alongside OA locations.  They
            # are not legal acquisition routes for this stage and must not
            # enter the downloader merely because they are discoverable.
            if not is_oa and not host_is_open(urlparse(url).netloc):
                continue
            locations.append({
                "url": url,
                "source": "openalex_oa_location",
                "is_oa": is_oa,
                "content_type_hint": hint,
                "license": license_name,
                "version": clean(location.get("version")),
                "source_name": source_name,
            })
    best = work.get("best_oa_location") or {}
    if isinstance(best, dict):
        for url, hint in [(clean(best.get("pdf_url")), "pdf"), (clean(best.get("landing_page_url")), "landing")]:
            if url:
                locations.append({
                    "url": url,
                    "source": "openalex_best_oa_location",
                    "is_oa": True,
                    "content_type_hint": hint,
                    "license": clean(best.get("license")),
                    "version": clean(best.get("version")),
                    "source_name": clean((best.get("source") or {}).get("display_name")) if isinstance(best.get("source"), dict) else "",
                })
    return locations


def parse_crossref_links(payload: dict[str, Any] | None, doi: str) -> list[dict[str, Any]]:
    message = (payload or {}).get("message") or {}
    links = message.get("link") or []
    out: list[dict[str, Any]] = []
    for link in links:
        if not isinstance(link, dict):
            continue
        url = clean(link.get("URL"))
        if not url:
            continue
        out.append({
            "url": url,
            "source": "crossref_public_link",
            "is_oa": bool(link.get("content-version") == "vor" or link.get("intended-application")),
            "content_type_hint": clean(link.get("content-type")),
            "license": "",
            "version": clean(link.get("content-version")),
            "source_name": "Crossref public link",
        })
    # A DOI landing page is discoverable without authentication, but that fact
    # does not establish open access. It is therefore not a Stage 2 download
    # route; only explicit public links are retained below.
    return out


def host_is_open(host: str) -> bool:
    host = host.lower().split(":", 1)[0].removeprefix("www.")
    return host in OPEN_HOSTS or any(host.endswith("." + domain) for domain in OPEN_HOSTS)


def rank_url(item: dict[str, Any]) -> tuple[int, str]:
    url = clean(item.get("url"))
    parsed = urlparse(url)
    path = parsed.path.lower()
    if path.endswith(".pdf") or item.get("content_type_hint") == "pdf":
        return (0, url)
    if host_is_open(parsed.netloc):
        return (1, url)
    if item.get("source") == "crossref_public_link":
        return (2, url)
    return (3, url)


def unique_urls(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out = []
    for item in sorted(locations, key=rank_url):
        url = clean(item.get("url"))
        if not url or url in seen or url.startswith("javascript:"):
            continue
        if urlparse(url).scheme not in {"http", "https"}:
            continue
        seen.add(url)
        out.append(item)
    return out


def strip_markup(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def pdf_text(path: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages[:8]:
            pages.append(page.extract_text() or "")
        metadata = reader.metadata or {}
        metadata_title = clean(metadata.get("/Title") if hasattr(metadata, "get") else "")
        return "\n".join(pages), metadata_title
    except Exception as exc:
        return "", f"pdf_extract_error:{type(exc).__name__}"


def identity_check(row: dict[str, Any], payload: bytes, kind: str, temp_path: Path | None = None) -> tuple[str, str, float]:
    expected_title = clean(row.get("title"))
    expected_doi = norm_doi(row.get("doi_norm") or row.get("doi"))
    if kind == "pdf" and temp_path is not None:
        text, metadata_title = pdf_text(temp_path)
        observed_text = f"{metadata_title} {text}"
    else:
        observed_text = strip_markup(payload)
    if not observed_text.strip():
        return "identity_unverified_no_text", "No extractable title, DOI, or body text", 0.0
    observed_dois = {norm_doi(value) for value in re.findall(r"(?:https?://doi\.org/|doi\s*:\s*)?10\.\d{4,9}/[-._;()/:a-z0-9]+", observed_text, flags=re.I)}
    observed_dois.discard("")
    if expected_doi and observed_dois and expected_doi not in observed_dois:
        return "identity_mismatch_doi", f"Observed DOI(s): {';'.join(sorted(observed_dois))}", 0.0
    overlap = title_overlap(expected_title, observed_text[:12000])
    expected_norm = norm_text(expected_title)
    title_in_text = bool(expected_norm and expected_norm in norm_text(observed_text[:30000]))
    if expected_doi and expected_doi in observed_dois:
        return "identity_verified_doi", "Candidate DOI observed in extracted text", max(overlap, 1.0)
    if title_in_text or overlap >= 0.55:
        return "identity_verified_title", f"Title token overlap={overlap:.3f}", overlap
    return "identity_mismatch_title", f"Title token overlap={overlap:.3f}", overlap


def classify_body(content: bytes, content_type: str, hint: str) -> str:
    head = content[:16].lstrip()
    ctype = content_type.lower()
    if head.startswith(b"%PDF") or "application/pdf" in ctype or hint == "pdf":
        return "pdf"
    if "xml" in ctype or head.startswith(b"<?xml"):
        return "xml"
    if "html" in ctype or b"<html" in content[:5000].lower() or b"<article" in content[:5000].lower():
        return "html"
    return "unknown"


def looks_like_fulltext(content: bytes, kind: str) -> bool:
    text = strip_markup(content)
    if kind == "pdf":
        return len(text) >= 500 or bool(re.search(r"\b(introduction|methods?|methodology|results|discussion|conclusion)\b", text, flags=re.I))
    if kind == "xml":
        return len(text) >= 1000 and bool(re.search(r"\b(introduction|methods?|results|discussion|conclusion)\b", text, flags=re.I))
    if kind == "html":
        lower = content.decode("utf-8", errors="ignore").lower()
        sections = sum(bool(re.search(rf"\b{term}\b", text, flags=re.I)) for term in ["introduction", "methods", "results", "discussion", "conclusion"])
        article_structure = any(marker in lower for marker in ["<article", "citation_title", "fulltext", "full-text", "article-body", "articlebody"])
        blocked = any(marker in text.lower() for marker in ["purchase access", "institutional access", "subscribe to read", "sign in to access"])
        return not blocked and article_structure and len(text) >= 1800 and sections >= 2
    return False


def cache_paths(url: str) -> tuple[Path, Path]:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE / f"{key}.bin", CACHE / f"{key}.json"


class FullTextClient:
    def __init__(self, email: str, max_attempts: int, timeout: int, max_bytes: int, force: bool = False):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"MROB-Academic-Review/1.0 (mailto:{email})",
            "Accept": "application/pdf, application/xml, text/xml, text/html;q=0.9, */*;q=0.1",
        })
        self.max_attempts = max_attempts
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.force = force
        self.last_request = 0.0
        self.delay = 0.55
        self.attempts: list[dict[str, Any]] = []

    def fetch(self, row: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
        url = clean(item.get("url"))
        cache_bin, cache_meta = cache_paths(url)
        if cache_bin.exists() and cache_meta.exists() and not self.force:
            try:
                metadata = json.loads(cache_meta.read_text(encoding="utf-8"))
                payload = cache_bin.read_bytes()
                self.attempts.append({
                    "candidate_id": row.get("candidate_id", ""), "attempt": 0, "url": url,
                    "source": item.get("source", ""), "access_route": "cache", "http_status": metadata.get("http_status", ""),
                    "outcome": "cache_hit", "bytes": len(payload), "mime_type": metadata.get("mime_type", ""),
                    "message": "Persistent full-text cache reused", "timestamp_utc": utc_now(),
                })
                return {"ok": True, "payload": payload, "mime_type": metadata.get("mime_type", ""), "final_url": metadata.get("final_url", url), "http_status": metadata.get("http_status", 200), "from_cache": True}
            except Exception:
                pass
        for attempt in range(1, self.max_attempts + 1):
            since = time.monotonic() - self.last_request
            if since < self.delay:
                time.sleep(self.delay - since)
            started = time.monotonic()
            try:
                response = self.session.get(url, timeout=(30, self.timeout), allow_redirects=True, stream=True)
                self.last_request = time.monotonic()
                status = response.status_code
                if status in {401, 402, 403}:
                    self.attempts.append(self._attempt(row, item, attempt, status, "blocked_access", "No public access without authentication", 0, ""))
                    return {"ok": False, "terminal": "blocked_access", "message": "Public route blocked or requires authentication"}
                if status == 404:
                    self.attempts.append(self._attempt(row, item, attempt, status, "not_found", "Public route returned 404", 0, ""))
                    return {"ok": False, "terminal": "not_found", "message": "Public route not found"}
                if status == 429 or 500 <= status < 600:
                    self.attempts.append(self._attempt(row, item, attempt, status, "retryable_http", f"Retryable HTTP {status}", 0, ""))
                    if attempt < self.max_attempts:
                        time.sleep(min(20.0, 2 ** attempt))
                        continue
                    return {"ok": False, "terminal": "retryable_http", "message": f"HTTP {status} after {attempt} attempts"}
                if status >= 400:
                    self.attempts.append(self._attempt(row, item, attempt, status, "http_error", f"HTTP {status}", 0, ""))
                    return {"ok": False, "terminal": "http_error", "message": f"HTTP {status}"}
                chunks: list[bytes] = []
                total = 0
                oversized = False
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > self.max_bytes:
                        oversized = True
                        break
                    chunks.append(chunk)
                payload = b"".join(chunks)
                if oversized:
                    self.attempts.append(self._attempt(row, item, attempt, status, "too_large", f"Response exceeds {self.max_bytes} bytes", total, response.headers.get("Content-Type", "")))
                    return {"ok": False, "terminal": "too_large", "message": "Response exceeded configured limit"}
                mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                self.attempts.append(self._attempt(row, item, attempt, status, "downloaded", "Public response downloaded", len(payload), mime))
                cache_bin.write_bytes(payload)
                cache_meta.write_text(json.dumps({"url": url, "final_url": response.url, "http_status": status, "mime_type": mime, "bytes": len(payload), "sha256": sha256_bytes(payload), "retrieved_at_utc": utc_now()}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                return {"ok": True, "payload": payload, "mime_type": mime, "final_url": response.url, "http_status": status, "from_cache": False}
            except (requests.RequestException, OSError) as exc:
                elapsed = int((time.monotonic() - started) * 1000)
                self.attempts.append(self._attempt(row, item, attempt, "", "request_error", f"{type(exc).__name__}: {exc}", 0, "", elapsed))
                if attempt < self.max_attempts:
                    time.sleep(min(20.0, 2 ** attempt))
                    continue
                return {"ok": False, "terminal": "request_error", "message": f"{type(exc).__name__}: {exc}"}
        return {"ok": False, "terminal": "request_error", "message": "No response"}

    @staticmethod
    def _attempt(row: dict[str, Any], item: dict[str, Any], attempt: int, status: Any, outcome: str, message: str, size: int, mime: str, elapsed: int = 0) -> dict[str, Any]:
        return {
            "candidate_id": row.get("candidate_id", ""), "attempt": attempt, "url": item.get("url", ""),
            "source": item.get("source", ""), "access_route": "public_unauthenticated", "http_status": status,
            "outcome": outcome, "bytes": size, "mime_type": mime, "message": message,
            "elapsed_ms": elapsed, "timestamp_utc": utc_now(),
        }


def detail_map(rows: list[dict[str, Any]], http: Any, email: str) -> dict[str, dict[str, Any]]:
    ids = sorted({openalex_id(row) for row in rows if openalex_id(row)})
    details: dict[str, dict[str, Any]] = {}
    for start in range(0, len(ids), 100):
        batch = ids[start:start + 100]
        payload = http.get_json("openalex", "stage2_work_details", "https://api.openalex.org/works", params={"filter": f"openalex:{'|'.join(batch)}", "per-page": 100})
        for work in (payload or {}).get("results", []):
            value = clean(work.get("id")).rsplit("/", 1)[-1]
            if value:
                details[value] = work
    return details


def acquire_row(row: dict[str, Any], details: dict[str, dict[str, Any]], crossref_cache: dict[str, dict[str, Any] | None], api_http: Any, client: FullTextClient, force: bool) -> dict[str, Any]:
    candidate_id = clean(row.get("candidate_id"))
    candidate_dir = FULLTEXT / candidate_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = candidate_dir / "acquisition.json"
    if manifest_path.exists() and not force:
        try:
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            if saved.get("status") in ALLOWED_STATUSES:
                result = dict(row)
                result.update(saved)
                return result
        except Exception:
            pass
    locations: list[dict[str, Any]] = []
    aid = openalex_id(row)
    if aid and aid in details:
        locations.extend(parse_openalex_locations(details[aid]))
    doi = norm_doi(row.get("doi_norm") or row.get("doi"))
    if doi and doi not in crossref_cache and (not locations or not any(item.get("is_oa") for item in locations)):
        crossref_cache[doi] = api_http.get_json("crossref", "stage2_work_links", f"https://api.crossref.org/works/{quote(doi, safe='()/._;-')}", params={})
    if doi:
        locations.extend(parse_crossref_links(crossref_cache.get(doi), doi))
    locations = unique_urls(locations)
    attempted_urls: list[str] = []
    rejections: list[str] = []
    successful = None
    for item in locations:
        attempted_urls.append(item["url"])
        response = client.fetch(row, item)
        if not response.get("ok"):
            rejections.append(f"{item['url']}:{response.get('terminal', 'error')}")
            continue
        payload = response["payload"]
        kind = classify_body(payload, response.get("mime_type", ""), clean(item.get("content_type_hint")))
        if kind not in {"pdf", "html", "xml"}:
            rejections.append(f"{item['url']}:unsupported_content")
            continue
        temp_path = candidate_dir / ".identity-check.pdf" if kind == "pdf" else None
        if temp_path is not None:
            temp_path.write_bytes(payload)
        identity, identity_note, overlap = identity_check(row, payload, kind, temp_path)
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
        if identity.startswith("identity_mismatch") or identity == "identity_unverified_no_text":
            rejections.append(f"{item['url']}:{identity}")
            continue
        if not looks_like_fulltext(payload, kind):
            rejections.append(f"{item['url']}:abstract_or_landing_only")
            continue
        extension = {"pdf": ".pdf", "html": ".html", "xml": ".xml"}[kind]
        output_path = candidate_dir / f"fulltext{extension}"
        output_path.write_bytes(payload)
        successful = {
            "status": f"acquired_{kind}",
            "fulltext_status": f"acquired_{kind}",
            "fulltext_source_url": response.get("final_url") or item["url"],
            "fulltext_retrieved_at_utc": utc_now(),
            "fulltext_sha256": sha256_file(output_path),
            "fulltext_mime_type": response.get("mime_type", ""),
            "fulltext_file_size": output_path.stat().st_size,
            "fulltext_access_note": "; ".join(filter(None, [item.get("source", ""), "public unauthenticated route", item.get("license", "")])) ,
            "fulltext_local_path": str(output_path.relative_to(BASE)),
            "fulltext_identity_status": identity,
            "fulltext_identity_note": f"{identity_note}; overlap={overlap:.3f}",
            "fulltext_attempted_urls": ";".join(attempted_urls),
            "fulltext_error": ";".join(rejections),
            "fulltext_attempt_count": sum(1 for attempt in client.attempts if attempt.get("candidate_id") == candidate_id),
        }
        break
    if successful is None:
        all_error = any(":request_error" in item or ":retryable_http" in item for item in rejections)
        status = "retrieval_error" if all_error and rejections and not any("blocked_access" in item or "not_found" in item for item in rejections) else ("abstract_only" if clean(row.get("abstract")) else "unavailable_legally")
        successful = {
            "status": status,
            "fulltext_status": status,
            "fulltext_source_url": "",
            "fulltext_retrieved_at_utc": utc_now(),
            "fulltext_sha256": "",
            "fulltext_mime_type": "",
            "fulltext_file_size": 0,
            "fulltext_access_note": "No legal/open full-text object verified without authentication",
            "fulltext_local_path": "",
            "fulltext_identity_status": "not_applicable",
            "fulltext_identity_note": "No object promoted",
            "fulltext_attempted_urls": ";".join(attempted_urls),
            "fulltext_error": ";".join(rejections) or "No public OA route observed",
            "fulltext_attempt_count": sum(1 for attempt in client.attempts if attempt.get("candidate_id") == candidate_id),
        }
    result = dict(row)
    result.update(successful)
    manifest_path.write_text(json.dumps(successful, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="reuse API and full-text caches and candidate manifests")
    parser.add_argument("--force", action="store_true", help="refresh API/download caches and reacquire candidates")
    args = parser.parse_args()
    freeze = ensure_stage1c_frozen()
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    config_hash = sha256_path(CONFIG)
    env = BOOT.dotenv_values(ENV)
    email = clean(env.get("CONTACT_EMAIL"))
    if not email:
        raise SystemExit("CONTACT_EMAIL is required for responsible scholarly API access.")
    queue = read_rows(QUEUE)
    corpus = read_rows(CORPUS)
    api_http = BOOT.CachedHttp(email, force=args.force, api_keys={})
    details = detail_map(queue, api_http, email)
    crossref_cache: dict[str, dict[str, Any] | None] = {}
    client = FullTextClient(email, int(config.get("max_attempts_per_url", 3)), int(config.get("request_timeout_seconds", 60)), int(config.get("max_download_bytes", 52428800)), force=args.force)
    enriched_queue: list[dict[str, Any]] = []
    for index, row in enumerate(queue, start=1):
        enriched_queue.append(acquire_row(row, details, crossref_cache, api_http, client, args.force))
        if index % 25 == 0:
            print(f"Stage 2 acquisition progress: {index}/{len(queue)}", flush=True)
    fields = list(corpus[0].keys()) if corpus else []
    extra_fields = [
        "fulltext_status", "fulltext_source_url", "fulltext_retrieved_at_utc", "fulltext_sha256",
        "fulltext_mime_type", "fulltext_file_size", "fulltext_access_note", "fulltext_local_path",
        "fulltext_identity_status", "fulltext_identity_note", "fulltext_attempted_urls", "fulltext_error",
        "fulltext_attempt_count",
    ]
    for field in extra_fields:
        if field not in fields:
            fields.append(field)
    by_id = {row["candidate_id"]: row for row in enriched_queue}
    enriched_corpus = []
    for row in corpus:
        updated = dict(row)
        if row.get("candidate_id") in by_id:
            updated.update({key: by_id[row["candidate_id"]].get(key, "") for key in extra_fields})
        else:
            updated.update({key: "" for key in extra_fields})
        enriched_corpus.append(updated)
    write_csv(PROCESSED / "candidate_corpus_stage2.csv", enriched_corpus, fields)
    write_csv(PROCESSED / "fulltext_queue_stage2.csv", enriched_queue, fields)
    log_fields = [
        "candidate_id", "title", "doi", "screening_decision", "fulltext_status", "source_url", "retrieval_timestamp",
        "sha256", "mime_type", "file_size", "license_access_note", "local_path", "identity_status", "identity_note",
        "attempt_count", "attempted_urls", "error",
    ]
    acquisition_log = []
    for row in enriched_queue:
        acquisition_log.append({
            "candidate_id": row.get("candidate_id", ""), "title": row.get("title", ""), "doi": row.get("doi_norm", ""),
            "screening_decision": row.get("screening_decision", ""), "fulltext_status": row.get("fulltext_status", ""),
            "source_url": row.get("fulltext_source_url", ""), "retrieval_timestamp": row.get("fulltext_retrieved_at_utc", ""),
            "sha256": row.get("fulltext_sha256", ""), "mime_type": row.get("fulltext_mime_type", ""),
            "file_size": row.get("fulltext_file_size", ""), "license_access_note": row.get("fulltext_access_note", ""),
            "local_path": row.get("fulltext_local_path", ""), "identity_status": row.get("fulltext_identity_status", ""),
            "identity_note": row.get("fulltext_identity_note", ""), "attempt_count": row.get("fulltext_attempt_count", ""),
            "attempted_urls": row.get("fulltext_attempted_urls", ""), "error": row.get("fulltext_error", ""),
        })
    write_csv(LOGS / "stage2_fulltext_acquisition.csv", acquisition_log, log_fields)
    attempt_fields = ["candidate_id", "attempt", "url", "source", "access_route", "http_status", "outcome", "bytes", "mime_type", "message", "elapsed_ms", "timestamp_utc"]
    attempt_rows = list(client.attempts)
    # A resume run legitimately has no in-memory HTTP attempts for candidates
    # whose manifests were already closed.  Emit a replay-safe summary instead
    # of an empty log, while keeping the exact prior URL/status/hash in each
    # candidate manifest and in the required acquisition log.
    seen_attempt_candidates = {clean(item.get("candidate_id")) for item in attempt_rows}
    for row in enriched_queue:
        candidate_id = clean(row.get("candidate_id"))
        if candidate_id in seen_attempt_candidates:
            continue
        for url in [item for item in clean(row.get("fulltext_attempted_urls")).split(";") if item]:
            attempt_rows.append({
                "candidate_id": candidate_id, "attempt": 0, "url": url,
                "source": "manifest_replay", "access_route": "manifest",
                "http_status": "", "outcome": "manifest_reused", "bytes": 0,
                "mime_type": "", "message": "Candidate acquisition manifest reused; see stage2_fulltext_acquisition.csv",
                "elapsed_ms": 0, "timestamp_utc": row.get("fulltext_retrieved_at_utc", utc_now()),
            })
    write_csv(LOGS / "stage2_fulltext_attempts.csv", attempt_rows, attempt_fields)
    write_csv(LOGS / "stage2_api_log.csv", [BOOT.asdict(event) for event in api_http.events], list(BOOT.ApiEvent.__dataclass_fields__.keys()))

    status_counts = Counter(row.get("fulltext_status", "") for row in enriched_queue)
    identity_counts = Counter(row.get("fulltext_identity_status", "") for row in enriched_queue)
    source_counts = Counter()
    for row in enriched_queue:
        if row.get("fulltext_source_url"):
            source_counts[urlparse(row["fulltext_source_url"]).netloc.lower()] += 1
    promoted = [row for row in enriched_queue if row.get("fulltext_status", "").startswith("acquired_")]
    verified_files = [row for row in promoted if row.get("fulltext_identity_status", "").startswith("identity_verified")]
    if len(promoted) != len(verified_files):
        raise RuntimeError("Stage 2 invariant failure: an acquired object lacks verified identity")
    if any(row.get("fulltext_status") not in ALLOWED_STATUSES for row in enriched_queue):
        raise RuntimeError("Stage 2 invariant failure: unsupported full-text status")
    qa = f"""# Stage 2 full-text acquisition QA

Run UTC: {utc_now()}

## Frozen inputs and access policy

- Stage 1C queue SHA-256: `{freeze['files'][str(QUEUE.relative_to(BASE))]['sha256']}`
- Stage 1C corpus SHA-256: `{freeze['files'][str(CORPUS.relative_to(BASE))]['sha256']}`
- Stage 2 configuration SHA-256: `{config_hash}`
- Queue records processed: **{len(enriched_queue)}**
- Access policy: **legal/open public routes only**; no credentials, proxy, paywall bypass, or robots restriction override.
- Metadata routes: OpenAlex OA locations and Crossref public links; DOI landing pages are not treated as OA routes.

## Acquisition statuses

{chr(10).join(f"- `{key}`: **{status_counts[key]}**" for key in sorted(ALLOWED_STATUSES))}

Acquired objects are retained only when the candidate DOI or title is observed
in the extracted PDF/HTML/XML. Mismatched objects and objects without
extractable identity are not promoted to the local corpus.

## Identity and sources

- Identity statuses: {', '.join(f'`{key}`={value}' for key, value in sorted(identity_counts.items())) or 'none'}
- Verified acquired objects: **{len(verified_files)}**
- Acquired file bytes: **{sum(int(row.get('fulltext_file_size') or 0) for row in promoted):,}**
- Top final source hosts: {', '.join(f'`{host}`={count}' for host, count in source_counts.most_common(12)) or 'none'}
- API events: **{len(api_http.events)}**; terminal API failures: **{sum(event.status in {'failed', 'forbidden', 'auth_required', 'parse_error'} for event in api_http.events)}**

## Validation

- Every queue record has exactly one status from the configured six-status vocabulary.
- Every promoted file has a SHA-256, byte size, local path and verified identity status.
- Candidate-level acquisition log and a replay-safe attempt-level log are generated; resumed candidates retain their prior details in manifests.
- Stage 1C inputs are frozen and were not overwritten.

## Limitations

Open-access discovery depends on the locations exposed by public metadata
services and on the availability of those public URLs at run time. A status of
`abstract_only` or `unavailable_legally` is not evidence that a paper has no
full text anywhere; it records only that this run did not verify a legal public
route. Retrieval errors remain operational failures and are not silently
converted into scientific evidence.
"""
    (REPORTS / "stage2_acquisition_qa.md").write_text(qa, encoding="utf-8")
    print(qa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
