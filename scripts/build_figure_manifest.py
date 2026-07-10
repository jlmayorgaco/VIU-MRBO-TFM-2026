"""Build a manifest for thesis figures and generated figures."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "generated" / "figure_manifest.csv"
FIGURE_ROOTS = [
    ROOT / "docs" / "doc-05-final-report" / "figures",
    ROOT / "results" / "theory_validation",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(path: Path) -> str:
    text = str(path).lower()
    for token in ("sp1", "sp2", "sp3", "sp4", "sp5", "sp6", "sp7", "sp8", "sp9"):
        if token in text:
            return token.upper()
    if "theory" in text or "v1" in text or "v2" in text or "v3" in text:
        return "THEORY"
    return "GLOBAL"


def main() -> int:
    rows: list[dict[str, object]] = []
    for root in FIGURE_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".png", ".pdf", ".tex"}:
                continue
            rows.append(
                {
                    "figure_id": path.stem,
                    "scope": classify(path),
                    "path": str(path.relative_to(ROOT)),
                    "extension": path.suffix.lower(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path) if path.is_file() and path.suffix.lower() in {".png", ".pdf"} else "",
                    "used_in_doc": "unknown",
                    "caption_source": "generated_or_existing",
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["figure_id", "scope", "path", "extension", "bytes", "sha256", "used_in_doc", "caption_source"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(rows)} figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
