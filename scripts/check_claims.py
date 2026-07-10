"""Scan thesis text for unsafe claim wording."""

from __future__ import annotations

import re
from pathlib import Path

from tfm_submit_utils import DOCS_GENERATED, ROOT, ensure_dir


SCAN_ROOTS = [
    ROOT / "docs" / "doc-05-final-report",
    ROOT / "docs" / "CLAIM_LEDGER.md",
    ROOT / "docs" / "CANONICAL_RESULTS.md",
]

PATTERNS = [
    ("validacion_industrial", re.compile(r"validaci[oó]n industrial|validado industrialmente", re.I)),
    ("hardware_real", re.compile(r"hardware real|robots reales", re.I)),
    ("ganador_universal", re.compile(r"mejor m[eé]todo|gana siempre|supera siempre|SOTA universal", re.I)),
    ("despliegue", re.compile(r"despliegue industrial", re.I)),
    ("garantiza_contexto", re.compile(r"\bgarantiz(?:a|an|ado|ada)\b", re.I)),
]

SAFE_NEGATORS = (
    "no se afirma",
    "no se declara",
    "no declara",
    "no prueba",
    "no permite decir",
    "no permite afirmar",
    "no equivale",
    "no sustituye",
    "queda fuera",
    "sin afirmar",
    "prohibido",
    "no escribir",
    "no afirmar",
    "que se evita",
    "evita confundir",
    "no como",
)


def iter_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.is_file():
            files.append(root)
        elif root.exists():
            files.extend(sorted(root.rglob("*.tex")))
            files.extend(sorted(root.rglob("*.md")))
    return files


def main() -> int:
    ensure_dir(DOCS_GENERATED)
    findings: list[dict[str, object]] = []
    for path in iter_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            lower = line.lower()
            safe_context = any(token in lower for token in SAFE_NEGATORS)
            for name, pattern in PATTERNS:
                if pattern.search(line):
                    severity = "warning" if safe_context or name == "garantiza_contexto" else "critical"
                    findings.append(
                        {
                            "severity": severity,
                            "pattern": name,
                            "file": str(path.relative_to(ROOT)),
                            "line": line_no,
                            "text": line.strip()[:240],
                        }
                    )
    critical = [item for item in findings if item["severity"] == "critical"]
    lines = [
        "# Claim Check Report",
        "",
        f"- Findings: {len(findings)}",
        f"- Critical: {len(critical)}",
        "",
        "| Severity | Pattern | File | Line | Text |",
        "|---|---|---|---:|---|",
    ]
    for item in findings:
        text = str(item["text"]).replace("|", "\\|")
        lines.append(f"| {item['severity']} | {item['pattern']} | `{item['file']}` | {item['line']} | {text} |")
    (DOCS_GENERATED / "claim_check_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Claim check: {len(critical)} critical, {len(findings)} total")
    return 1 if critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
