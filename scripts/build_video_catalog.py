"""Build a lightweight catalog of existing MP4 videos."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "video_catalog.csv"
OUT_MD = ROOT / "results" / "VIDEO_CATALOG.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(path: Path) -> str:
    parts = [part.lower() for part in path.parts]
    for sp in ("sp1", "sp2", "sp3", "sp4", "sp5", "sp6", "sp7", "sp8", "sp9"):
        if sp in parts or any(sp in part for part in parts):
            return sp.upper()
    return "NON_CANONICAL"


def main() -> int:
    rows: list[dict[str, object]] = []
    for base in [ROOT / "results"]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.mp4")):
            rows.append(
                {
                    "video_id": path.stem,
                    "SP": classify(path),
                    "path_local": str(path.relative_to(ROOT)),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "used_in_doc": "false",
                    "caption": "",
                }
            )
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video_id", "SP", "path_local", "sha256", "bytes", "used_in_doc", "caption"])
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Video Catalog",
        "",
        "Videos are qualitative inspection artifacts. Heavy MP4 files are not required inside the final PDF.",
        "",
        "| SP | Video | Path |",
        "|---|---|---|",
    ]
    for row in rows[:200]:
        lines.append(f"| {row['SP']} | {row['video_id']} | `{row['path_local']}` |")
    if len(rows) > 200:
        lines.append(f"| ... | {len(rows) - 200} more rows | see `video_catalog.csv` |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)} with {len(rows)} videos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
