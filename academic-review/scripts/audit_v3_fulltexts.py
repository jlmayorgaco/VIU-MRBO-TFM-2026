"""Audit whether V3 close-reading files contain substantive readable text.

This is an operational accessibility check, not a scientific-quality judgment.
It preserves the original acquisition status and prevents landing pages or
extraction-limited PDFs from silently entering the close-reading claim workflow.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
QUEUE = V3 / "data" / "priority_reading_queue_v3.csv"


def clean(value: Any) -> str:
    return str(value or "").strip()


def normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def strip_markup(raw: bytes) -> str:
    decoded = raw.decode("utf-8", errors="ignore")
    decoded = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", decoded)
    return normalise(html.unescape(re.sub(r"(?s)<[^>]+>", " ", decoded)))


def extract_text(path: Path) -> tuple[str, int]:
    if path.suffix.lower() == ".pdf":
        pdftotext = shutil.which("pdftotext") or r"C:\Program Files\MiKTeX\miktex\bin\x64\pdftotext.exe"
        completed = subprocess.run(
            [pdftotext, "-enc", "UTF-8", str(path), "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(f"pdftotext failed: {message or completed.returncode}")
        text = completed.stdout.decode("utf-8", errors="ignore")
        return text, max(1, text.count("\f") + 1)
    return strip_markup(path.read_bytes()), 1


def classify_text(path: Path, text: str, pages: int) -> tuple[str, list[str]]:
    """Return an auditable, conservative reading-access class."""
    words = len(re.findall(r"\b[\w-]+\b", text))
    body = normalise(text).lower()
    landing_page = bool(
        re.search(
            r"this is a preview of subscription content|access this chapter|"
            r"log in via an institution|buy (this )?(chapter|article)|"
            r"subscribe and save",
            body,
        )
    )
    markers = {
        "abstract": bool(re.search(r"\babstract\b", body)),
        "introduction": bool(re.search(r"\bintroduction\b", body)),
        "methods": bool(re.search(r"\b(methods?|methodology|materials and methods)\b", body)),
        "results": bool(re.search(r"\b(results|experiments|evaluation)\b", body)),
        "conclusion": bool(re.search(r"\b(conclusion|conclusions|discussion)\b", body)),
        "references": bool(re.search(r"\b(references|bibliography)\b", body)),
    }
    found = [name for name, present in markers.items() if present]
    body_sections = sum(markers[name] for name in ["introduction", "methods", "results", "conclusion"])
    if path.suffix.lower() == ".pdf":
        if words >= 1200 and pages >= 2 and body_sections >= 2:
            return "substantive_pdf_text", found
        if words < 250:
            return "pdf_needs_ocr_or_alternative", found
        return "pdf_text_limited", found
    if landing_page:
        return "landing_or_abstract_like_html", found
    if words >= 1500 and body_sections >= 2:
        return "substantive_html_text", found
    if words < 1200 or body_sections < 2:
        return "landing_or_abstract_like_html", found
    return "html_text_limited", found


def audit_row(row: dict[str, str]) -> dict[str, Any]:
        relative = clean(row.get("fulltext_local_path"))
        path = BASE / relative
        audit: dict[str, Any] = {
            "candidate_id": clean(row.get("candidate_id")),
            "title": clean(row.get("title")),
            "priority_tier": clean(row.get("priority_tier")),
            "review_targets_routing_only": clean(row.get("review_targets_routing_only")),
            "fulltext_local_path": relative,
            "file_format": path.suffix.lower().lstrip("."),
            "v3_text_adequacy": "",
            "page_count": "",
            "extracted_word_count": "",
            "section_markers": "",
            "file_sha256_matches_queue": "",
            "close_reading_eligibility": "",
            "audit_note": "",
        }
        if not path.is_file():
            audit.update(v3_text_adequacy="missing_file", close_reading_eligibility="blocked", audit_note="The expected local acquisition is unavailable.")
            return audit
        actual_hash = sha256(path)
        audit["file_sha256_matches_queue"] = str(actual_hash == clean(row.get("fulltext_sha256"))).lower()
        try:
            text, pages = extract_text(path)
            classification, markers = classify_text(path, text, pages)
            words = len(re.findall(r"\b[\w-]+\b", text))
            eligible = classification.startswith("substantive_")
            audit.update(
                v3_text_adequacy=classification,
                page_count=pages,
                extracted_word_count=words,
                section_markers=";".join(markers),
                close_reading_eligibility="eligible" if eligible else "requires_alternative_or_manual_inspection",
                audit_note="Automated text-access classification; it does not verify scientific content.",
            )
        except Exception as exc:
            audit.update(
                v3_text_adequacy="extraction_error",
                close_reading_eligibility="requires_alternative_or_manual_inspection",
                audit_note=f"{type(exc).__name__}: {exc}",
            )
        return audit


def audit_queue(queue_rows: list[dict[str, str]], workers: int = 8) -> list[dict[str, Any]]:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(audit_row, queue_rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=QUEUE)
    parser.add_argument("--output", type=Path, default=V3 / "data" / "fulltext_adequacy_audit_v3.csv")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    audited = audit_queue(read_csv(args.queue), workers=max(1, args.workers))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.output, audited, list(audited[0]))
    counts = Counter(row["v3_text_adequacy"] for row in audited)
    report = V3 / "reports" / "v3_fulltext_adequacy_qa.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# V3 full-text adequacy audit\n\n"
        "This is an automated access check, not a review of the paper's scientific quality.\n\n"
        + "\n".join(f"- `{name}`: {count}" for name, count in sorted(counts.items()))
        + "\n\nOnly `substantive_*` files are initially eligible for close reading. Other files remain valid bibliographic acquisitions but require an alternative full text, OCR or manual inspection before they can support a passage-localized claim.\n",
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(args.queue.relative_to(BASE)).replace("\\", "/"),
        "input_sha256": sha256(args.queue),
        "output": str(args.output.relative_to(BASE)).replace("\\", "/"),
        "output_sha256": sha256(args.output),
        "counts": dict(sorted(counts.items())),
    }
    manifest_path = V3 / "manifests" / "v3_fulltext_adequacy_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
