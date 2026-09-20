"""Build an auditable progress tracker for V3 passage-localized close reading.

The tracker measures workflow state only.  A completed evidence card means that
the named local passages were inspected; it never upgrades a paper into proof of
an untested scientific property.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
QUEUE = V3 / "data" / "priority_reading_queue_v3.csv"
AUDIT = V3 / "data" / "fulltext_adequacy_audit_v3.csv"
CARDS = V3 / "close-read"


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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def card_for(candidate_id: str, cards_dir: Path = CARDS) -> Path | None:
    matches = sorted(cards_dir.glob(f"{candidate_id}_*.md"))
    if len(matches) > 1:
        raise ValueError(f"More than one evidence card found for {candidate_id}")
    return matches[0] if matches else None


def display_path(path: Path) -> str:
    """Use a repository-relative path in production and a stable path in tests."""
    try:
        return str(path.relative_to(BASE)).replace("\\", "/")
    except ValueError:
        return str(path)


def make_tracker(queue_rows: list[dict[str, str]], audit_rows: list[dict[str, str]], cards_dir: Path = CARDS) -> list[dict[str, str]]:
    audit_by_id = {clean(row.get("candidate_id")): row for row in audit_rows}
    rows: list[dict[str, str]] = []
    for source in queue_rows:
        candidate_id = clean(source.get("candidate_id"))
        audit = audit_by_id.get(candidate_id, {})
        card = card_for(candidate_id, cards_dir)
        access = clean(audit.get("close_reading_eligibility"))
        if card:
            status = "completed_passage_localized_card"
        elif access == "eligible":
            status = "ready_for_close_reading"
        else:
            status = "requires_fulltext_or_manual_access_check"
        rows.append(
            {
                "candidate_id": candidate_id,
                "priority_tier": clean(source.get("priority_tier")),
                "review_targets_routing_only": clean(source.get("review_targets_routing_only")),
                "title": clean(source.get("title")),
                "access_eligibility": access,
                "close_reading_status": status,
                "evidence_card": display_path(card) if card else "",
                "evidence_card_sha256": sha256(card) if card else "",
                "tracker_note": "Workflow progress only; verify scope and localizers in the card before citation.",
            }
        )
    return rows


def main() -> None:
    queue = read_csv(QUEUE)
    audit = read_csv(AUDIT)
    tracked = make_tracker(queue, audit)
    output = V3 / "data" / "close_reading_tracker_v3.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output, tracked, list(tracked[0]))
    statuses = Counter(row["close_reading_status"] for row in tracked)
    tiers = Counter((row["priority_tier"], row["close_reading_status"]) for row in tracked)
    report = V3 / "reports" / "v3_close_reading_progress.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# V3 close-reading progress",
        "",
        "The counts below track passage-localized evidence cards, not the number of papers that support a final scientific claim.",
        "",
        "## Overall",
        "",
        *[f"- `{status}`: {count}" for status, count in sorted(statuses.items())],
        "",
        "## By priority tier",
        "",
        "| Tier | completed | ready | access/manual check |",
        "| --- | ---: | ---: | ---: |",
    ]
    for tier in sorted({row["priority_tier"] for row in tracked}):
        lines.append(
            f"| {tier} | {tiers[(tier, 'completed_passage_localized_card')]} | "
            f"{tiers[(tier, 'ready_for_close_reading')]} | "
            f"{tiers[(tier, 'requires_fulltext_or_manual_access_check')]} |"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "queue_sha256": sha256(QUEUE),
        "audit_sha256": sha256(AUDIT),
        "tracker_sha256": sha256(output),
        "status_counts": dict(sorted(statuses.items())),
    }
    manifest_path = V3 / "manifests" / "v3_close_reading_tracker_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["status_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
