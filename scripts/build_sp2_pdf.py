"""Compile and validate the standalone canonical SP2 technical report."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPOSITORY_ROOT / "thesis" / "sp2_report"
BUILD_DIR = SOURCE_DIR / "build"
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT / "output" / "pdf" / "SP2_transporte_cooperativo_submit_ready.pdf"
)


def _run(command: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        tail = "\n".join(completed.stdout.splitlines()[-120:])
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{tail}")


def build(output: Path) -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    latex_args = [
        "lualatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={BUILD_DIR.name}",
        "main.tex",
    ]
    _run(latex_args, cwd=SOURCE_DIR)
    _run(["biber", str(BUILD_DIR / "main")], cwd=SOURCE_DIR)
    _run(latex_args, cwd=SOURCE_DIR)
    _run(latex_args, cwd=SOURCE_DIR)
    source_pdf = BUILD_DIR / "main.pdf"
    if not source_pdf.is_file() or source_pdf.stat().st_size < 20_000:
        raise RuntimeError("LaTeX did not produce a plausible PDF.")
    log = (BUILD_DIR / "main.log").read_text(encoding="utf-8", errors="replace")
    forbidden = ("undefined references", "undefined citations")
    if any(token in log.lower() for token in forbidden):
        raise RuntimeError("The PDF contains unresolved references or citations.")
    shutil.copy2(source_pdf, output)
    if output.read_bytes()[:5] != b"%PDF-":
        raise RuntimeError("The output does not have a PDF signature.")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build(args.output.resolve())
    print(f"PDF generated: {result} ({result.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
