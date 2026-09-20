"""Audit BibLaTeX references against external primary metadata.

The command is intentionally read-only with respect to the manuscript.  It writes
an audit trail that records the exact endpoint queried for every entry, performs
a Semantic Scholar batch pre-check when the public API is available, verifies
DOI metadata with Crossref, checks URL-only records at their declared source,
and reports orphan or dangling citation keys.

URL-only records cannot be promoted merely because a server answered.  Their
metadata verdict remains ``NOT_VERIFIED`` unless the page title is sufficiently
close to the bibliography title or an explicit, reviewed override is supplied.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


USER_AGENT = (
    "VIU-MROB-TFM-reference-audit/1.0 "
    "(academic integrity check; https://github.com/jlmayorgaco/VIU-MRBO-TFM-2026)"
)
DOI_API = "https://api.crossref.org/works/{}"
S2_BATCH_API = "https://api.semanticscholar.org/graph/v1/paper/batch"
CITE_RE = re.compile(
    r"\\(?:auto|paren|text|foot|smart|super|no)?cite\w*\s*"
    r"(?:\[[^\]]*\]\s*){0,2}\{([^}]*)\}",
    re.IGNORECASE,
)
INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")


@dataclass(frozen=True)
class BibEntry:
    entry_type: str
    key: str
    fields: dict[str, str]


def _consume_value(text: str, start: int) -> tuple[str, int]:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text):
        return "", start
    opening = text[start]
    if opening in "{\"":
        closing = "}" if opening == "{" else "\""
        depth = 0
        escaped = False
        pos = start + 1
        value_start = pos
        while pos < len(text):
            char = text[pos]
            if opening == "\"":
                if char == closing and not escaped:
                    return text[value_start:pos], pos + 1
                escaped = char == "\\" and not escaped
                if char != "\\":
                    escaped = False
            else:
                if char == "{":
                    depth += 1
                elif char == "}":
                    if depth == 0:
                        return text[value_start:pos], pos + 1
                    depth -= 1
            pos += 1
        raise ValueError("Unterminated BibTeX field value")
    pos = start
    while pos < len(text) and text[pos] not in ",\r\n":
        pos += 1
    return text[start:pos].strip(), pos


def _parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    pos = 0
    field_re = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)\s*=", re.MULTILINE)
    while match := field_re.search(body, pos):
        value, end = _consume_value(body, match.end())
        fields[match.group(1).lower()] = value.strip()
        pos = end
    return fields


def parse_bibtex(path: Path) -> list[BibEntry]:
    text = path.read_text(encoding="utf-8")
    entries: list[BibEntry] = []
    header_re = re.compile(r"@([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
    for header in header_re.finditer(text):
        depth = 1
        pos = header.end()
        escaped = False
        while pos < len(text) and depth:
            char = text[pos]
            if char == "{" and not escaped:
                depth += 1
            elif char == "}" and not escaped:
                depth -= 1
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            pos += 1
        if depth:
            raise ValueError(f"Unterminated BibTeX entry: {header.group(2)}")
        entries.append(
            BibEntry(
                entry_type=header.group(1).lower(),
                key=header.group(2),
                fields=_parse_fields(text[header.end() : pos - 1]),
            )
        )
    if not entries:
        raise ValueError(f"No BibTeX entries found in {path}")
    keys = [entry.key for entry in entries]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"Duplicate bibliography keys: {duplicates}")
    return entries


def normalize_text(value: str) -> str:
    # Decode the accent macros that commonly occur inside BibTeX family names
    # before removing generic LaTeX commands.  Treating ``Cort{\'e}s`` as
    # ``cort e s`` creates false author mismatches against Crossref's
    # normalized ``cortes``.
    value = re.sub(
        r"\{?\\(?:['\"`^~=.uvHckbrd])\s*\{?\s*([A-Za-z])\s*\}?\}?",
        r"\1",
        value,
    )
    value = re.sub(r"\\(?:ae|AE|oe|OE|aa|AA|o|O|l|L)\b", " ", value)
    value = re.sub(r"\\[A-Za-z]+\*?(?:\[[^]]*\])?", " ", value)
    value = value.replace("--", "-").replace("~", " ")
    value = re.sub(r"[{}$\\_^]", " ", value)
    value = html.unescape(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^0-9A-Za-z]+", " ", value).lower()
    return " ".join(value.split())


def title_similarity(left: str, right: str) -> float:
    a, b = normalize_text(left), normalize_text(right)
    if not a or not b:
        return 0.0
    seq = SequenceMatcher(None, a, b).ratio()
    at, bt = set(a.split()), set(b.split())
    jaccard = len(at & bt) / max(1, len(at | bt))
    return max(seq, jaccard)


def author_surnames(value: str) -> list[str]:
    names = []
    for author in re.split(r"\s+and\s+", value, flags=re.IGNORECASE):
        author = author.strip()
        if not author or author.lower() in {"others", "et al."}:
            continue
        surname = author.split(",", 1)[0] if "," in author else author.split()[-1]
        names.append(normalize_text(surname))
    return [name for name in names if name]


def surname_equivalent(expected: str, source: str) -> bool:
    """Compare a BibTeX family name with imperfect Crossref family fields."""

    expected = normalize_text(expected)
    source = normalize_text(source)
    if not expected or not source:
        return False
    return (
        expected == source
        or source.endswith(" " + expected)
        or expected.endswith(" " + source)
    )


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 25.0,
    retries: int = 4,
) -> tuple[int, Any, str]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, json.loads(response.read().decode("utf-8")), response.geturl()
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries:
                return exc.code, None, exc.geturl()
            retry_after = exc.headers.get("Retry-After", "")
            try:
                delay = float(retry_after)
            except ValueError:
                delay = min(8.0, 0.75 * (2**attempt))
            time.sleep(max(0.25, min(delay, 15.0)))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == retries:
                return 0, {"error": str(exc)}, url
            time.sleep(min(8.0, 0.75 * (2**attempt)))
    return 0, {"error": "retry loop exhausted"}, url


def semantic_scholar_batch(entries: Iterable[BibEntry]) -> dict[str, dict[str, Any]]:
    doi_entries = [entry for entry in entries if entry.fields.get("doi")]
    if not doi_entries:
        return {}
    output: dict[str, dict[str, Any]] = {}
    for offset in range(0, len(doi_entries), 100):
        batch = doi_entries[offset : offset + 100]
        ids = [f"DOI:{entry.fields['doi']}" for entry in batch]
        status, data, _ = _request_json(
            S2_BATCH_API + "?fields=title,year,authors,externalIds",
            method="POST",
            payload={"ids": ids},
            timeout=40.0,
        )
        if status != 200 or not isinstance(data, list):
            for entry in batch:
                output[entry.key] = {"status": "API_UNAVAILABLE", "http_status": status}
            continue
        for entry, record in zip(batch, data, strict=True):
            if record is None:
                output[entry.key] = {"status": "S2_NOT_FOUND", "http_status": status}
                continue
            external = record.get("externalIds") or {}
            returned_doi = str(external.get("DOI") or "")
            requested_doi = entry.fields["doi"]
            verdict = (
                "S2_VERIFIED"
                if returned_doi.casefold() == requested_doi.casefold()
                else "DOI_MISMATCH"
            )
            output[entry.key] = {
                "status": verdict,
                "http_status": status,
                "title": record.get("title") or "",
                "year": record.get("year"),
                "doi": returned_doi,
            }
        time.sleep(0.2)
    return output


def _crossref_years(message: dict[str, Any]) -> set[int]:
    years: set[int] = set()
    for name in ("published-print", "published-online", "published", "issued", "created"):
        parts = ((message.get(name) or {}).get("date-parts") or [])
        if parts and parts[0]:
            try:
                years.add(int(parts[0][0]))
            except (TypeError, ValueError):
                pass
    return years


def verify_doi(
    entry: BibEntry,
    s2: dict[str, Any],
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doi = entry.fields["doi"].strip()
    endpoint = DOI_API.format(urllib.parse.quote(doi, safe=""))
    status, data, final_url = _request_json(endpoint)
    row: dict[str, Any] = {
        "key": entry.key,
        "entry_type": entry.entry_type,
        "doi": doi,
        "url": entry.fields.get("url", ""),
        "query": endpoint,
        "top_result_url": f"https://doi.org/{doi}",
        "http_status": status,
        "s2_status": s2.get("status", "NOT_RUN"),
        "s2_http_status": s2.get("http_status", ""),
        "source_title": "",
        "source_authors": "",
        "source_venue": "",
        "source_volume": "",
        "source_pages": "",
        "source_years": "",
        "title_similarity": 0.0,
        "author_match": False,
        "year_match": False,
        "venue_match": False,
        "volume_match": False,
        "pages_match": False,
        "existence_verdict": "NOT_FOUND",
        "bibliographic_verdict": "NOT_VERIFIED",
        "notes": "",
    }
    if status != 200 or not isinstance(data, dict) or not isinstance(data.get("message"), dict):
        row["notes"] = "Crossref did not return a work record."
        if override and override.get("verified"):
            row.update(
                {
                    "top_result_url": str(override.get("source_url") or row["top_result_url"]),
                    "source_title": str(override.get("title") or ""),
                    "source_authors": str(override.get("authors") or ""),
                    "source_venue": str(override.get("venue") or ""),
                    "source_volume": str(override.get("volume") or ""),
                    "source_pages": str(override.get("pages") or ""),
                    "source_years": str(override.get("year") or ""),
                    "title_similarity": 1.0,
                    "author_match": True,
                    "year_match": True,
                    "venue_match": True,
                    "volume_match": True,
                    "pages_match": True,
                    "existence_verdict": "VERIFIED",
                    "bibliographic_verdict": "VERIFIED",
                    "notes": str(override.get("notes") or "Reviewed primary-source override."),
                }
            )
        return row
    message = data["message"]
    titles = message.get("title") or []
    source_title = str(titles[0]) if titles else ""
    similarity = title_similarity(entry.fields.get("title", ""), source_title)
    bib_authors = author_surnames(entry.fields.get("author", ""))
    source_authors_raw = [normalize_text(str(author.get("family", ""))) for author in message.get("author") or []]
    has_open_author_list = bool(re.search(r"\band\s+(?:others|et\s+al\.?)\b", entry.fields.get("author", ""), re.I))
    author_match = bool(
        bib_authors
        and source_authors_raw
        and (
            surname_equivalent(bib_authors[0], source_authors_raw[0])
            if has_open_author_list
            else len(bib_authors) == len(source_authors_raw)
            and all(
                surname_equivalent(expected, source)
                for expected, source in zip(bib_authors, source_authors_raw, strict=True)
            )
        )
    )
    years = _crossref_years(message)
    bib_date = entry.fields.get("date") or entry.fields.get("year") or ""
    try:
        bib_year = int(re.sub(r"\D", "", bib_date)[:4])
    except ValueError:
        bib_year = 0
    year_match = not bib_year or bib_year in years or any(abs(bib_year - year) <= 1 for year in years)
    containers = [str(value) for value in message.get("container-title") or []]
    source_venue = containers[0] if containers else str(message.get("publisher") or "")
    bib_venue = (
        entry.fields.get("journaltitle")
        or entry.fields.get("journal")
        or entry.fields.get("booktitle")
        or entry.fields.get("publisher")
        or ""
    )
    venue_match = not bib_venue or title_similarity(bib_venue, source_venue) >= 0.45
    source_volume = str(message.get("volume") or "")
    bib_volume = entry.fields.get("volume", "")
    volume_match = not bib_volume or not source_volume or normalize_text(bib_volume) == normalize_text(source_volume)
    source_pages = str(message.get("page") or "")
    bib_pages = entry.fields.get("pages", "")
    pages_match = not bib_pages or not source_pages or normalize_text(bib_pages) == normalize_text(source_pages)
    metadata_ok = all(
        (
            similarity >= 0.80,
            author_match,
            year_match,
            venue_match,
            volume_match,
            pages_match,
        )
    )
    row.update(
        {
            "source_title": source_title,
            "source_authors": ";".join(source_authors_raw),
            "source_venue": source_venue,
            "source_volume": source_volume,
            "source_pages": source_pages,
            "source_years": ";".join(str(year) for year in sorted(years)),
            "title_similarity": round(similarity, 4),
            "author_match": author_match,
            "year_match": year_match,
            "venue_match": venue_match,
            "volume_match": volume_match,
            "pages_match": pages_match,
            "existence_verdict": "VERIFIED",
            "bibliographic_verdict": "VERIFIED" if metadata_ok else "MISMATCH",
            "notes": "Crossref metadata matched." if metadata_ok else "Review title, first author, or year mismatch.",
        }
    )
    if s2.get("status") == "DOI_MISMATCH":
        row["bibliographic_verdict"] = "MISMATCH"
        row["notes"] += " Semantic Scholar returned a different DOI."
    if override and override.get("verified"):
        row.update(
            {
                "top_result_url": str(override.get("source_url") or row["top_result_url"]),
                "source_title": str(override.get("title") or row["source_title"]),
                "source_authors": str(override.get("authors") or row["source_authors"]),
                "source_venue": str(override.get("venue") or row["source_venue"]),
                "source_volume": str(override.get("volume") or row["source_volume"]),
                "source_pages": str(override.get("pages") or row["source_pages"]),
                "source_years": str(override.get("year") or row["source_years"]),
                "title_similarity": 1.0,
                "author_match": True,
                "year_match": True,
                "venue_match": True,
                "volume_match": True,
                "pages_match": True,
                "existence_verdict": "VERIFIED",
                "bibliographic_verdict": "VERIFIED",
                "notes": str(override.get("notes") or "Reviewed primary-source override."),
            }
        )
    return row


def _fetch_url(url: str, timeout: float = 25.0) -> tuple[int, str, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            raw = response.read(2_000_000)
            if content_type == "application/pdf" or raw.startswith(b"%PDF"):
                title = ""
                text = raw.decode("latin-1", errors="ignore")
                match = re.search(r"/Title\s*\((.*?)\)", text, flags=re.DOTALL)
                if match:
                    title = match.group(1)
            else:
                text = raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
                match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
                title = re.sub(r"<[^>]+>", " ", html.unescape(match.group(1))).strip() if match else ""
            return response.status, response.geturl(), content_type, title
    except urllib.error.HTTPError as exc:
        return exc.code, exc.geturl(), "", ""
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, url, "", str(exc)


def verify_url(entry: BibEntry, override: dict[str, Any] | None) -> dict[str, Any]:
    url = str((override or {}).get("source_url") or entry.fields.get("url") or "")
    title = entry.fields.get("title", "")
    if not url:
        return {
            "key": entry.key,
            "entry_type": entry.entry_type,
            "doi": "",
            "url": "",
            "query": normalize_text(title),
            "top_result_url": "",
            "http_status": 0,
            "s2_status": "NOT_APPLICABLE",
            "s2_http_status": "",
            "source_title": "",
            "source_authors": "",
            "source_venue": "",
            "source_volume": "",
            "source_pages": "",
            "source_years": "",
            "title_similarity": 0.0,
            "author_match": False,
            "year_match": False,
            "venue_match": False,
            "volume_match": False,
            "pages_match": False,
            "existence_verdict": "NOT_FOUND",
            "bibliographic_verdict": "NOT_VERIFIED",
            "notes": "No DOI, URL, or reviewed metadata override.",
        }
    status, final_url, content_type, page_title = _fetch_url(url)
    authoritative_title = str((override or {}).get("title") or page_title)
    similarity = title_similarity(title, authoritative_title)
    override_verified = bool((override or {}).get("verified"))
    # A reviewed override records a human verification against the stated
    # primary source.  Preserve the live HTTP result separately, but do not
    # demote that audit merely because a publisher blocks automated clients or
    # a university mirror is temporarily unavailable.
    existence = "VERIFIED" if override_verified or 200 <= status < 400 else "NOT_FOUND"
    metadata = "VERIFIED" if override_verified or (existence == "VERIFIED" and similarity >= 0.55) else "NOT_VERIFIED"
    return {
        "key": entry.key,
        "entry_type": entry.entry_type,
        "doi": "",
        "url": entry.fields.get("url", ""),
        "query": url,
        "top_result_url": final_url,
        "http_status": status,
        "s2_status": "NOT_APPLICABLE",
        "s2_http_status": "",
        "source_title": authoritative_title,
        "source_authors": str((override or {}).get("authors") or ""),
        "source_venue": str((override or {}).get("venue") or ""),
        "source_volume": str((override or {}).get("volume") or ""),
        "source_pages": str((override or {}).get("pages") or ""),
        "source_years": str((override or {}).get("year") or ""),
        "title_similarity": round(similarity, 4),
        "author_match": bool((override or {}).get("author_match", override_verified)),
        "year_match": bool((override or {}).get("year_match", override_verified)),
        "venue_match": bool((override or {}).get("venue_match", override_verified)),
        "volume_match": bool((override or {}).get("volume_match", override_verified)),
        "pages_match": bool((override or {}).get("pages_match", override_verified)),
        "existence_verdict": existence,
        "bibliographic_verdict": metadata,
        "notes": (
            str((override or {}).get("notes") or "Reviewed metadata override and live source matched.")
            if metadata == "VERIFIED"
            else f"Live {content_type or 'source'} did not expose enough matching metadata; manual review required."
        ),
    }


def _strip_tex_comments(text: str) -> str:
    cleaned: list[str] = []
    for line in text.splitlines():
        cut = len(line)
        for index, character in enumerate(line):
            if character != "%":
                continue
            slashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                slashes += 1
                cursor -= 1
            if slashes % 2 == 0:
                cut = index
                break
        cleaned.append(line[:cut])
    return "\n".join(cleaned)


def _without_literal_iffalse(text: str) -> str:
    """Remove literal disabled branches while retaining their ``\\else`` arm."""

    source = _strip_tex_comments(text)
    token_re = re.compile(r"\\(?:iffalse|iftrue|else|fi)(?![A-Za-z@])")
    stack: list[bool] = []
    output: list[str] = []
    cursor = 0

    def visible() -> bool:
        return all(stack)

    for match in token_re.finditer(source):
        if visible():
            output.append(source[cursor : match.start()])
        token = match.group(0)
        if token == r"\iffalse":
            stack.append(False)
        elif token == r"\iftrue":
            stack.append(True)
        elif token == r"\else" and stack:
            stack[-1] = not stack[-1]
        elif token == r"\fi" and stack:
            stack.pop()
        cursor = match.end()
    if stack:
        raise ValueError("unclosed literal TeX conditional")
    if visible():
        output.append(source[cursor:])
    return "".join(output)


def active_tex_sources(tex_root: Path, entrypoints: Iterable[Path]) -> list[Path]:
    """Resolve the active input graph from the declared document entrypoints."""

    root = tex_root.resolve()
    pending = [
        (path if path.is_absolute() else root / path).resolve()
        for path in entrypoints
        if (path if path.is_absolute() else root / path).is_file()
    ]
    visited: set[Path] = set()
    while pending:
        source = pending.pop()
        if source in visited or not source.is_file():
            continue
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"TeX input escapes the declared root: {source}") from exc
        visited.add(source)
        active = _without_literal_iffalse(source.read_text(encoding="utf-8", errors="replace"))
        for match in INPUT_RE.finditer(active):
            name = match.group(1)
            candidate = root / name
            if candidate.suffix == "":
                candidate = candidate.with_suffix(".tex")
            if not candidate.is_file():
                candidate = source.parent / name
                if candidate.suffix == "":
                    candidate = candidate.with_suffix(".tex")
            if candidate.is_file():
                pending.append(candidate.resolve())
    return sorted(visited)


def extract_citations(
    tex_root: Path,
    entrypoints: Iterable[Path] | None = None,
) -> tuple[dict[str, int], list[str]]:
    counts: dict[str, int] = {}
    scanned: list[str] = []
    if entrypoints is None:
        defaults = [tex_root / "main.tex", tex_root / "monograph" / "main.tex"]
        paths = active_tex_sources(tex_root, defaults)
        if not paths:
            paths = sorted(tex_root.rglob("*.tex"))
    else:
        paths = active_tex_sources(tex_root, entrypoints)
    for path in paths:
        text = _without_literal_iffalse(path.read_text(encoding="utf-8", errors="replace"))
        scanned.append(path.as_posix())
        for match in CITE_RE.finditer(text):
            for key in match.group(1).split(","):
                key = key.strip()
                if key and key != "*":
                    counts[key] = counts.get(key, 0) + 1
    return counts, scanned


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, required=True)
    parser.add_argument("--tex-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overrides", type=Path)
    parser.add_argument(
        "--entrypoint",
        action="append",
        type=Path,
        help="TeX entrypoint relative to --tex-root; repeat for multiple deliverables",
    )
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args(argv)

    entries = parse_bibtex(args.bib)
    overrides: dict[str, Any] = {}
    if args.overrides and args.overrides.exists():
        overrides = json.loads(args.overrides.read_text(encoding="utf-8"))
    checked_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    s2_results = semantic_scholar_batch(entries)

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {}
        for entry in entries:
            if entry.fields.get("doi"):
                future = pool.submit(
                    verify_doi,
                    entry,
                    s2_results.get(entry.key, {}),
                    overrides.get(entry.key),
                )
            else:
                future = pool.submit(verify_url, entry, overrides.get(entry.key))
            futures[future] = entry.key
        for future in as_completed(futures):
            row = future.result()
            row["checked_at_utc"] = checked_at
            rows.append(row)
    rows.sort(key=lambda row: str(row["key"]).casefold())

    citations, scanned_files = extract_citations(args.tex_root, args.entrypoint)
    bib_keys = {entry.key for entry in entries}
    cited_keys = set(citations)
    # A .bib file is a source database, not the rendered reference list:
    # biblatex prints only cited keys unless ``\\nocite{*}`` is active.  Keep
    # unused database records visible for curation, but do not misclassify
    # them as orphan references in the PDF.
    ghost_rows = [
        {"issue": "uncited_database_entry", "key": key, "count": 0}
        for key in sorted(bib_keys - cited_keys)
    ] + [
        {"issue": "dangling_citation", "key": key, "count": citations[key]}
        for key in sorted(cited_keys - bib_keys)
    ]

    audit_fields = [
        "key",
        "entry_type",
        "doi",
        "url",
        "query",
        "top_result_url",
        "http_status",
        "s2_status",
        "s2_http_status",
        "source_title",
        "source_authors",
        "source_venue",
        "source_volume",
        "source_pages",
        "source_years",
        "title_similarity",
        "author_match",
        "year_match",
        "venue_match",
        "volume_match",
        "pages_match",
        "existence_verdict",
        "bibliographic_verdict",
        "checked_at_utc",
        "notes",
    ]
    write_csv(args.output_dir / "reference-audit.csv", rows, audit_fields)
    write_csv(args.output_dir / "ghost-citations.csv", ghost_rows, ["issue", "key", "count"])

    summary = {
        "schema_version": 1,
        "checked_at_utc": checked_at,
        "bibliography": args.bib.as_posix(),
        "tex_root": args.tex_root.as_posix(),
        "tex_files_scanned": len(scanned_files),
        "references_total": len(rows),
        "existence_verified": sum(row["existence_verdict"] == "VERIFIED" for row in rows),
        "bibliographic_verified": sum(row["bibliographic_verdict"] == "VERIFIED" for row in rows),
        "mismatches": sum(row["bibliographic_verdict"] == "MISMATCH" for row in rows),
        "not_verified": sum(row["bibliographic_verdict"] == "NOT_VERIFIED" for row in rows),
        "orphan_references": 0,
        "uncited_database_entries": sum(
            row["issue"] == "uncited_database_entry" for row in ghost_rows
        ),
        "dangling_citations": sum(row["issue"] == "dangling_citation" for row in ghost_rows),
        "semantic_scholar": {
            status: sum(record.get("status") == status for record in s2_results.values())
            for status in ("S2_VERIFIED", "S2_NOT_FOUND", "DOI_MISMATCH", "API_UNAVAILABLE")
        },
        "verdict": "PASS"
        if rows
        and all(row["bibliographic_verdict"] == "VERIFIED" for row in rows)
        and not any(row["issue"] == "dangling_citation" for row in ghost_rows)
        else "FAIL",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "reference-audit-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
