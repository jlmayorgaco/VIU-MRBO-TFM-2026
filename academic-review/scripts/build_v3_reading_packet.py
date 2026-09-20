"""Create a bounded source-text workbench for close reading V3 papers.

The packet is deliberately not a synthesis.  It presents passages from locally
verified text with page markers so that a reviewer can verify evidence against
the underlying article before completing its evidence card.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
QUEUE = V3 / "data" / "priority_reading_queue_v3.csv"
AUDIT = V3 / "data" / "fulltext_adequacy_audit_v3.csv"


def clean(value: Any) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def strip_markup(raw: bytes) -> str:
    decoded = raw.decode("utf-8", errors="ignore")
    decoded = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", decoded)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", decoded))).strip()


def extract_pages(path: Path) -> list[str]:
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
        return completed.stdout.decode("utf-8", errors="ignore").split("\f")
    return [strip_markup(path.read_bytes())]


def find_excerpt(pages: list[str], pattern: str, reverse: bool = False, width: int = 1800) -> tuple[int, str] | None:
    indexed = list(enumerate(pages, start=1))
    if reverse:
        indexed.reverse()
    matcher = re.compile(pattern, flags=re.I)
    for page, text in indexed:
        matches = list(matcher.finditer(text))
        if not matches:
            continue
        match = matches[-1] if reverse else matches[0]
        start = max(0, match.start() - 180)
        end = min(len(text), match.end() + width)
        return page, re.sub(r"\s+", " ", text[start:end]).strip()
    return None


def excerpt_block(pages: list[str]) -> list[tuple[str, int, str]]:
    patterns = [
        ("Resumen o introducción", r"\b(abstract|introduction)\b", False),
        ("Método o formulación", r"\b(method|methodology|approach|formulation|algorithm)\b", False),
        ("Resultados o evaluación", r"\b(results|experiments|evaluation|simulation)\b", False),
        ("Conclusión o limitación", r"\b(conclusion|conclusions|discussion|future work|limitation)\b", True),
    ]
    excerpts: list[tuple[str, int, str]] = []
    seen: set[tuple[int, str]] = set()
    for label, pattern, reverse in patterns:
        located = find_excerpt(pages, pattern, reverse=reverse)
        if located is None:
            continue
        page, text = located
        fingerprint = (page, text[:160])
        if fingerprint not in seen:
            excerpts.append((label, page, text))
            seen.add(fingerprint)
    return excerpts


def build_packet(
    queue_rows: list[dict[str, str]],
    audit_by_id: dict[str, dict[str, str]],
    tier: str,
    limit: int,
    offset: int = 0,
) -> str:
    eligible = [
        row for row in queue_rows
        if clean(row.get("priority_tier")) == tier
        and clean(audit_by_id.get(clean(row.get("candidate_id")), {}).get("close_reading_eligibility")) == "eligible"
    ]
    selected = eligible[max(offset, 0):max(offset, 0) + max(limit, 0)]
    lines = [
        f"# V3 close-reading packet: {tier} (eligible offset {max(offset, 0)})",
        "",
        "These are source-text excerpts for review. They are not verified claims, summaries or citation-ready prose.",
        "A completed evidence card must still record the exact supporting passage and its scientific interpretation.",
        "",
    ]
    for position, row in enumerate(selected, start=1):
        path = BASE / clean(row.get("fulltext_local_path"))
        lines.extend(
            [
                f"## {position}. {row['title']}",
                "",
                f"- Candidate: `{row['candidate_id']}`",
                f"- Citation: {row['authors']} ({row['year']}). {row['venue']}. DOI: {row['doi'] or 'not recorded'}",
                f"- Routing only: {row['review_targets_routing_only']}; priority `{row['priority_tier']}` ({row['priority_score']}).",
                f"- Local text: `{row['fulltext_local_path']}`",
                "",
            ]
        )
        try:
            pages = extract_pages(path)
            for label, page, excerpt in excerpt_block(pages):
                lines.extend([f"### {label} (p. {page})", "", excerpt, ""])
        except Exception as exc:
            lines.extend([f"Extraction error: `{type(exc).__name__}: {exc}`", ""])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", default="P0")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Number of eligible records in the selected tier to skip before building the packet.",
    )
    parser.add_argument("--output", type=Path, default=V3 / "packets" / "P0_batch_001.md")
    args = parser.parse_args()
    queue = read_csv(QUEUE)
    audit = {clean(row.get("candidate_id")): row for row in read_csv(AUDIT)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_packet(queue, audit, args.tier, args.limit, args.offset), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
