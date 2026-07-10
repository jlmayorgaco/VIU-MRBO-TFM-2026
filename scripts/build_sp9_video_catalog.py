"""Build a SP9 video catalog if real videos exist."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results" / "sp9" / "SP9_COPPELIA_gap_study"


def main() -> int:
    videos = sorted((RUN_DIR / "videos").glob("*.mp4")) if (RUN_DIR / "videos").exists() else []
    out = RUN_DIR / "video_index.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video_id", "path", "used_in_doc", "caption"])
        writer.writeheader()
        for idx, path in enumerate(videos, start=1):
            writer.writerow({"video_id": f"sp9_video_{idx:03d}", "path": str(path.relative_to(ROOT)), "used_in_doc": "false", "caption": ""})
    print(f"Wrote {out.relative_to(ROOT)} with {len(videos)} videos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
