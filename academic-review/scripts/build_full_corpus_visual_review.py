"""Build the seven-page literature-review chapter with unified typography.

Pages 1--3 are recompiled from an editable facsimile of the approved reference
so every diagram uses Noto Sans internally. Page 2 receives a narrow editorial
rewrite that preserves the continuous argument. Page 4 is rebuilt from the
full analytical corpus, pages 5--6 connect the evidence to the experimental
design, and page 7 closes the chapter with the bibliometric interpretation.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import fitz


EXPECTED_REFERENCE_SHA256 = (
    "840164c6e6e85be3b265c57dc033fee4f627314bfd13274776ec1fc7e9003028"
)

ORANGE_RGB = (227 / 255, 106 / 255, 46 / 255)
INK_RGB = (12 / 255, 12 / 255, 12 / 255)
RULE_RGB = (0.82, 0.82, 0.82)
FORBIDDEN_VISIBLE_PATTERNS = {
    "red-team": "process label",
    "claim": "process vocabulary",
    "analytic_corpus_v3.csv": "internal dataset filename",
    "method_period_v3.csv": "internal dataset filename",
    "academic-review/literature-review-v3": "internal repository path",
    "closed coalición": "internal state label",
    "guarded margen": "internal state label",
    "executed misión": "internal state label",
    "referencias principales": "intermediate bibliography heading",
    "referencias complementarias": "intermediate bibliography heading",
    "revisión académica de papers": "standalone-document header",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_page_count(path: Path) -> int:
    with fitz.open(path) as document:
        return document.page_count


def compile_tex(directory: Path, source_name: str) -> Path:
    engine = shutil.which("xelatex")
    if engine is None:
        raise RuntimeError("xelatex is required to build the literature review")
    for _ in range(2):
        subprocess.run(
            [engine, "-interaction=nonstopmode", "-halt-on-error", source_name],
            cwd=directory,
            check=True,
        )
    return directory / Path(source_name).with_suffix(".pdf")


def run_analysis(repo_root: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(repo_root / "academic-review" / "scripts" / "build_v3_full_corpus_bibliometrics.py"),
        ],
        cwd=repo_root,
        check=True,
    )


def rewrite_page_two(page: fitz.Page) -> None:
    """Continue the page-two argument without altering the figures above it."""
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    noto_sans_bold = fonts / "NotoSans-Bold.ttf"
    noto_serif = fonts / "NotoSerif-Regular.ttf"
    for font in (noto_sans_bold, noto_serif):
        if not font.exists():
            raise RuntimeError(f"Required font not found: {font}")

    # The editable page already omits the former process-language paragraph.
    # Reserve the lower block without touching the Figure 2b caption or source.
    page.add_redact_annot(fitz.Rect(42.0, 540.0, 570.0, 724.0), fill=(1, 1, 1))
    page.apply_redactions()
    page.insert_font(fontname="NotoSerif", fontfile=noto_serif)

    paragraph = (
        "El mismo patrón se mantiene al introducir la sustitución. Verma et al. "
        "(2019) reemplazan robots durante el transporte, aunque suponen ruta e hitos "
        "conocidos y planificación global [11]. Sahu y Kumar (2026) integran "
        "transporte, detección de fallos y sustitución mediante una arquitectura "
        "maestro-esclavo [27]. Shibata permite retirar e incorporar agentes durante "
        "el control distribuido, pero no selecciona el sustituto desde una flota "
        "heterogénea [14]. La brecha se concentra así en la selección local y en la "
        "continuidad física de la misión. La Figura 3 examina esa intersección y la "
        "autoridad residual de cada etapa."
    )
    spare = page.insert_textbox(
        fitz.Rect(44.3, 548.0, 568.9, 715.0),
        paragraph,
        fontname="NotoSerif",
        fontsize=9.35,
        lineheight=1.10,
        color=INK_RGB,
        align=fitz.TEXT_ALIGN_LEFT,
        overlay=True,
    )
    if spare < 0:
        raise RuntimeError(f"Editorial rewrite overflowed page 2 by {-spare:.2f} pt")


def merge(
    reference: Path,
    replacement_and_bibliometrics: Path,
    integrated_pages: Path,
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with (
        fitz.open(reference) as legacy,
        fitz.open(replacement_and_bibliometrics) as replacement,
        fitz.open(integrated_pages) as integrated,
    ):
        merged = fitz.open()
        merged.insert_pdf(legacy, from_page=0, to_page=2)
        rewrite_page_two(merged[1])
        merged.insert_pdf(replacement, from_page=0, to_page=0)
        merged.insert_pdf(integrated)
        merged.insert_pdf(replacement, from_page=1, to_page=1)
        merged.set_metadata(
            {
                "title": "Marco teórico y estado del arte: coordinación multi-AMR",
                "author": "Jorge Luis Mayorga Taborda",
                "subject": "Marco teórico y estado del arte para el TFM MROB",
                "keywords": "MROB, MRTA, coaliciones, transporte cooperativo, bibliometría",
                "creator": "XeLaTeX + Matplotlib + NetworkX + PyMuPDF reproducible build",
            }
        )
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", dir=output.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        try:
            merged.save(temporary_path, garbage=4, deflate=True)
            merged.close()
            os.replace(temporary_path, output)
        finally:
            temporary_path.unlink(missing_ok=True)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    exact_dir = repo_root / "academic-review" / "literature-review-v3" / "compact-6p-exact"
    full_dir = repo_root / "academic-review" / "literature-review-v3" / "compact-7p-full"
    reference = exact_dir / "legacy" / "academic_literature_review_reference.pdf"
    typography_dir = full_dir / "legacy-typography"
    typography_source = "MROB_literature_review_reference_typography.tex"
    output = repo_root / "output" / "pdf" / "MROB_literature_review_7p_full_corpus_bibliometrics.pdf"

    reference_hash = sha256(reference)
    if reference_hash != EXPECTED_REFERENCE_SHA256:
        raise RuntimeError(
            "The approved visual reference differs from the frozen source: "
            f"{reference_hash}"
        )
    if pdf_page_count(reference) != 4:
        raise RuntimeError("The approved visual reference must contain four pages")

    typography_reference = compile_tex(typography_dir, typography_source)
    if pdf_page_count(typography_reference) != 3:
        raise RuntimeError("The editable typography reference must contain three pages")

    run_analysis(repo_root)
    replacement = compile_tex(
        full_dir, "MROB_literature_review_full_corpus_pages_4_7.tex"
    )
    integrated = compile_tex(
        exact_dir, "MROB_literature_review_v3_update_2p.tex"
    )
    if pdf_page_count(replacement) != 2:
        raise RuntimeError("The replacement source must produce pages 4 and 7")
    if pdf_page_count(integrated) != 2:
        raise RuntimeError("The integrated SP1--SP3 source must produce pages 5--6")

    merge(typography_reference, replacement, integrated, output)
    if pdf_page_count(output) != 7:
        raise RuntimeError("The final full-corpus review must contain seven pages")

    with fitz.open(reference) as legacy, fitz.open(typography_reference) as typography, fitz.open(output) as final:
        for page_index in range(3):
            if legacy[page_index].rect != typography[page_index].rect:
                raise RuntimeError(f"Typography source changed page {page_index + 1} geometry")
            if typography[page_index].rect != final[page_index].rect:
                raise RuntimeError(f"Page {page_index + 1} geometry changed unexpectedly")
        visible_text = "\n".join(page.get_text("text") for page in final).lower()
        for pattern, reason in FORBIDDEN_VISIBLE_PATTERNS.items():
            if pattern in visible_text:
                raise RuntimeError(f"Visible {reason} remains in final PDF: {pattern}")

    manifest = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "output": str(output.relative_to(repo_root)).replace("\\", "/"),
        "output_sha256": sha256(output),
        "pages": 7,
        "assembly": [
            {
                "pages": "1-3",
                "source": str((typography_dir / typography_source).relative_to(repo_root)).replace("\\", "/"),
                "source_sha256": sha256(typography_dir / typography_source),
                "compiled_sha256": sha256(typography_reference),
                "typography": "Noto Sans inside figures; Noto Serif for prose, captions and source lines",
            },
            {
                "page": 2,
                "source": str((typography_dir / typography_source).relative_to(repo_root)).replace("\\", "/"),
                "editorial_rewrite": True,
            },
            {"page": 4, "source": str(replacement.relative_to(repo_root)).replace("\\", "/"), "source_page": 1},
            {"pages": "5-6", "source": str(integrated.relative_to(repo_root)).replace("\\", "/"), "sha256": sha256(integrated)},
            {"page": 7, "source": str(replacement.relative_to(repo_root)).replace("\\", "/"), "source_page": 2},
        ],
        "approved_visual_reference": {
            "path": str(reference.relative_to(repo_root)).replace("\\", "/"),
            "sha256": reference_hash,
            "role": "geometry and visual provenance",
        },
        "analysis_manifest": "academic-review/literature-review-v3/compact-7p-full/analysis_manifest.json",
    }
    manifest_path = full_dir / "build_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
