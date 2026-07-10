"""Build a compact report for V1-V3 theory validation."""

from __future__ import annotations

import json

from tfm_submit_utils import ROOT, THEORY_ROOT, ensure_dir


def main() -> int:
    ensure_dir(THEORY_ROOT)
    manifests = []
    for name in ("v1", "v2", "v3"):
        path = THEORY_ROOT / name / "manifest.json"
        if path.exists():
            manifests.append(json.loads(path.read_text(encoding="utf-8")))
    lines = [
        "# Theory Validation Report",
        "",
        "This report is generated from V1-V3 numerical checks. It supports the thesis theory chapter but does not replace the formal appendix.",
        "",
    ]
    for manifest in manifests:
        lines.append(f"## {manifest.get('validation', 'Validation')}")
        for key, value in manifest.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    if not manifests:
        lines.append("No manifests found. Run `make theory-validation`.")
    (THEORY_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    merged = {"validations": manifests}
    (THEORY_ROOT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"Wrote {(THEORY_ROOT / 'report.md').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
