"""Build the six-page literature review with an exact four-page legacy facsimile.

Pages 1--4 are copied from the approved visual reference. Pages 5--6 are
compiled from the V3 update source and appended without rasterising either PDF.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

import fitz


EXPECTED_REFERENCE_SHA256 = (
    "840164c6e6e85be3b265c57dc033fee4f627314bfd13274776ec1fc7e9003028"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compile_update(update_dir: Path) -> Path:
    engine = shutil.which("xelatex")
    if engine is None:
        raise RuntimeError("xelatex is required to compile the V3 update")

    source = update_dir / "MROB_literature_review_v3_update_2p.tex"
    for _ in range(2):
        subprocess.run(
            [engine, "-interaction=nonstopmode", "-halt-on-error", source.name],
            cwd=update_dir,
            check=True,
        )
    return source.with_suffix(".pdf")


def pdf_page_count(path: Path) -> int:
    with fitz.open(path) as document:
        return document.page_count


def merge_pdfs(reference: Path, update: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(reference) as legacy, fitz.open(update) as supplement:
        merged = fitz.open()
        merged.insert_pdf(legacy)
        merged.insert_pdf(supplement)
        merged.set_metadata(
            {
                "title": "Revisión académica MROB: estado del arte e integración SP1-SP3",
                "author": "Jorge Luis Mayorga Taborda",
                "subject": "Revisión de literatura para el TFM MROB",
                "keywords": "MROB, MRTA, coaliciones, transporte cooperativo, revisión de literatura",
                "creator": "XeLaTeX + PyMuPDF reproducible build",
            }
        )
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", dir=output.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        try:
            merged.save(temporary_path)
            merged.close()
            os.replace(temporary_path, output)
        finally:
            temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    update_dir = (
        repo_root / "academic-review" / "literature-review-v3" / "compact-6p-exact"
    )
    reference = update_dir / "legacy" / "academic_literature_review_reference.pdf"
    output = repo_root / "output" / "pdf" / "MROB_literature_review_6p_exact_visual.pdf"

    reference_hash = sha256(reference)
    if reference_hash != EXPECTED_REFERENCE_SHA256:
        raise RuntimeError(
            "The vendored visual reference differs from the approved source: "
            f"{reference_hash}"
        )
    if pdf_page_count(reference) != 4:
        raise RuntimeError("The approved visual reference must contain exactly four pages")

    update = compile_update(update_dir)
    if pdf_page_count(update) != 2:
        raise RuntimeError("The V3 supplement must contain exactly two pages")

    merge_pdfs(reference, update, output)
    if pdf_page_count(output) != 6:
        raise RuntimeError("The merged deliverable must contain exactly six pages")

    manifest = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "output": str(output.relative_to(repo_root)).replace("\\", "/"),
        "output_sha256": sha256(output),
        "pages": 6,
        "reference": {
            "path": str(reference.relative_to(repo_root)).replace("\\", "/"),
            "sha256": reference_hash,
            "pages": 4,
            "placement": "pages 1-4, vector-preserving insertion",
        },
        "v3_update": {
            "path": str(update.relative_to(repo_root)).replace("\\", "/"),
            "sha256": sha256(update),
            "pages": 2,
            "placement": "pages 5-6",
        },
    }
    manifest_path = update_dir / "build_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
