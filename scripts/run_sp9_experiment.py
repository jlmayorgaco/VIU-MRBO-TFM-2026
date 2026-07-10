"""Run or block the SP9 CoppeliaSim gap study.

When CoppeliaSim is not installed, this script writes a blocking report instead
of creating fake experiment CSV files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from viu_mrob_tfm.sp9.runner import find_coppeliasim, required_scene_files  # noqa: E402


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_blocked_report(config_path: Path, config: dict, reason: str, missing_scenes: list[Path]) -> Path:
    blocked_dir = ROOT / config["outputs"].get("blocked_dir", "results/sp9/SP9_BLOCKED_EXECUTION")
    blocked_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "PENDING_RUNTIME",
        "reason": reason,
        "config": str(config_path.relative_to(ROOT)),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "missing_scene_files": [str(path.relative_to(ROOT)) for path in missing_scenes],
        "safe_thesis_wording": "SP9 queda preparado como protocolo de brecha teoria-implementacion; no se reporta como evidencia ejecutada hasta disponer de CSV, figuras y manifest de CoppeliaSim.",
    }
    (blocked_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# SP9 Blocked Execution Report",
        "",
        "SP9 is prepared but not promoted as executed evidence.",
        "",
        f"- Status: `{manifest['status']}`",
        f"- Reason: {reason}",
        f"- Config: `{manifest['config']}`",
        "",
        "## Missing Scene Files",
        "",
    ]
    if missing_scenes:
        lines.extend(f"- `{path.relative_to(ROOT)}`" for path in missing_scenes)
    else:
        lines.append("- None detected.")
    lines.extend(
        [
            "",
            "## Thesis Wording",
            "",
            manifest["safe_thesis_wording"],
            "",
        ]
    )
    (blocked_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return blocked_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/sp9/SP9_COPPELIA_gap_study.yaml")
    args = parser.parse_args(argv)
    config_path = (ROOT / args.config).resolve()
    config = load_config(config_path)
    scene_dir = ROOT / config["simulator"]["scene_dir"]
    missing_scenes = [path for path in required_scene_files(scene_dir, config["scenarios"]) if not path.exists()]
    coppelia = find_coppeliasim()
    if missing_scenes:
        blocked = write_blocked_report(config_path, config, "Required CoppeliaSim scene files are missing.", missing_scenes)
        print(f"SP9 blocked: wrote {blocked.relative_to(ROOT)}")
        return 0
    if not coppelia:
        blocked = write_blocked_report(config_path, config, "CoppeliaSim executable was not found in PATH.", missing_scenes)
        print(f"SP9 blocked: wrote {blocked.relative_to(ROOT)}")
        return 0
    blocked = write_blocked_report(
        config_path,
        config,
        f"CoppeliaSim found at {coppelia}, but automated ZMQ execution is not implemented in this freeze. Run the campaign manually with this config and promote only real CSV/figures.",
        missing_scenes,
    )
    print(f"SP9 prepared for manual runtime: wrote {blocked.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
