"""Submit-ready document gate for the VIU TFM.

The gate is intentionally local and dependency-light. It can inspect LaTeX,
Markdown, plain text, DOCX, and PDF files when a local text extractor is
available. It does not certify external plagiarism by itself; use
--similarity-report or --require-similarity-report for a Turnitin-like export.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "generated" / "submit_ready"

TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".tex", ".bib"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | {".docx", ".pdf"}

TEX_INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
CITE_RE = re.compile(r"\\cite[a-zA-Z*]*(?:\[[^\]]*\]){0,2}\{([^}]+)\}")
BIB_RE = re.compile(r"\\(?:bibliography|addbibresource)\{([^}]+)\}")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
REF_RE = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref)\{([^}]+)\}")
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)")

SAFE_NEGATORS = (
    "no se afirma",
    "no se declara",
    "no declara",
    "no prueba",
    "no permite afirmar",
    "no equivale",
    "no sustituye",
    "queda fuera",
    "quedan fuera",
    "sin afirmar",
    "se evita",
    "evita confundir",
    "no como",
    "no se certifica",
    "no es una promesa",
    "ni una promesa",
    "no afirmar",
    "no se debe afirmar",
    "no debe afirmarse",
    "no acredita",
    "no constituye",
    "sin despliegue industrial",
    "sin validacion industrial",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    category: str
    check: str
    message: str
    evidence: str = ""
    recommendation: str = ""


@dataclass(frozen=True)
class DocumentSource:
    path: Path
    kind: str
    raw_text: str
    plain_text: str
    included_files: tuple[Path, ...]
    missing_includes: tuple[str, ...]
    notes: tuple[str, ...]


def relpath(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text_best_effort(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def strip_tex_comment(line: str) -> str:
    escaped = False
    out: list[str] = []
    for char in line:
        if char == "%" and not escaped:
            break
        out.append(char)
        if char == "\\":
            escaped = not escaped
        else:
            escaped = False
    return "".join(out)


def resolve_include(name: str, tex_root: Path, current_dir: Path) -> Path | None:
    cleaned = name.strip().replace("\\", "/")
    if not cleaned or cleaned.startswith("|"):
        return None
    candidate = Path(cleaned)
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".tex")
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    for base in (tex_root, current_dir, ROOT):
        path = (base / candidate).resolve()
        if path.exists():
            return path
    return None


def collect_tex_source(
    path: Path,
    tex_root: Path | None = None,
    seen: set[Path] | None = None,
) -> tuple[str, list[Path], list[str], list[str]]:
    tex_root = tex_root or path.parent
    seen = seen or set()
    path = path.resolve()
    if path in seen:
        return "", [], [], [f"Skipped recursive include: {relpath(path)}"]
    seen.add(path)

    text = read_text_best_effort(path)
    pieces = [text]
    included = [path]
    missing: list[str] = []
    notes: list[str] = []

    for line in text.splitlines():
        uncommented = strip_tex_comment(line)
        optional = "\\IfFileExists" in uncommented
        for match in TEX_INPUT_RE.finditer(uncommented):
            include_name = match.group(1)
            include_path = resolve_include(include_name, tex_root, path.parent)
            if include_path is None:
                message = f"{include_name} referenced from {relpath(path)}"
                if optional:
                    notes.append(f"Optional include not present: {message}")
                else:
                    missing.append(message)
                continue
            child_text, child_included, child_missing, child_notes = collect_tex_source(
                include_path,
                tex_root=tex_root,
                seen=seen,
            )
            pieces.append(f"\n\n% BEGIN included: {relpath(include_path)}\n")
            pieces.append(child_text)
            included.extend(child_included)
            missing.extend(child_missing)
            notes.extend(child_notes)

    return "\n".join(pieces), included, missing, notes


def latex_to_plain(text: str) -> str:
    text = "\n".join(strip_tex_comment(line) for line in text.splitlines())
    text = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", " ", text, flags=re.DOTALL)
    text = re.sub(r"\\(?:begin|end)\{[^}]+\}", "\n", text)
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(
        r"\\(?:cite[a-zA-Z*]*|ref|eqref|autoref|cref|Cref|label|url|href|input|include|"
        r"bibliography|bibliographystyle|includegraphics)(?:\[[^\]]*\])*\{[^}]*\}",
        " ",
        text,
    )
    text = re.sub(
        r"\\(?:section|subsection|subsubsection|paragraph|caption|keywords|"
        r"setviutitle|setviustudent|setviututor|setviuedition|setviudate|"
        r"setviuheadertitle)\*?(?:\[[^\]]*\])?\{([^{}]*)\}",
        r"\n\1\n",
        text,
    )
    for _ in range(5):
        text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r" \1 ", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}_$^&#~]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def docx_to_text(path: Path) -> tuple[str, list[str]]:
    notes: list[str] = []
    parts: list[str] = []
    xml_names: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name == "word/document.xml":
                xml_names.append(name)
            elif re.match(r"word/(header|footer|footnotes|endnotes)\d*\.xml$", name):
                xml_names.append(name)
        for name in sorted(xml_names):
            try:
                root = ElementTree.fromstring(archive.read(name))
            except ElementTree.ParseError as exc:
                notes.append(f"Could not parse {name}: {exc}")
                continue
            texts = [
                node.text
                for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
                if node.text
            ]
            if texts:
                parts.append("\n".join(texts))
    return "\n\n".join(parts), notes


def pdf_to_text(path: Path) -> tuple[str, list[str]]:
    pages, notes = pdf_to_pages(path)
    return "\n\n".join(pages), notes


def pdf_to_pages(path: Path) -> tuple[list[str], list[str]]:
    notes: list[str] = []
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        completed = subprocess.run(
            [pdftotext, "-layout", "-enc", "UTF-8", str(path), "-"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=90,
            check=False,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            notes.append("Extracted PDF text with pdftotext.")
            pages = completed.stdout.split("\f")
            if pages and not pages[-1].strip():
                pages.pop()
            return pages, notes
        notes.append(f"pdftotext failed: {completed.stderr.strip()[:240]}")

    try:
        import pypdf  # type: ignore[import-not-found]
    except Exception:
        notes.append("No pdftotext or pypdf extractor available for PDF content.")
        return [], notes

    reader = pypdf.PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    if any(page.strip() for page in pages):
        notes.append("Extracted PDF text with pypdf.")
    else:
        notes.append("pypdf found no extractable text.")
    return pages, notes


def extract_document(path: Path) -> DocumentSource:
    suffix = path.suffix.lower()
    kind = suffix.lstrip(".") or "unknown"
    if not path.exists():
        return DocumentSource(path, kind, "", "", (), (), (f"File does not exist: {path}",))

    if suffix == ".tex":
        raw, included, missing, notes = collect_tex_source(path)
        return DocumentSource(path, kind, raw, latex_to_plain(raw), tuple(included), tuple(missing), tuple(notes))
    if suffix in {".md", ".markdown", ".txt", ".bib"}:
        raw = read_text_best_effort(path)
        return DocumentSource(path, kind, raw, raw, (path,), (), ())
    if suffix == ".docx":
        text, notes = docx_to_text(path)
        return DocumentSource(path, kind, text, text, (path,), (), tuple(notes))
    if suffix == ".pdf":
        text, notes = pdf_to_text(path)
        return DocumentSource(path, kind, text, text, (path,), (), tuple(notes))
    return DocumentSource(
        path,
        kind,
        "",
        "",
        (path,),
        (),
        (f"Unsupported file suffix: {suffix or '<none>'}",),
    )


def normalize_for_search(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9%]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def word_tokens(text: str) -> list[str]:
    return re.findall(r"\b[a-z0-9]{2,}\b", normalize_for_search(text))


def sentence_lengths(text: str) -> list[int]:
    lengths: list[int] = []
    for sentence in re.split(r"[.!?]+", text):
        count = len(word_tokens(sentence))
        if count >= 3:
            lengths.append(count)
    return lengths


def paragraph_lengths(text: str) -> list[int]:
    lengths: list[int] = []
    for paragraph in re.split(r"\n\s*\n", text):
        count = len(word_tokens(paragraph))
        if count >= 20:
            lengths.append(count)
    return lengths


def prose_for_style_checks(doc: DocumentSource) -> str:
    if doc.path.suffix.lower() != ".tex":
        return doc.plain_text

    raw = doc.raw_text
    captions = re.findall(r"\\caption(?:\[[^\]]*\])?\{(.*?)\}", raw, flags=re.DOTALL)
    raw = re.sub(
        r"% BEGIN included: [^\r\n]*/figures/[^\r\n]*\r?\n.*?(?=\n\n% BEGIN included:|\Z)",
        " ",
        raw,
        flags=re.DOTALL | re.IGNORECASE,
    )
    removable_environments = (
        "table",
        "table*",
        "tabular",
        "tabularx",
        "longtable",
        "equation",
        "equation*",
        "align",
        "align*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "algorithm",
        "algorithmic",
        "tikzpicture",
        "figure",
        "figure*",
        "itemize",
        "enumerate",
        "description",
    )
    for environment in removable_environments:
        raw = re.sub(
            rf"\\begin\{{{re.escape(environment)}\}}.*?\\end\{{{re.escape(environment)}\}}",
            " ",
            raw,
            flags=re.DOTALL | re.IGNORECASE,
        )
    raw = re.sub(r"\\\[.*?\\\]", " ", raw, flags=re.DOTALL)
    raw = re.sub(r"\$[^$]*\$\s*--\s*\$[^$]*\$", " ", raw)
    caption_text = "\n\n".join(latex_to_plain(caption) for caption in captions)
    return latex_to_plain(raw) + "\n" + caption_text


def has_any_pattern(blob: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, blob) for pattern in patterns)


def add_extraction_findings(doc: DocumentSource, findings: list[Finding]) -> None:
    if not doc.path.exists():
        findings.append(
            Finding(
                "blocker",
                "file",
                "exists",
                "The submitted file path does not exist.",
                str(doc.path),
                "Pass FILE=<path> to an existing manuscript file.",
            )
        )
        return
    if doc.path.suffix.lower() not in SUPPORTED_SUFFIXES:
        findings.append(
            Finding(
                "blocker",
                "file",
                "supported-format",
                "The file type is not supported by the local gate.",
                doc.path.suffix or "<no suffix>",
                "Use .tex, .md, .txt, .docx, or a text-extractable .pdf.",
            )
        )
    if not doc.plain_text.strip():
        findings.append(
            Finding(
                "blocker",
                "file",
                "extractable-text",
                "No text could be extracted from the file.",
                relpath(doc.path),
                "For PDF, install pdftotext or provide the LaTeX/DOCX source.",
            )
        )
    for item in doc.missing_includes:
        findings.append(
            Finding(
                "blocker",
                "latex",
                "missing-input",
                "A required LaTeX input/include file is missing.",
                item,
                "Fix the path or remove the input before submitting.",
            )
        )
    for note in doc.notes:
        findings.append(Finding("info", "file", "extraction-note", note))


def check_template(doc: DocumentSource, findings: list[Finding]) -> None:
    raw = doc.raw_text
    raw_norm = normalize_for_search(raw)
    blob = normalize_for_search(raw + "\n" + doc.plain_text)
    if doc.kind == "tex":
        required_tokens = {
            "article documentclass": ("documentclass", "article"),
            "12pt A4": ("12pt", "a4paper"),
            "VIU style package": ("usepackage", "viu mrob midreport"),
            "VIU cover": ("makeviucover",),
            "VIU title metadata": ("setviutitle", "setviustudent", "setviututor"),
            "VIU date metadata": ("setviuedition", "setviudate", "setviuheadertitle"),
        }
        for check, tokens in required_tokens.items():
            if not all(token in raw_norm for token in tokens):
                findings.append(
                    Finding(
                        "blocker",
                        "viu-template",
                        check,
                        "The LaTeX source does not expose the expected VIU template element.",
                        ", ".join(tokens),
                        "Use docs/doc-05-final-report/main.tex as the canonical source.",
                    )
                )
        if "viu mrob midreport" in raw_norm and not (doc.path.parent / "viu-mrob-midreport.sty").exists():
            findings.append(
                Finding(
                    "blocker",
                    "viu-template",
                    "style-file",
                    "The VIU style package is referenced but not present beside the main .tex file.",
                    relpath(doc.path.parent / "viu-mrob-midreport.sty"),
                    "Keep viu-mrob-midreport.sty next to main.tex.",
                )
            )
    elif not has_any_pattern(blob, (r"\bviu\b", r"universidad internacional de valencia")):
        findings.append(
            Finding(
                "warning",
                "viu-template",
                "brand-marker",
                "The extracted text does not contain an obvious VIU institutional marker.",
                "No VIU/Universidad Internacional de Valencia marker found.",
                "Review that the exported document still uses the VIU cover/template.",
            )
        )


def check_viu_sections(doc: DocumentSource, findings: list[Finding], require_ai_declaration: bool) -> None:
    blob = normalize_for_search(doc.raw_text + "\n" + doc.plain_text)
    required = [
        ("portada institucional", (r"makeviucover", r"universidad internacional de valencia", r"\bviu\b"), "blocker"),
        ("resumen", (r"\bresumen\b", r"viuabstract"), "blocker"),
        ("palabras clave", (r"palabras clave", r"\bkeywords\b"), "blocker"),
        ("indice/contenido", (r"\bindice\b", r"\bcontenido\b", r"tableofcontents"), "blocker"),
        ("nomenclatura/glosario", (r"nomenclatura", r"glosario"), "warning"),
        ("introduccion", (r"introduccion", r"introduction"), "blocker"),
        ("estado del arte / marco teorico", (r"estado del arte", r"marco teorico", r"theoretical framework"), "blocker"),
        ("objetivos", (r"objetivo", r"objectives"), "blocker"),
        ("hipotesis de partida", (r"hipotesis de partida", r"\bhipotesis\b", r"hypothesis"), "blocker"),
        ("metodologia", (r"metodologia", r"methodology"), "blocker"),
        ("resultados y analisis", (r"resultados", r"analisis", r"validacion"), "blocker"),
        ("validacion de los resultados", (r"validacion de los resultados",), "blocker"),
        ("conclusiones y recomendaciones", (r"conclusiones y recomendaciones",), "blocker"),
        ("bibliografia/referencias", (r"bibliografia", r"referencias", r"bibliography", r"bibliographystyle"), "blocker"),
        ("anexos", (r"\banexo\b", r"\banexos\b", r"appendix"), "blocker"),
    ]
    for check, patterns, severity in required:
        if not has_any_pattern(blob, patterns):
            findings.append(
                Finding(
                    severity,
                    "viu-requirements",
                    check,
                    "The document does not show a required VIU thesis block.",
                    " / ".join(patterns),
                    "Add or expose the section in the submitted manuscript.",
                )
            )

    ai_patterns = (
        r"ia generativa",
        r"inteligencia artificial",
        r"uso de ia",
        r"herramientas de ia",
        r"chatgpt",
        r"openai",
    )
    if not has_any_pattern(blob, ai_patterns):
        severity = "blocker" if require_ai_declaration else "warning"
        findings.append(
            Finding(
                severity,
                "viu-requirements",
                "declaracion-ia",
                "No explicit generative-AI use declaration was found.",
                "Expected one of: IA generativa, inteligencia artificial, uso de IA.",
                "Add a short appendix or front/back matter statement if the call requires it.",
            )
        )

    if doc.path.suffix.lower() == ".tex":
        order_source = read_text_best_effort(doc.path)
        ordered_commands = [
            ("introduccion", r"\\(?:input|include)\{[^}]*01-introduction(?:\.tex)?\}|\\section\{Introducci[oó]n\}"),
            ("objetivos", r"\\(?:input|include)\{[^}]*02-objectives(?:\.tex)?\}|\\section\{Objetivos\}"),
            ("hipotesis", r"\\(?:input|include)\{[^}]*03-hypothesis(?:\.tex)?\}|\\section\{Hip[oó]tesis(?: de partida)?\}"),
            ("metodologia", r"\\(?:input|include)\{[^}]*04-methodology(?:\.tex)?\}|\\section\{Metodolog[ií]a\}"),
            ("marco teorico", r"\\(?:input|include)\{[^}]*05-theoretical-framework[^}]*\}|\\section\{Marco te[oó]rico[^}]*\}"),
            ("resultados y analisis", r"\\(?:input|include)\{[^}]*06-results-and-analysis[^}]*\}|\\section\{Resultados y an[aá]lisis\}"),
            ("conclusiones y recomendaciones", r"\\(?:input|include)\{[^}]*07-conclusions(?:\.tex)?\}|\\section\{Conclusiones y recomendaciones\}"),
            ("referencias bibliograficas", r"\\section\{Referencias bibliogr[aá]ficas\}"),
            ("anexos", r"\\appendix\b"),
        ]
        positions: list[tuple[str, int]] = []
        missing_order_markers: list[str] = []
        for name, pattern in ordered_commands:
            match = re.search(pattern, order_source, flags=re.IGNORECASE)
            if match is None:
                missing_order_markers.append(name)
            else:
                positions.append((name, match.start()))
        if not missing_order_markers:
            actual_order = [name for name, _ in sorted(positions, key=lambda item: item[1])]
            expected_order = [name for name, _ in positions]
            if actual_order != expected_order:
                findings.append(
                    Finding(
                        "blocker",
                        "viu-requirements",
                        "section-order",
                        "The LaTeX sections do not follow the VIU MROB order documented on 17 June 2026.",
                        " -> ".join(actual_order),
                        "Place references before appendices and preserve the required chapter sequence.",
                    )
                )


def check_figure_attribution(doc: DocumentSource, findings: list[Finding]) -> None:
    if doc.path.suffix.lower() != ".tex":
        return
    figure_blocks = re.findall(
        r"\\begin\{figure\}(?:\[[^\]]*\])?(.*?)\\end\{figure\}",
        doc.raw_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    unattributed = []
    source_pattern = re.compile(
        r"\\viuownsource\b|\\viusource\{|elaboraci[oó]n propia|fuente\s*:|adaptado de|tomado de",
        flags=re.IGNORECASE,
    )
    for block in figure_blocks:
        if "\\caption" not in block or source_pattern.search(block):
            continue
        label = re.search(r"\\label\{([^}]+)\}", block)
        unattributed.append(label.group(1) if label else "figure-without-label")
    if unattributed:
        findings.append(
            Finding(
                "blocker",
                "figure-attribution",
                "source-note",
                "One or more figures have captions but no authorship/source note.",
                f"{len(unattributed)} figure(s): {', '.join(unattributed[:12])}",
                "Use \\viuownsource for original work or \\viusource{...} for adapted/external material.",
            )
        )


def parse_cite_keys(raw_text: str) -> set[str]:
    keys: set[str] = set()
    for match in CITE_RE.finditer(raw_text):
        for key in match.group(1).split(","):
            key = key.strip()
            if key:
                keys.add(key)
    return keys


def parse_bib_paths(raw_text: str, base_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for match in BIB_RE.finditer(raw_text):
        for name in match.group(1).split(","):
            candidate = Path(name.strip())
            if candidate.suffix == "":
                candidate = candidate.with_suffix(".bib")
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            paths.append(candidate.resolve())
    return paths


def parse_bib_keys(paths: Iterable[Path]) -> tuple[set[str], list[Path]]:
    keys: set[str] = set()
    missing: list[Path] = []
    for path in paths:
        if not path.exists():
            missing.append(path)
            continue
        text = read_text_best_effort(path)
        keys.update(match.group(1).strip() for match in BIB_KEY_RE.finditer(text))
    return keys, missing


def check_references(doc: DocumentSource, findings: list[Finding], min_citations: int, min_bib_entries: int) -> None:
    words = len(word_tokens(doc.plain_text))
    if doc.kind == "tex":
        cite_keys = parse_cite_keys(doc.raw_text)
        bib_paths = parse_bib_paths(doc.raw_text, doc.path.parent)
        bib_keys, missing_bibs = parse_bib_keys(bib_paths)

        if not bib_paths:
            findings.append(
                Finding(
                    "blocker",
                    "bibliography",
                    "bibliography-command",
                    "The LaTeX manuscript has no bibliography command.",
                    relpath(doc.path),
                    "Add \\bibliography{references} or \\addbibresource{references.bib}.",
                )
            )
        for path in missing_bibs:
            findings.append(
                Finding(
                    "blocker",
                    "bibliography",
                    "bib-file-exists",
                    "A bibliography file referenced by the manuscript is missing.",
                    relpath(path),
                    "Fix the bibliography path before submission.",
                )
            )
        if cite_keys and bib_keys:
            missing_keys = sorted(cite_keys - bib_keys)
            if missing_keys:
                findings.append(
                    Finding(
                        "blocker",
                        "bibliography",
                        "citation-keys-resolve",
                        "Some citation keys are not present in the bibliography.",
                        ", ".join(missing_keys[:25]),
                        "Fix the citation key or add the missing BibTeX entry.",
                    )
                )
        if words >= 5000 and len(cite_keys) < min_citations:
            findings.append(
                Finding(
                    "warning",
                    "bibliography",
                    "citation-density",
                    "The manuscript has a low number of citation commands for a full TFM.",
                    f"{len(cite_keys)} citation keys; threshold {min_citations}.",
                    "Review whether literature/state-of-the-art claims are fully supported.",
                )
            )
        if bib_paths and len(bib_keys) < min_bib_entries:
            findings.append(
                Finding(
                    "warning",
                    "bibliography",
                    "bibliography-size",
                    "The bibliography appears small for a final TFM.",
                    f"{len(bib_keys)} BibTeX entries; threshold {min_bib_entries}.",
                    "Review VIU expectations and the state-of-the-art coverage.",
                )
            )
        labels = set(LABEL_RE.findall(doc.raw_text))
        refs = set(REF_RE.findall(doc.raw_text))
        unresolved = sorted(refs - labels)
        if unresolved:
            findings.append(
                Finding(
                    "warning",
                    "latex",
                    "cross-references",
                    "Some LaTeX references do not have labels in the collected source.",
                    ", ".join(unresolved[:25]),
                    "Run the LaTeX build and fix unresolved references.",
                )
            )
    else:
        blob = normalize_for_search(doc.plain_text)
        if len(word_tokens(doc.plain_text)) >= 5000 and not has_any_pattern(blob, (r"referencias", r"bibliografia")):
            findings.append(
                Finding(
                    "blocker",
                    "bibliography",
                    "references-section",
                    "No references/bibliography marker was found in the extracted text.",
                    relpath(doc.path),
                    "Ensure the exported manuscript includes the bibliography.",
                )
            )


def check_claim_safety(doc: DocumentSource, findings: list[Finding]) -> None:
    patterns = [
        ("validacion-industrial", re.compile(r"\bvalidacion industrial\b|\bvalidado industrialmente\b")),
        ("hardware-real", re.compile(r"\bhardware real\b|\brobots reales\b")),
        ("ganador-universal", re.compile(r"mejor metodo|gana siempre|supera siempre|sota universal|dominancia universal")),
        ("despliegue-industrial", re.compile(r"\bdespliegue industrial\b")),
        ("certificacion", re.compile(r"\bcertificacion\b|\bcertifica\b|\bcertificado\b")),
        ("garantia-fuerte", re.compile(r"\bgarantiza\b|\bgarantizan\b|\bgarantizado\b|\bgarantizada\b")),
    ]
    lines = doc.plain_text.splitlines()
    for index, line in enumerate(lines):
        line_no = index + 1
        normalized = normalize_for_search(line)
        if not normalized:
            continue
        context = " ".join(lines[max(0, index - 1) : index + 2])
        normalized_context = normalize_for_search(context)
        safe = any(token in normalized_context for token in SAFE_NEGATORS)
        for name, pattern in patterns:
            if pattern.search(normalized) and not safe:
                severity = "warning" if name in {"certificacion", "garantia-fuerte"} else "blocker"
                findings.append(
                    Finding(
                        severity,
                        "claim-safety",
                        name,
                        "The manuscript uses a high-risk claim without a nearby limiter.",
                        f"line {line_no}: {line.strip()[:220]}",
                        "Qualify the claim or connect it to explicit evidence.",
                    )
                )


def check_placeholders(doc: DocumentSource, findings: list[Finding]) -> None:
    raw = doc.raw_text
    raw_norm = normalize_for_search(raw)
    blocker_patterns = {
        "todo": r"\bTODO\b",
        "fixme": r"\bFIXME\b",
        "lorem-ipsum": r"lorem ipsum",
        "tbd": r"\bTBD\b",
        "xxx": r"\bXXX\b",
    }
    for name, pattern in blocker_patterns.items():
        source = raw_norm if name == "lorem-ipsum" else raw
        count = len(re.findall(pattern, source))
        if count:
            findings.append(
                Finding(
                    "blocker",
                    "readiness",
                    f"placeholder-{name}",
                    "The manuscript still contains placeholder/editorial markers.",
                    f"{count} occurrence(s) of {name}.",
                    "Remove placeholders before submission.",
                )
            )
    pending_count = len(re.findall(r"\bpendiente\b|\bcompletar\b", raw_norm))
    if pending_count:
        findings.append(
            Finding(
                "warning",
                "readiness",
                "pending-markers",
                "The manuscript contains Spanish pending/completion markers.",
                f"{pending_count} occurrence(s) of pendiente/completar.",
                "Check whether they are editorial notes or legitimate prose.",
            )
        )


def check_document_size(doc: DocumentSource, findings: list[Finding], min_words: int) -> None:
    words = len(word_tokens(doc.plain_text))
    if words < min_words:
        findings.append(
            Finding(
                "blocker",
                "readiness",
                "word-count",
                "The document is shorter than the configured full-manuscript threshold.",
                f"{words} words; threshold {min_words}.",
                "Pass the complete final manuscript or lower --min-words for a partial check.",
            )
        )


def heading_line_index(page_text: str, patterns: tuple[str, ...]) -> int | None:
    for index, line in enumerate(page_text.splitlines()):
        normalized = normalize_for_search(line)
        if any(re.fullmatch(pattern, normalized) for pattern in patterns):
            return index
    return None


def last_heading_page(page_texts: list[str], patterns: tuple[str, ...]) -> int | None:
    matches = [
        index
        for index, page_text in enumerate(page_texts)
        if heading_line_index(page_text, patterns) is not None
    ]
    return matches[-1] if matches else None


def calculate_page_budget(page_texts: list[str]) -> dict[str, int | bool] | None:
    intro_page = last_heading_page(page_texts, (r"1 introduccion",))
    appendix_page = last_heading_page(
        page_texts,
        (
            r"a desarrollo matematico extendido",
            r"a reproducibilidad",
            r"(?:anexo|apendice) a(?: .+)?",
        ),
    )
    references_page = last_heading_page(
        page_texts,
        (r"(?:8 )?referencias", r"(?:8 )?referencias bibliograficas", r"(?:8 )?bibliografia"),
    )
    if intro_page is None or appendix_page is None or references_page is None:
        return None
    if intro_page >= appendix_page or intro_page >= references_page:
        return None

    appendix_line = heading_line_index(
        page_texts[appendix_page],
        (
            r"a desarrollo matematico extendido",
            r"a reproducibilidad",
            r"(?:anexo|apendice) a(?: .+)?",
        ),
    )
    assert appendix_line is not None
    prefix = "\n".join(page_texts[appendix_page].splitlines()[:appendix_line])
    appendix_shares_main_page = len(word_tokens(prefix)) >= 20

    pages_before_appendices = appendix_page - intro_page
    if appendix_shares_main_page:
        pages_before_appendices += 1

    if appendix_page < references_page:
        appendix_pages = references_page - appendix_page
        reference_pages = len(page_texts) - references_page
        main_pages = pages_before_appendices + reference_pages
    else:
        main_pages = pages_before_appendices
        appendix_pages = len(page_texts) - appendix_page

    return {
        "total_pdf_pages": len(page_texts),
        "introduction_pdf_page": intro_page + 1,
        "appendix_pdf_page": appendix_page + 1,
        "references_pdf_page": references_page + 1,
        "main_pages": main_pages,
        "appendix_pages": appendix_pages,
        "appendix_shares_main_page": appendix_shares_main_page,
    }


def check_page_budget(
    doc: DocumentSource,
    findings: list[Finding],
    max_main_pages: int,
    max_appendix_pages: int,
    configured_pdf: Path | None,
) -> None:
    if configured_pdf is not None:
        pdf_path = configured_pdf
    elif doc.path.suffix.lower() == ".pdf":
        pdf_path = doc.path
    elif doc.path.suffix.lower() == ".tex":
        pdf_path = doc.path.with_suffix(".pdf")
    else:
        pdf_path = None

    if pdf_path is None or not pdf_path.exists():
        findings.append(
            Finding(
                "warning",
                "page-budget",
                "compiled-pdf",
                "The page limits could not be checked because no compiled PDF was found.",
                relpath(pdf_path) if pdf_path is not None else doc.kind,
                "Compile the final PDF and re-run the gate before submission.",
            )
        )
        return

    page_texts, notes = pdf_to_pages(pdf_path)
    budget = calculate_page_budget(page_texts)
    if budget is None:
        findings.append(
            Finding(
                "warning",
                "page-budget",
                "section-boundaries",
                "The gate could not locate Introduction, Appendix A, and References in the PDF.",
                "; ".join(notes),
                "Check the PDF headings and count the pages manually.",
            )
        )
        return

    evidence = (
        f"Main document: {budget['main_pages']}/{max_main_pages}; "
        f"appendices: {budget['appendix_pages']}/{max_appendix_pages}; "
        f"Introduction starts on PDF page {budget['introduction_pdf_page']}, "
        f"Appendix A on {budget['appendix_pdf_page']}, and References on "
        f"{budget['references_pdf_page']}."
    )
    if int(budget["main_pages"]) > max_main_pages:
        findings.append(
            Finding(
                "blocker",
                "page-budget",
                "main-pages",
                f"The main document exceeds the configured {max_main_pages}-page VIU submission limit.",
                evidence,
                "Reduce the main document; cover and front matter are already excluded.",
            )
        )
    else:
        findings.append(
            Finding(
                "info",
                "page-budget",
                "main-pages",
                "The main document is within the configured page limit.",
                evidence,
            )
        )

    if int(budget["appendix_pages"]) > max_appendix_pages:
        excess = int(budget["appendix_pages"]) - max_appendix_pages
        findings.append(
            Finding(
                "blocker",
                "page-budget",
                "appendix-pages",
                f"The appendices exceed the configured {max_appendix_pages}-page VIU submission limit.",
                f"{evidence} Excess: {excess} page(s).",
                "Condense the appendices to essential evidence or move non-required material to the repository.",
            )
        )
    else:
        findings.append(
            Finding(
                "info",
                "page-budget",
                "appendix-pages",
                "The appendices are within the configured page limit.",
                evidence,
            )
        )


def check_human_writing(
    doc: DocumentSource,
    findings: list[Finding],
    warn_density: float,
    block_density: float,
) -> None:
    text = prose_for_style_checks(doc)
    norm = normalize_for_search(text)
    words = max(1, len(word_tokens(text)))
    critical_patterns = {
        "ai-disclaimer": r"como modelo de lenguaje|as an ai|as a language model",
        "chatbot-artifact": r"espero que esto ayude|i hope this helps|great question|excelente pregunta",
        "cutoff-disclaimer": r"hasta mi ultima actualizacion|as of my last update|no tengo acceso a datos en tiempo real",
    }
    for name, pattern in critical_patterns.items():
        count = len(re.findall(pattern, norm))
        if count:
            findings.append(
                Finding(
                    "blocker",
                    "human-writing",
                    name,
                    "The manuscript contains chatbot/AI-process artifacts.",
                    f"{count} occurrence(s).",
                    "Remove model-process language from the submitted manuscript.",
                )
            )

    style_patterns = {
        "cabe-destacar": r"cabe destacar|cabe senalar|cabe mencionar",
        "important-note": r"es importante destacar|es importante senalar|es importante mencionar|es importante notar",
        "present-work": r"en el presente trabajo|a lo largo de este trabajo|a lo largo del trabajo",
        "generic-transition": r"en conclusion|en resumen|en sintesis|por otro lado|por otra parte",
        "broad-context": r"hoy en dia|en la actualidad|en el contexto actual|en una era",
        "ai-verbs": r"profundizar en|adentrarse en|delve into|deep dive|dive into|lets explore|vamos a explorar",
        "inflation": r"sin precedentes|revolucionario|transformador|holistico|vanguardista|game changer",
        "vague-endorsement": r"vale la pena destacar|vale la pena senalar|worth noting|it is worth noting",
        "meta-narration": r"a continuacion (?:se|veremos|presentamos)|este (?:capitulo|apartado) (?:explora|analiza|presenta)|vamos a (?:analizar|examinar|ver)",
        "vague-attribution": r"estudios (?:demuestran|muestran)|la literatura (?:demuestra|confirma)|expertos (?:consideran|afirman)|diversos autores (?:senalan|afirman)",
        "nominalized-process": r"se llevo a cabo|fue llevado a cabo|se procedio a|realizacion de un analisis|ejecucion de un analisis",
        "translation-calque": r"hacer sentido|en orden a|correr (?:un|el) experimento|soportar (?:una|la) hipotesis|direccionar (?:un|el|la) problema|realizar (?:una|la) decision|estar en linea con",
        "confidence-cue": r"resulta evidente|claramente|sin duda|indudablemente|conviene (?:destacar|senalar|mencionar)",
    }
    total_hits = 0
    repeated: list[str] = []
    for name, pattern in style_patterns.items():
        count = len(re.findall(pattern, norm))
        total_hits += count
        if count >= 3:
            repeated.append(f"{name}: {count}")
    density = total_hits / words * 1000.0
    if density >= block_density:
        findings.append(
            Finding(
                "blocker",
                "human-writing",
                "style-density",
                "AI-like filler/style patterns are too dense for a submit-ready manuscript.",
                f"{total_hits} hits, {density:.2f} per 1000 words.",
                "Rewrite flagged prose into specific, evidence-led claims.",
            )
        )
    elif density >= warn_density:
        findings.append(
            Finding(
                "warning",
                "human-writing",
                "style-density",
                "AI-like filler/style patterns are present above the warning threshold.",
                f"{total_hits} hits, {density:.2f} per 1000 words.",
                "Review the generated report and simplify formulaic transitions.",
            )
        )
    if repeated:
        findings.append(
            Finding(
                "warning",
                "human-writing",
                "repeated-style-patterns",
                "Some formulaic writing patterns repeat several times.",
                "; ".join(repeated[:12]),
                "Patch repeated openings/transitions before final export.",
            )
        )

    structural_patterns = {
        "contrastive-reframing": (
            r"\bno (?:es|se trata de)\b.{0,120}?\bsino(?: que| tambien)?\b|\bno es\b.{0,120}?\b(?:es|representa|constituye)\b|\bno solo\b.{0,120}?\bsino(?: tambien)?\b",
            max(2, math.ceil(words / 5000)),
            "Rewrite repeated 'no es A, sino B' structures as direct claims supported by evidence.",
        ),
        "english-calques": (
            style_patterns["translation-calque"],
            1,
            "Replace literal English-to-Spanish calques with idiomatic academic Spanish.",
        ),
    }
    for check, (pattern, threshold, recommendation) in structural_patterns.items():
        count = len(re.findall(pattern, norm))
        if count >= threshold:
            findings.append(
                Finding(
                    "warning",
                    "human-writing",
                    check,
                    "A repeated mechanical writing pattern requires contextual review.",
                    f"{count} occurrence(s); review threshold {threshold}.",
                    recommendation,
                )
            )

    em_dash_count = text.count("\u2014") + len(re.findall(r"\s--\s", text))
    if em_dash_count:
        findings.append(
            Finding(
                "warning",
                "human-writing",
                "dash-frequency",
                "Dash-like separators remain in the manuscript prose.",
                f"{em_dash_count} dash-like separators.",
                "Review every prose occurrence; preserve only LaTeX ranges, CLI options, code, and mathematics.",
            )
        )

    semicolon_count = text.count(";")
    semicolon_density = semicolon_count / words * 1000.0
    punctuation_paragraphs = [
        paragraph
        for paragraph in re.split(r"\n\s*\n", text)
        if len(word_tokens(paragraph)) >= 20
    ]
    semicolon_heavy = [paragraph for paragraph in punctuation_paragraphs if paragraph.count(";") >= 3]
    if len(semicolon_heavy) > 5:
        findings.append(
            Finding(
                "warning",
                "human-writing",
                "semicolon-density",
                "Semicolons accumulate repeatedly inside individual prose paragraphs.",
                f"{len(semicolon_heavy)} paragraphs contain at least 3 semicolons; {semicolon_count} total ({semicolon_density:.2f} per 1000 words).",
                "Review paragraphs with three or more semicolons; keep only grammatical complex links or lists.",
            )
        )

    colon_count = text.count(":")
    colon_density = colon_count / words * 1000.0
    colon_heavy = [paragraph for paragraph in punctuation_paragraphs if paragraph.count(":") >= 2]
    if len(colon_heavy) > 8:
        findings.append(
            Finding(
                "warning",
                "human-writing",
                "colon-density",
                "Repeated colon structures appear across several prose paragraphs.",
                f"{len(colon_heavy)} paragraphs contain at least 2 colons; {colon_count} total ({colon_density:.2f} per 1000 words).",
                "Check that each colon follows a complete clause and introduces a real list or explanation.",
            )
        )

    lengths = sentence_lengths(text)
    if len(lengths) >= 40:
        long_sentences = sum(1 for length in lengths if length > 55)
        if long_sentences / len(lengths) > 0.18:
            findings.append(
                Finding(
                    "warning",
                    "human-writing",
                    "long-sentences",
                    "A large fraction of sentences are very long.",
                    f"{long_sentences}/{len(lengths)} sentences exceed 55 words.",
                    "Split dense paragraphs where readability suffers.",
                )
            )
        mean = statistics.mean(lengths)
        if mean and statistics.pstdev(lengths) / mean < 0.28:
            findings.append(
                Finding(
                    "warning",
                    "human-writing",
                    "sentence-rhythm",
                    "Sentence lengths are unusually uniform.",
                    f"mean={mean:.1f}, stdev={statistics.pstdev(lengths):.1f}.",
                    "Vary sentence length during the final human prose pass.",
                )
            )

    paragraphs = paragraph_lengths(text)
    if len(paragraphs) >= 12:
        mean = statistics.mean(paragraphs)
        if mean and statistics.pstdev(paragraphs) / mean < 0.25:
            findings.append(
                Finding(
                    "warning",
                    "human-writing",
                    "paragraph-rhythm",
                    "Paragraph lengths are very uniform.",
                    f"mean={mean:.1f}, stdev={statistics.pstdev(paragraphs):.1f}.",
                    "Vary paragraph structure where the prose reads mechanically.",
                )
            )


def duplicate_ngrams(words: list[str], n: int = 18) -> list[tuple[str, int]]:
    if len(words) < n * 2:
        return []
    grams = []
    for index in range(0, len(words) - n + 1):
        gram = tuple(words[index : index + n])
        if len(set(gram)) < 8:
            continue
        grams.append(gram)
    counts = Counter(grams)
    repeated = [(gram, count) for gram, count in counts.items() if count > 1]
    repeated.sort(key=lambda item: (-item[1], item[0]))
    return [(" ".join(gram), count) for gram, count in repeated[:10]]


def parse_similarity_score(report_path: Path) -> tuple[float | None, str]:
    report = extract_document(report_path)
    text = report.plain_text or report.raw_text
    if not text.strip():
        return None, "No text could be extracted from the similarity report."
    matches: list[tuple[float, str]] = []
    for match in re.finditer(r"(\d{1,3}(?:[.,]\d+)?)\s*%", text):
        raw_value = match.group(1).replace(",", ".")
        try:
            value = float(raw_value)
        except ValueError:
            continue
        start = max(0, match.start() - 80)
        end = min(len(text), match.end() + 80)
        window = normalize_for_search(text[start:end])
        matches.append((value, window))
    labelled = [
        value
        for value, window in matches
        if any(token in window for token in ("similarity", "similitud", "turnitin", "plagio", "originalidad"))
    ]
    if labelled:
        return max(labelled), "Matched percentage near a similarity/originality label."
    if matches:
        return max(value for value, _ in matches), "Used maximum percentage found in the report text."
    return None, "No percentage was found in the similarity report."


def check_originality(
    doc: DocumentSource,
    findings: list[Finding],
    similarity_report: Path | None,
    require_similarity_report: bool,
    warn_pct: float,
    block_pct: float,
) -> None:
    words = word_tokens(doc.plain_text)
    repeated = duplicate_ngrams(words)
    if repeated:
        findings.append(
            Finding(
                "warning",
                "originality",
                "internal-duplicate-fragments",
                "Long exact fragments repeat inside the manuscript.",
                "; ".join(f"{count}x: {fragment[:120]}" for fragment, count in repeated[:3]),
                "Check whether repeated text is intentional, quoted, or should be consolidated.",
            )
        )

    if similarity_report is None:
        severity = "blocker" if require_similarity_report else "warning"
        findings.append(
            Finding(
                severity,
                "originality",
                "external-similarity-report",
                "No external similarity report was provided.",
                "Local checks cannot certify plagiarism against external corpora.",
                "Run with SIMILARITY_REPORT=<path> or REQUIRE_SIMILARITY=1 for final lock.",
            )
        )
        return

    if not similarity_report.exists():
        findings.append(
            Finding(
                "blocker",
                "originality",
                "similarity-report-exists",
                "The configured similarity report does not exist.",
                str(similarity_report),
                "Pass a valid Turnitin/similarity export path.",
            )
        )
        return

    score, evidence = parse_similarity_score(similarity_report)
    if score is None:
        findings.append(
            Finding(
                "warning",
                "originality",
                "similarity-score-parse",
                "Could not parse a similarity percentage from the report.",
                evidence,
                "Inspect the report manually or provide a text/PDF export with the percentage visible.",
            )
        )
    elif score >= block_pct:
        findings.append(
            Finding(
                "blocker",
                "originality",
                "similarity-score",
                "The external similarity score is above the blocking threshold.",
                f"{score:.1f}% similarity; block threshold {block_pct:.1f}%. {evidence}",
                "Resolve high-similarity passages before final submission.",
            )
        )
    elif score >= warn_pct:
        findings.append(
            Finding(
                "warning",
                "originality",
                "similarity-score",
                "The external similarity score is above the warning threshold.",
                f"{score:.1f}% similarity; warning threshold {warn_pct:.1f}%. {evidence}",
                "Review the similarity report and justify quoted/common-method material.",
            )
        )
    else:
        findings.append(
            Finding(
                "info",
                "originality",
                "similarity-score",
                "The external similarity score is below the configured warning threshold.",
                f"{score:.1f}% similarity.",
            )
        )


def finding_to_dict(finding: Finding) -> dict[str, str]:
    return {
        "severity": finding.severity,
        "category": finding.category,
        "check": finding.check,
        "message": finding.message,
        "evidence": finding.evidence,
        "recommendation": finding.recommendation,
    }


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def slugify(value: str) -> str:
    value = normalize_for_search(value)
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "document"


def write_reports(
    doc: DocumentSource,
    findings: list[Finding],
    output_dir: Path,
    strict: bool,
    args: argparse.Namespace,
) -> tuple[Path, Path, str]:
    ensure_dir(output_dir)
    blockers = [item for item in findings if item.severity == "blocker"]
    warnings = [item for item in findings if item.severity == "warning"]
    if blockers or (strict and warnings):
        status = "FAIL"
    elif warnings:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"

    stem = slugify(f"{doc.path.stem}_{doc.kind}")
    json_path = output_dir / f"{stem}_submit_ready_report.json"
    md_path = output_dir / f"{stem}_submit_ready_report.md"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict": strict,
        "file": relpath(doc.path),
        "kind": doc.kind,
        "word_count": len(word_tokens(doc.plain_text)),
        "included_files": [relpath(path) for path in doc.included_files],
        "missing_includes": list(doc.missing_includes),
        "counts": {
            "blockers": len(blockers),
            "warnings": len(warnings),
            "info": len([item for item in findings if item.severity == "info"]),
        },
        "thresholds": {
            "min_words": args.min_words,
            "min_citations": args.min_citations,
            "min_bib_entries": args.min_bib_entries,
            "max_main_pages": args.max_main_pages,
            "max_appendix_pages": args.max_appendix_pages,
            "similarity_warn_pct": args.similarity_warn_pct,
            "similarity_block_pct": args.similarity_block_pct,
            "human_warn_density": args.human_warn_density,
            "human_block_density": args.human_block_density,
        },
        "findings": [finding_to_dict(item) for item in findings],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Submit Ready Gate",
        "",
        f"- Status: `{status}`",
        f"- File: `{relpath(doc.path)}`",
        f"- Word count: `{payload['word_count']}`",
        f"- Blockers: `{len(blockers)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Strict mode: `{strict}`",
        "",
        "## Scope",
        "",
        "This report is a local pre-submission gate. It checks VIU structure, template markers,",
        "bibliography integrity, claim safety, human-writing heuristics, and local originality",
        "signals. It cannot certify external plagiarism unless a similarity report is provided.",
        "",
        "## Findings",
        "",
        "| Severity | Category | Check | Message | Evidence | Recommendation |",
        "|---|---|---|---|---|---|",
    ]
    severity_rank = {"blocker": 0, "warning": 1, "info": 2}
    for item in sorted(findings, key=lambda finding: (severity_rank.get(finding.severity, 9), finding.category)):
        lines.append(
            "| {severity} | {category} | {check} | {message} | {evidence} | {recommendation} |".format(
                severity=markdown_escape(item.severity),
                category=markdown_escape(item.category),
                check=markdown_escape(item.check),
                message=markdown_escape(item.message),
                evidence=markdown_escape(item.evidence),
                recommendation=markdown_escape(item.recommendation),
            )
        )
    lines.extend(
        [
            "",
            "## Included Files",
            "",
            *[f"- `{relpath(path)}`" for path in doc.included_files],
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, json_path, status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check whether a TFM manuscript is submit-ready.")
    parser.add_argument("--file", required=True, type=Path, help="Path to the manuscript to check.")
    parser.add_argument("--similarity-report", type=Path, help="Optional Turnitin/similarity report export.")
    parser.add_argument(
        "--require-similarity-report",
        action="store_true",
        help="Fail if no external similarity report is provided.",
    )
    parser.add_argument(
        "--require-ai-declaration",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require an explicit generative-AI use declaration.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-words", type=int, default=5000)
    parser.add_argument("--min-citations", type=int, default=20)
    parser.add_argument("--min-bib-entries", type=int, default=20)
    parser.add_argument("--max-main-pages", type=int, default=80)
    parser.add_argument("--max-appendix-pages", type=int, default=8)
    parser.add_argument(
        "--page-count-pdf",
        type=Path,
        help="Optional compiled PDF used to enforce the page limits.",
    )
    parser.add_argument("--similarity-warn-pct", type=float, default=15.0)
    parser.add_argument("--similarity-block-pct", type=float, default=20.0)
    parser.add_argument("--human-warn-density", type=float, default=4.0)
    parser.add_argument("--human-block-density", type=float, default=12.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manuscript = args.file if args.file.is_absolute() else (ROOT / args.file)
    similarity_report = None
    if args.similarity_report is not None:
        similarity_report = args.similarity_report
        if not similarity_report.is_absolute():
            similarity_report = ROOT / similarity_report
    output_dir = args.output_dir if args.output_dir.is_absolute() else (ROOT / args.output_dir)
    page_count_pdf = args.page_count_pdf
    if page_count_pdf is not None and not page_count_pdf.is_absolute():
        page_count_pdf = ROOT / page_count_pdf

    doc = extract_document(manuscript.resolve())
    findings: list[Finding] = []
    add_extraction_findings(doc, findings)
    if doc.plain_text.strip():
        check_document_size(doc, findings, args.min_words)
        check_page_budget(
            doc,
            findings,
            args.max_main_pages,
            args.max_appendix_pages,
            page_count_pdf.resolve() if page_count_pdf else None,
        )
        check_template(doc, findings)
        check_viu_sections(doc, findings, args.require_ai_declaration)
        check_figure_attribution(doc, findings)
        check_references(doc, findings, args.min_citations, args.min_bib_entries)
        check_claim_safety(doc, findings)
        check_placeholders(doc, findings)
        check_human_writing(doc, findings, args.human_warn_density, args.human_block_density)
        check_originality(
            doc,
            findings,
            similarity_report.resolve() if similarity_report else None,
            args.require_similarity_report,
            args.similarity_warn_pct,
            args.similarity_block_pct,
        )

    md_path, json_path, status = write_reports(doc, findings, output_dir.resolve(), args.strict, args)
    blockers = [item for item in findings if item.severity == "blocker"]
    warnings = [item for item in findings if item.severity == "warning"]

    print(f"Submit-ready gate: {status}")
    print(f"Blockers: {len(blockers)} | Warnings: {len(warnings)}")
    print(f"Markdown report: {relpath(md_path)}")
    print(f"JSON report: {relpath(json_path)}")
    for item in blockers[:8]:
        print(f"BLOCKER [{item.category}/{item.check}]: {item.message} {item.evidence}".rstrip())
    if blockers or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
