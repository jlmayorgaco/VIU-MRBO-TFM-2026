#!/usr/bin/env python3
"""Build and validate the pre-thesis source and evidence inventory.

The script is intentionally self-contained and only writes below
``pre-thesis/evidence``.  It inventories the four source corpora without
copying their contents, deduplicates exact byte-identical files with SHA-256,
and creates a conservative first-pass audit of LaTeX formal results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "pre-thesis" / "evidence"
CORPORA = ("books", "work", "paper", "thesis")
CORPUS_ROOTS = {
    "books": REPO_ROOT / "material" / "books",
    "work": REPO_ROOT / "material" / "compendios",
    "paper": REPO_ROOT / "paper",
    "thesis": REPO_ROOT / "thesis",
}
CORPUS_PRIORITY = {"thesis": 0, "paper": 1, "work": 2, "books": 3}
EXPECTED_PDF_COUNTS = {"books": 42, "work": 43}
EXPECTED_UNIQUE_PDF_COUNTS = {"books": 37, "work": 33}
PLANNED_PAPER_FORMAL_COUNT = 104
CURATED_SOURCE_AUDITS = {
    "books": EVIDENCE_DIR / "book-consultation-map.csv",
    "work": EVIDENCE_DIR / "work-thematic-crosswalk.csv",
}
SOURCE_CLAIM_REVIEW = EVIDENCE_DIR / "source-claim-review.csv"
FORMAL_SEMANTIC_AUDIT = (
    EVIDENCE_DIR / "integrity" / "formal-audit" / "semantic-all.csv"
)

VALID_DESTINATIONS = {
    "thesis-body",
    "thesis-appendix",
    "monograph",
    "background",
    "archive-only",
}
VALID_EVIDENCE_STATUSES = {"candidate", "pending-audit", "supported"}
FORMAL_AUDIT_VERDICTS = {"PASS", "LIMITED", "FAIL", "DUPLICATE", "CONJECTURE"}
VALID_SP_TOKENS = {"SP1", "SP2", "SP3", "transversal", "out-of-scope"}
VALID_CLAIM_LINK_STATUSES = {
    "linked",
    "not-applicable",
    "pending-semantic-review",
    "reviewed-unlinked",
}
VALID_CLAIM_RELATIONS = {
    "candidate-only",
    "canonical-reference",
    "context",
    "future-required",
    "mentions",
    "none",
    "refutes",
    "supports",
}
VALID_SYMBOL_STATUSES = {
    "indexed",
    "none-detected",
    "not-applicable",
    "pending-semantic-review",
    "reviewed-local-only",
}

# These units contain or derive scientific claims but cannot be linked safely at
# file granularity.  They remain an explicit semantic backlog until a reviewer
# records the exact claim relation and locator.
CLAIM_SOURCE_OVERRIDES: dict[str, tuple[str, ...]] = {
    # Generated from the same versioned AWS summaries used by C15--C19.  The
    # macro file is a presentation artefact in the evidence chain, not a new
    # claim and not a substitute for RAW/processed results.
    "thesis/generated/aws-industrial2-results.tex": (
        "C15-SP0",
        "C16-SP1SP2",
        "C17-SP1SP2",
        "C18-SP1SP5",
        "C19-SP1SP5SP7",
    ),
}

THESIS_REVIEWED_NON_EVIDENCE: dict[str, str] = {
    "thesis/generated/literature-coverage.tex": (
        "Tabla generada de cobertura bibliográfica; audita el corpus, pero no "
        "constituye evidencia de un claim científico."
    ),
    "thesis/sections/frontmatter/01-summary.tex": (
        "Resumen derivado de resultados enlazados en sus secciones de origen; "
        "no es una fuente de evidencia independiente."
    ),
    "thesis/sections/frontmatter/02-abstract.tex": (
        "Abstract derivado de resultados enlazados en sus secciones de origen; "
        "no es una fuente de evidencia independiente."
    ),
    "thesis/sections/mainmatter/01-introduction.tex": (
        "Encuadre y motivación bibliográfica; las citas se auditan por clave y "
        "los resultados propios se enlazan en sus fuentes de evidencia."
    ),
    "thesis/sections/mainmatter/04-methodology.tex": (
        "Declara modelo, protocolo y límites; no se usa como prueba de los "
        "resultados formales o empíricos que describe."
    ),
    "thesis/sections/mainmatter/06-results-and-analysis/index.tex": (
        "Agregador estructural de Resultados; los claims pertenecen a los "
        "fragmentos incluidos y a sus artefactos versionados."
    ),
    "thesis/sections/mainmatter/07-conclusions.tex": (
        "Síntesis derivada de claims ya adjudicados; no añade evidencia ni "
        "modifica su nivel de soporte."
    ),
}

BOOK_REVIEWED_CONTEXT_ONLY: dict[str, str] = {
    "SRC-7923e0f353c892cb": (
        "Volumen secundario usado como índice de capítulos; no respalda un claim "
        "activo y cualquier capítulo futuro deberá verificarse por separado."
    ),
    "SRC-0b7ceba994fe5772": (
        "Contexto industrial y catálogo de KPI; no respalda algoritmos, resultados "
        "AWS ni una afirmación de realismo físico."
    ),
    "SRC-c0cae4da012e4a4e": (
        "Contenedor de capítulos reservado para consulta; no existe un claim activo "
        "que deba enlazarse al volumen completo."
    ),
    "SRC-fda513c2ae72b910": (
        "Referencia auxiliar para definiciones puntuales de grafos; no sustituye las "
        "fuentes primarias que soportan los claims activos."
    ),
}
FORMAL_ENVIRONMENTS = (
    "teorema",
    "proposicion",
    "lema",
    "corolario",
    "conjetura",
    "theorem",
    "proposition",
    "lemma",
    "corollary",
    "conjecture",
)

MANIFEST_COLUMNS = (
    "unit_id",
    "sha256",
    "path",
    "bytes",
    "media_type",
    "pages_or_section",
    "corpus",
    "is_canonical",
    "canonical_duplicate",
    "sp_target",
    "claim_ids",
    "claim_link_status",
    "claim_relation",
    "claim_link_reason",
    "evidence_locator",
    "symbols",
    "symbol_status",
    "symbol_note",
    "evidence_status",
    "evidence_status_note",
    "use",
    "generator",
    "provenance",
    "license",
)

CROSSWALK_COLUMNS = (
    "unit_id",
    "path",
    "corpus",
    "sha256",
    "canonical_path",
    "is_exact_duplicate",
    "destination",
    "incorporation_mode",
    "sp_target",
    "claim_ids",
    "claim_link_status",
    "claim_relation",
    "claim_link_reason",
    "evidence_locator",
    "evidence_status",
    "evidence_status_note",
    "rationale",
)

FORMAL_AUDIT_COLUMNS = (
    "result_id",
    "corpus",
    "path",
    "source_sha256",
    "line",
    "end_line",
    "environment",
    "title",
    "label",
    "label_occurrences_within_corpus",
    "duplicate_label_within_corpus",
    "inline_proof_detected",
    "proof_line",
    "linked_claim_ids",
    "claim_ledger_states",
    "evidence_status",
    "audit_status",
    "assumptions_audited",
    "domain_audited",
    "units_audited",
    "proof_audited",
    "dependencies_audited",
    "counterexample_audited",
    "evidence_link_audited",
    "notes",
)

LATEX_SECTION_RE = re.compile(
    r"\\(?:chapter|section|subsection)\*?\{([^\n{}]*(?:\{[^\n{}]*\}[^\n{}]*)*)\}",
    re.MULTILINE,
)
FORMAL_BEGIN_RE = re.compile(
    r"\\begin\{(" + "|".join(re.escape(item) for item in FORMAL_ENVIRONMENTS) + r")\}"
    r"\s*(?:\[([^\]]*)\])?",
    re.MULTILINE,
)
LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
PROOF_RE = re.compile(r"\\begin\{proof\}")


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    ledger_state: str
    artifact_tokens: tuple[str, ...]
    raw_line: str


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_unit_id(path: str) -> str:
    suffix = hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]
    return f"SRC-{suffix}"


def stable_unit_path(path: Path, corpus: str) -> str:
    """Preserve IDs assigned before books/work moved below material/."""

    member = path.relative_to(CORPUS_ROOTS[corpus]).as_posix()
    return f"{corpus}/{member}"


def run_git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process.stdout.decode("utf-8", errors="replace").strip()


def git_status_summary() -> dict[str, object]:
    output = run_git("status", "--porcelain=v1", "--untracked-files=all")
    lines = output.splitlines() if output else []
    codes = Counter(line[:2] for line in lines if len(line) >= 2)
    categories = Counter()
    for code, count in codes.items():
        if code == "??":
            categories["untracked"] += count
            continue
        if code == "!!":
            categories["ignored"] += count
            continue
        if "U" in code or code in {"AA", "DD"}:
            categories["conflicted"] += count
        if "D" in code:
            categories["deleted"] += count
        if "M" in code:
            categories["modified"] += count
        if "A" in code:
            categories["added"] += count
        if "R" in code:
            categories["renamed"] += count
        if "C" in code:
            categories["copied"] += count
    return {
        "dirty": bool(lines),
        "total_entries": len(lines),
        "category_counts": dict(sorted(categories.items())),
        "status_code_counts": dict(sorted(codes.items())),
        "note": "Resumen no destructivo; no se restauró, limpió ni modificó el árbol fuente.",
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def pdf_page_count(path: Path) -> tuple[int | None, str | None]:
    executable = shutil.which("pdfinfo")
    pdfinfo_error = "pdfinfo-not-found"
    if executable:
        try:
            process = subprocess.run(
                [executable, str(path)],
                cwd=REPO_ROOT,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            output = process.stdout.decode("utf-8", errors="replace")
            match = re.search(r"(?mi)^Pages:\s*(\d+)\s*$", output)
            if process.returncode == 0 and match:
                return int(match.group(1)), None
            detail = process.stderr.decode("utf-8", errors="replace").strip()
            pdfinfo_error = f"pdfinfo-error:{detail[:120]}"
        except subprocess.TimeoutExpired:
            pdfinfo_error = "pdfinfo-timeout"

    # Poppler on Windows can reject otherwise valid paths longer than MAX_PATH.
    # pypdf receives the already-opened stream and therefore avoids that limit.
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]

        with path.open("rb") as stream:
            return len(PdfReader(stream, strict=False).pages), None
    except Exception as exc:  # pragma: no cover - exercised only for malformed PDFs
        return None, f"{pdfinfo_error};pypdf-error:{type(exc).__name__}:{str(exc)[:100]}"


def first_latex_section(path: Path) -> str:
    text = read_text(path)
    match = LATEX_SECTION_RE.search(text)
    if not match:
        if "\\documentclass" in text:
            return "document-root"
        return "source-fragment"
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return f"section:{title[:240]}"


def media_type(path: Path) -> str:
    extension = path.suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".tex": "text/x-tex",
        ".sty": "text/x-tex-style",
        ".bib": "application/x-bibtex",
        ".json": "application/json",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".csv": "text/csv",
        ".md": "text/markdown",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".ps1": "text/x-powershell",
    }.get(extension, "application/octet-stream")


def parse_claim_ledger() -> list[ClaimRecord]:
    ledger_path = REPO_ROOT / "docs" / "04_CLAIMS_EVIDENCE.md"
    records: list[ClaimRecord] = []
    state_re = re.compile(r"\|\s*(SOPORTADA|PARCIAL|PENDIENTE|REFUTADA|RETIRADA)\s*\|\s*$")
    id_re = re.compile(r"^\|\s*([^|]+?)\s*\|")
    for line in read_text(ledger_path).splitlines():
        id_match = id_re.match(line)
        state_match = state_re.search(line)
        if not id_match or not state_match:
            continue
        claim_id = id_match.group(1).strip()
        if not claim_id.startswith("C"):
            continue
        prefix = line[: state_match.start()]
        last_pipe = prefix.rfind("|")
        artifact_cell = prefix[last_pipe + 1 :] if last_pipe >= 0 else ""
        artifacts = tuple(re.findall(r"`([^`]+)`", artifact_cell))
        records.append(
            ClaimRecord(
                claim_id=claim_id,
                ledger_state=state_match.group(1),
                artifact_tokens=artifacts,
                raw_line=line,
            )
        )
    return records


def normalize_artifact_token(token: str) -> str:
    value = token.replace("\\", "/").strip()
    value = value.split("…", 1)[0].rstrip("/.")
    return value


@lru_cache(maxsize=1)
def audited_formal_claim_ids_by_source() -> dict[str, tuple[str, ...]]:
    """Return exact source/claim links already adjudicated by the formal audit."""

    if not FORMAL_SEMANTIC_AUDIT.exists():
        return {}
    excluded_markers = {"", "NONE", "NONE_IN_DOCS_04"}
    linked: dict[str, set[str]] = defaultdict(set)
    with FORMAL_SEMANTIC_AUDIT.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            source_path = str(row["source_path"]).replace("\\", "/")
            for claim_id in str(row["claim_id"]).split(";"):
                claim_id = claim_id.strip()
                if claim_id not in excluded_markers:
                    linked[source_path].add(claim_id)
    return {
        source_path: tuple(sorted(claim_ids))
        for source_path, claim_ids in linked.items()
    }


def claims_for_path(path: str, claims: Sequence[ClaimRecord]) -> list[ClaimRecord]:
    matches: list[ClaimRecord] = []
    for claim in claims:
        for raw_token in claim.artifact_tokens:
            token = normalize_artifact_token(raw_token)
            if not token:
                continue
            if path == token or path.startswith(token.rstrip("/") + "/"):
                matches.append(claim)
                break
    claims_by_id = {claim.claim_id: claim for claim in claims}
    audited_claim_ids = audited_formal_claim_ids_by_source().get(path, ())
    for claim_id in (*CLAIM_SOURCE_OVERRIDES.get(path, ()), *audited_claim_ids):
        if claim_id not in claims_by_id:
            raise ValueError(f"Unknown claim in source-level audit: {path}:{claim_id}")
        matches.append(claims_by_id[claim_id])
    return sorted(
        {claim.claim_id: claim for claim in matches}.values(),
        key=lambda item: item.claim_id,
    )


def infer_sp_target(path: str, corpus: str) -> str:
    lowered = path.lower()
    name = Path(path).name.lower()

    # ``aws-industrial2`` is the SP3 pilot declared in the research matrix.
    # The results index is a genuine SP1--SP3 aggregator, not an unknown unit.
    if name in {"aws-industrial2.tex", "aws-industrial2-results.tex"}:
        return "SP3"
    if corpus == "thesis" and lowered.endswith(
        "sections/mainmatter/06-results-and-analysis/index.tex"
    ):
        return "SP1;SP2;SP3;transversal"

    legacy_match = re.search(r"(?:^|[^a-z0-9])sp([0-8])(?:[^0-9]|$)", lowered)
    if legacy_match and (corpus in {"work", "thesis"} or "06-results-and-analysis" in lowered):
        stage = int(legacy_match.group(1))
        if stage <= 3:
            return "SP1"
        if stage <= 6:
            return "SP2"
        return "SP3"

    if corpus == "paper":
        sp1_parts = {
            "sec_cfrd.tex",
            "sec_estimacion.tex",
            "sec_informacion.tex",
            "sec_informacion2.tex",
        }
        sp2_parts = {
            "sec_autoridad.tex",
            "sec_clusters.tex",
            "sec_degradacion.tex",
            "sec_fundamentos.tex",
            "sec_modelo_fisico.tex",
            "sec_posicionamiento.tex",
            "sec_robotica.tex",
        }
        sp3_parts = {
            "sec_comunicacion.tex",
            "sec_mision.tex",
            "sec_multiclase.tex",
            "sec_operacion.tex",
            "sec_standby.tex",
            "sec_topologia.tex",
        }
        if name in sp1_parts:
            return "SP1"
        if name in sp2_parts:
            return "SP2"
        if name in sp3_parts:
            return "SP3"

    if "cargo" in lowered or any(term in lowered for term in ("wrench", "caging", "transport", "control cooperativo")):
        return "SP2"
    if any(term in lowered for term in ("pasillo", "traffic", "routing", "route", "mapf", "congestion")):
        return "SP3"
    if any(term in lowered for term in ("coalition", "coalicion", "allocation", "asignacion", "population game", "nash")):
        return "SP1"
    if corpus == "thesis" and "mainmatter/06-results-and-analysis" not in lowered:
        return "transversal"
    if corpus == "paper":
        return "transversal"
    return "unassigned"


SYMBOL_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\\mathcal\s*\{R\}", "R"),
    (r"\\mathcal\s*\{K\}", "K"),
    (r"\\mathcal\s*\{C\}", "C"),
    (r"\\Kcal(?![A-Za-z])", "K"),
    (r"\\Ccal(?![A-Za-z])", "C"),
    (r"\\Gcal(?![A-Za-z])", "G"),
    (r"\\Ncal(?![A-Za-z])", "N_i"),
    (r"\\boldsymbol\s*\{q\}", "q"),
    (r"\\boldsymbol\s*\{x\}", "x"),
    (r"\\boldsymbol\s*\{u\}", "u"),
    (r"\\boldsymbol\s*\{w\}", "w"),
    (
        r"\\(?:boldsymbol|bm)\s*(?:\{W\}|W)|"
        r"\\mathcal\s*(?:\{W\}|W)|\\Wdem(?![A-Za-z])",
        "W",
    ),
    (r"\\Phi", "Phi"),
    (r"\\Psi", "Psi"),
    (r"(?<![A-Za-z])q_i(?![A-Za-z])", "q_i"),
    (r"(?<![A-Za-z])p_i(?![A-Za-z])", "p_i"),
    (r"(?<![A-Za-z])v_i(?![A-Za-z])", "v_i"),
    (r"\\theta(?![A-Za-z])", "theta"),
    (r"\\omega(?![A-Za-z])", "omega"),
    (r"\\(?:boldsymbol|bm)\s*(?:\{h\}|h)_i", "h_i"),
    (r"\\ell(?![A-Za-z])", "ell"),
    (r"p_\{\\mathrm\s*\{Holm\}\}", "p_Holm"),
    (r"(?<![A-Za-z])q_k(?![A-Za-z])", "q_k"),
    (r"(?<![A-Za-z])n_k(?![A-Za-z])", "n_k"),
    (r"(?<![A-Za-z])c_i(?![A-Za-z])", "c_i"),
    (r"(?<![A-Za-z])m_k(?![A-Za-z])", "m_k"),
    (r"(?<![A-Za-z])d_k(?![A-Za-z])", "d_k"),
    (r"\\tau", "tau"),
)

# Source-specific additions are restricted to cases reviewed against
# docs/05_NOTATION.md where a generic regular expression would create known
# false positives.  In particular, a broad ``N`` pattern would confuse the
# number of robots with sample size, Newtons, and continuation nodes.
SYMBOL_SOURCE_OVERRIDES: dict[str, tuple[str, ...]] = {
    "thesis/sections/frontmatter/01-summary.tex": ("N",),
    "thesis/sections/frontmatter/02-abstract.tex": ("N",),
}

# These notes preserve semantic findings that a token-only index cannot encode.
# They are copied into the manifest even when another canonical symbol in the
# same source is indexed successfully.
SYMBOL_REVIEW_NOTES: dict[str, str] = {
    "paper/sec_auditoria.tex": (
        "Revisión manual: \\delta aparece como nombre contextual de la "
        "disipatividad citada, no como símbolo propio definido por la obra."
    ),
    "paper/sec_ensayo_cierre_figs.tex": (
        "Revisión manual: el modo matemático contiene coordenadas, tiempos, "
        "porcentajes y el alcance local n; no introduce un símbolo canónico."
    ),
    "paper/sec_ensayo_cierre_interp.tex": (
        "Revisión manual: contiene cifras, p-valores y el alcance local n, "
        "sin una variable canónica inequívoca para indexar."
    ),
    "paper/sec_ensayo_cierre_plan.tex": (
        "Sobrecarga detectada: N denota nodos de la continuación, no el número "
        "canónico de robots; debe renombrarse antes de migrar a la monografía."
    ),
    "paper/sec_ensayo_cierre_resultados.tex": (
        "Revisión manual: IC95, T, E y p son abreviaturas de tabla aún no "
        "normalizadas; deben registrarse o expandirse antes de migrar."
    ),
    "paper/sec_ensayos.tex": (
        "Sobrecarga detectada: N=30 denota tamaño muestral en la comparación, "
        "mientras N está reservado al número de robots."
    ),
}


def detect_symbols(path: Path) -> str:
    if path.suffix.lower() not in {".tex", ".sty"}:
        return ""
    text = read_text(path)
    symbols = [label for pattern, label in SYMBOL_PATTERNS if re.search(pattern, text)]
    source_path = path.relative_to(REPO_ROOT).as_posix()
    symbols.extend(SYMBOL_SOURCE_OVERRIDES.get(source_path, ()))
    return ";".join(dict.fromkeys(symbols))


def generator_for(path: str, corpus: str) -> str:
    extension = Path(path).suffix.lower()
    build_extensions = {".aux", ".bbl", ".bcf", ".blg", ".lof", ".log", ".lot", ".out", ".toc", ".xml"}
    if extension in build_extensions or (extension == ".pdf" and corpus in {"paper", "thesis"}):
        return "latex-build"
    if corpus == "books":
        return "external-publication"
    if corpus == "work":
        return "author-draft-export"
    if "/generated/" in f"/{path}":
        return "repository-generator-unspecified"
    if extension in {".tex", ".sty", ".bib"}:
        return "author-latex-source"
    return "repository-file"


def provenance_for(corpus: str) -> tuple[str, str]:
    if corpus == "books":
        return "third-party academic source; private consultation only", "unknown/restricted; do not redistribute"
    if corpus == "work":
        return "author draft; not independent evidence", "author-owned; internal"
    if corpus == "paper":
        return "author technical manuscript candidate", "author-owned; repository"
    return "author VIU thesis source", "author-owned; repository"


def initial_use(path: str, corpus: str) -> str:
    extension = Path(path).suffix.lower()
    if corpus == "books":
        return "consultation-only"
    if corpus == "work":
        return "author-draft-candidate"
    if corpus == "paper":
        return "monograph-candidate" if extension == ".tex" else "archive-or-build-reference"
    if extension in {".tex", ".sty", ".bib", ".json", ".ps1", ".png", ".jpg", ".jpeg"}:
        return "VIU-format-or-content-source"
    return "archive-or-build-reference"


def evidence_status_for(corpus: str, linked_claims: Sequence[ClaimRecord]) -> str:
    if any(claim.ledger_state == "SOPORTADA" for claim in linked_claims):
        return "supported"
    if linked_claims or corpus == "thesis":
        return "pending-audit"
    return "candidate"


def evidence_status_note(status: str) -> str:
    notes = {
        "supported": (
            "Al menos un claim enlazado está SOPORTADA; el estado no valida todas "
            "las afirmaciones de una unidad mixta."
        ),
        "pending-audit": (
            "Triage estructural de archivo; cada claim conserva su estado propio en "
            "docs/04_CLAIMS_EVIDENCE.md."
        ),
        "candidate": (
            "Fuente candidata o contextual; no constituye evidencia independiente "
            "hasta completar la auditoría aplicable."
        ),
    }
    return notes[status]


def claim_traceability_for(
    row: dict[str, object],
    audits: dict[str, dict[str, dict[str, str]]],
    source_reviews: dict[str, dict[str, str]],
) -> tuple[str, str, str, str]:
    """Classify claim applicability without manufacturing semantic links."""

    path = str(row["path"])
    corpus = str(row["corpus"])
    claim_ids = [item for item in str(row["claim_ids"]).split(";") if item]
    is_canonical = row["is_canonical"] == "yes"

    if claim_ids:
        if not is_canonical:
            relation = "canonical-reference"
            reason = (
                "Los enlaces se heredan del archivo canónico; el duplicado exacto "
                "no añade evidencia."
            )
        elif corpus == "books":
            relation = "context"
            reason = (
                "La fuente se enlaza como contexto verificado; no demuestra el "
                "resultado propio del TFM."
            )
        else:
            relation = "mentions"
            reason = (
                "La unidad participa en el claim indicado; el tipo y el nivel de "
                "evidencia se resuelven en el ledger, no por el archivo completo."
            )
        locator = "docs/04_CLAIMS_EVIDENCE.md::" + ";".join(claim_ids)
        return "linked", relation, reason, locator

    if not is_canonical:
        return (
            "not-applicable",
            "none",
            "Duplicado exacto sin claim en su canónico; se conserva solo la procedencia.",
            "",
        )

    source_review = source_reviews.get(str(row["unit_id"]))
    if source_review is not None:
        reason = (
            f"Auditoría de fuente `{source_review['review_category']}`: "
            f"{source_review['rationale']} Límite: {source_review['limitation']}"
        )
        return (
            "reviewed-unlinked",
            "candidate-only",
            reason,
            source_review["evidence_locator"],
        )

    if corpus in audits:
        audit = audits[corpus][str(row["unit_id"])]
        if corpus == "books":
            context_reason = BOOK_REVIEWED_CONTEXT_ONLY.get(str(row["unit_id"]))
            if context_reason:
                return (
                    "not-applicable",
                    "none",
                    context_reason,
                    "",
                )
            if audit["decision"] != "out-of-scope":
                return (
                    "pending-semantic-review",
                    "future-required",
                    "Consulta contextual sin claim actual; cualquier enlace futuro exige verificar la fuente autorizada y el pasaje exacto.",
                    "",
                )
            return (
                "not-applicable",
                "none",
                "Fuente excluida por la auditoría bibliográfica; no respalda claims del TFM.",
                "",
            )
        if audit["destino"] == "monograph":
            return (
                "pending-semantic-review",
                "future-required",
                "Borrador del autor reservado para extracción fragmentaria; no puede adquirir un claim sin prueba, código o datos independientes.",
                "",
            )
        return (
            "not-applicable",
            "none",
            "Borrador destinado a contexto o archivo; no se usa como evidencia independiente.",
            "",
        )

    if corpus == "paper" and Path(path).suffix.lower() == ".tex":
        return (
            "pending-semantic-review",
            "future-required",
            "Cantera de monografía pendiente de auditoría por fragmento, supuestos, prueba y evidencia.",
            "",
        )
    if corpus == "thesis" and path in THESIS_REVIEWED_NON_EVIDENCE:
        return (
            "not-applicable",
            "none",
            THESIS_REVIEWED_NON_EVIDENCE[path],
            "",
        )
    return (
        "not-applicable",
        "none",
        "Unidad estructural, editorial o auxiliar sin claim propio en el uso actual.",
        "",
    )


LATEX_MATH_SIGNAL_RE = re.compile(
    r"(?<!\\)\$|\\\(|\\\[|\\begin\{(?:equation|align|gather|multline|cases|matrix)|\\ensuremath"
)


def symbol_traceability_for(row: dict[str, object]) -> tuple[str, str]:
    """State whether a blank symbol index is N/A, empty, or still pending."""

    symbols = str(row["symbols"])
    source_path = str(row["path"])
    review_note = SYMBOL_REVIEW_NOTES.get(source_path, "")
    path = REPO_ROOT / str(row["path"])
    suffix = path.suffix.lower()
    if symbols:
        note = (
            "Índice heurístico conservador; significado, dominio y unidades se validan "
            "contra docs/05_NOTATION.md."
        )
        if review_note:
            note = f"{note} {review_note}"
        return (
            "indexed",
            note,
        )
    if suffix not in {".tex", ".sty"} or suffix == ".sty":
        return (
            "not-applicable",
            "El tipo de unidad o su función de estilo queda fuera del índice semántico de notación.",
        )
    if LATEX_MATH_SIGNAL_RE.search(read_text(path)):
        if review_note:
            return (
                "reviewed-local-only",
                review_note,
            )
        return (
            "pending-semantic-review",
            "Contiene notación matemática fuera del detector conservador; requiere revisión contra docs/05_NOTATION.md.",
        )
    return (
        "none-detected",
        "Fuente LaTeX examinada sin coincidencias del vocabulario conservador ni señales de modo matemático.",
    )


def attach_traceability_metadata(
    manifest: Sequence[dict[str, object]],
    audits: dict[str, dict[str, dict[str, str]]],
    source_reviews: dict[str, dict[str, str]],
) -> None:
    for row in manifest:
        status, relation, reason, locator = claim_traceability_for(
            row, audits, source_reviews
        )
        symbol_status, symbol_note = symbol_traceability_for(row)
        row["claim_link_status"] = status
        row["claim_relation"] = relation
        row["claim_link_reason"] = reason
        row["evidence_locator"] = locator
        row["symbol_status"] = symbol_status
        row["symbol_note"] = symbol_note
        row["evidence_status_note"] = evidence_status_note(str(row["evidence_status"]))


def destination_for(path: str, corpus: str, is_canonical: bool) -> tuple[str, str, str]:
    extension = Path(path).suffix.lower()
    lowered = path.lower()
    if not is_canonical:
        return "archive-only", "exact-duplicate-reference", "Hash idéntico; se conserva solo la ruta y el enlace al canónico."
    if corpus == "books":
        return "background", "consultation-without-copy", "Fuente de terceros: consulta y verificación bibliográfica; no se copia ni se reproduce."
    if corpus == "work":
        return "monograph", "candidate-extraction", "Borrador del autor; toda afirmación requiere prueba, código o datos independientes."
    if corpus == "paper":
        if extension == ".tex":
            return "monograph", "candidate-extraction", "Cantera técnica; etiquetas, pruebas y citas requieren auditoría antes de migrar."
        return "archive-only", "build-reference", "Artefacto de compilación o respaldo; no se concatena al documento nuevo."
    if "/sections/appendices/" in f"/{lowered}":
        return "thesis-appendix", "selective-self-contained-migration", "Prueba o material reproducible candidato al anexo VIU."
    if (
        extension in {".tex", ".sty", ".bib", ".json", ".ps1", ".png", ".jpg", ".jpeg"}
        and "/build/" not in f"/{lowered}"
    ):
        return "thesis-body", "snapshot-or-selective-migration", "Base VIU autocontenida de formato, contenido o figura."
    return "archive-only", "build-reference", "Artefacto auxiliar o salida obsoleta; se regenera desde fuentes."


def load_curated_source_audits(
    manifest: Sequence[dict[str, object]],
) -> dict[str, dict[str, dict[str, str]]]:
    """Load the human-audited book/work routing without treating it as evidence."""

    manifest_by_id = {str(row["unit_id"]): row for row in manifest}
    expected_ids = {
        corpus: {
            str(row["unit_id"])
            for row in manifest
            if row["corpus"] == corpus
            and row["is_canonical"] == "yes"
            and row["media_type"] == "application/pdf"
        }
        for corpus in CURATED_SOURCE_AUDITS
    }
    audits: dict[str, dict[str, dict[str, str]]] = {}
    for corpus, path in CURATED_SOURCE_AUDITS.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing curated source audit: {path.relative_to(REPO_ROOT)}")
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        by_id = {row["unit_id"]: row for row in rows}
        if len(by_id) != len(rows):
            raise ValueError(f"Duplicate unit_id in {path.name}")
        if set(by_id) != expected_ids[corpus]:
            missing = sorted(expected_ids[corpus] - set(by_id))
            extra = sorted(set(by_id) - expected_ids[corpus])
            raise ValueError(
                f"Curated audit coverage mismatch for {corpus}: missing={missing}, extra={extra}"
            )
        for unit_id, audit in by_id.items():
            source = manifest_by_id[unit_id]
            if audit["path"] != source["path"] or audit["sha256"] != source["sha256"]:
                raise ValueError(f"Curated audit identity mismatch: {unit_id}")
        audits[corpus] = by_id
    return audits


def load_source_claim_reviews(
    manifest: Sequence[dict[str, object]],
    audits: dict[str, dict[str, dict[str, str]]],
) -> dict[str, dict[str, str]]:
    """Load source-level decisions without treating them as claim evidence."""

    if not SOURCE_CLAIM_REVIEW.is_file():
        raise FileNotFoundError(
            f"Missing source claim review: {SOURCE_CLAIM_REVIEW.relative_to(REPO_ROOT)}"
        )
    expected_ids = {
        str(row["unit_id"])
        for row in manifest
        if row["is_canonical"] == "yes"
        and not str(row["claim_ids"])
        and (
            (
                row["corpus"] == "paper"
                and Path(str(row["path"])).suffix.casefold() == ".tex"
            )
            or (
                row["corpus"] == "work"
                and audits["work"][str(row["unit_id"])]["destino"] == "monograph"
            )
        )
    }
    with SOURCE_CLAIM_REVIEW.open(
        "r", encoding="utf-8-sig", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    reviews = {row["unit_id"]: row for row in rows}
    if len(reviews) != len(rows):
        raise ValueError("Duplicate unit_id in source-claim-review.csv")
    if set(reviews) != expected_ids:
        missing = sorted(expected_ids - set(reviews))
        extra = sorted(set(reviews) - expected_ids)
        raise ValueError(
            f"Source claim review coverage mismatch: missing={missing}, extra={extra}"
        )
    manifest_by_id = {str(row["unit_id"]): row for row in manifest}
    for unit_id, review in reviews.items():
        source = manifest_by_id[unit_id]
        if (
            review["path"] != source["path"]
            or review["source_sha256"] != source["sha256"]
            or review["corpus"] != source["corpus"]
        ):
            raise ValueError(f"Source claim review identity mismatch: {unit_id}")
        if review["claim_ids"]:
            raise ValueError(f"Reviewed-unlinked source has claim IDs: {unit_id}")
        if (
            review["claim_link_status"] != "reviewed-unlinked"
            or review["claim_relation"] != "candidate-only"
            or not review["rationale"]
            or not review["limitation"]
        ):
            raise ValueError(f"Invalid source claim review decision: {unit_id}")
        expected_locator = (
            f"pre-thesis/evidence/source-claim-review.csv::{unit_id}"
        )
        if review["evidence_locator"] != expected_locator:
            raise ValueError(f"Invalid source claim review locator: {unit_id}")
    return reviews


def apply_curated_manifest_overrides(
    manifest: Sequence[dict[str, object]],
    audits: dict[str, dict[str, dict[str, str]]],
) -> None:
    """Attach audited scope and intended use while preserving conservative status."""

    by_path = {str(row["path"]): row for row in manifest}
    for row in manifest:
        corpus = str(row["corpus"])
        if corpus not in audits or row["is_canonical"] != "yes":
            continue
        audit = audits[corpus][str(row["unit_id"])]
        if corpus == "books":
            row["sp_target"] = audit["scope"]
            row["claim_ids"] = audit["claim_ids"]
            row["use"] = f"consultation-{audit['decision']}"
        else:
            if audit["claim_ids"].strip():
                raise ValueError("A work draft cannot acquire claim IDs in the thematic audit")
            row["sp_target"] = audit["sp_scope"]
            row["claim_ids"] = ""
            row["use"] = f"author-draft-{audit['decision']}"
        row["evidence_status"] = "candidate"

    for row in manifest:
        if row["is_canonical"] == "yes":
            continue
        canonical = by_path[str(row["canonical_duplicate"])]
        row["sp_target"] = canonical["sp_target"]
        row["claim_ids"] = canonical["claim_ids"]
        row["evidence_status"] = canonical["evidence_status"]
        row["use"] = "exact-duplicate-reference"


def safe_cell(value: object) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[\r\n]+", " ", text).strip()
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def write_csv(path: Path, columns: Sequence[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: safe_cell(row.get(column, "")) for column in columns})


def enumerate_source_files() -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    for corpus in CORPORA:
        root = CORPUS_ROOTS[corpus]
        for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: relative_path(item).casefold()):
            result.append((corpus, path))
    return result


def build_manifest(claims: Sequence[ClaimRecord]) -> list[dict[str, object]]:
    files = enumerate_source_files()
    base_rows: list[dict[str, object]] = []
    hash_groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    pdf_pages: dict[str, tuple[int | None, str | None]] = {}

    for corpus, path in files:
        rel = relative_path(path)
        digest = sha256_file(path)
        hash_groups[digest].append((corpus, rel))
        pages_or_section = "file"
        if path.suffix.lower() == ".pdf":
            count, error = pdf_page_count(path)
            pdf_pages[rel] = (count, error)
            pages_or_section = f"pages:{count}" if count is not None else f"pages:unknown ({error})"
        elif path.suffix.lower() == ".tex":
            pages_or_section = first_latex_section(path)

        linked_claims = claims_for_path(rel, claims)
        provenance, license_value = provenance_for(corpus)
        base_rows.append(
            {
                "unit_id": stable_unit_id(stable_unit_path(path, corpus)),
                "sha256": digest,
                "path": rel,
                "bytes": path.stat().st_size,
                "media_type": media_type(path),
                "pages_or_section": pages_or_section,
                "corpus": corpus,
                "sp_target": infer_sp_target(rel, corpus),
                "claim_ids": ";".join(claim.claim_id for claim in linked_claims),
                "symbols": detect_symbols(path),
                "evidence_status": evidence_status_for(corpus, linked_claims),
                "use": initial_use(rel, corpus),
                "generator": generator_for(rel, corpus),
                "provenance": provenance,
                "license": license_value,
            }
        )

    canonical_for_hash: dict[str, str] = {}
    for digest, members in hash_groups.items():
        canonical_for_hash[digest] = min(
            members,
            key=lambda item: (CORPUS_PRIORITY[item[0]], item[1].casefold()),
        )[1]

    for row in base_rows:
        canonical = canonical_for_hash[str(row["sha256"])]
        is_canonical = str(row["path"]) == canonical
        row["is_canonical"] = "yes" if is_canonical else "no"
        row["canonical_duplicate"] = "" if is_canonical else canonical

    audits = load_curated_source_audits(base_rows)
    apply_curated_manifest_overrides(base_rows, audits)
    source_reviews = load_source_claim_reviews(base_rows, audits)
    attach_traceability_metadata(base_rows, audits, source_reviews)

    return sorted(base_rows, key=lambda row: (CORPORA.index(str(row["corpus"])), str(row["path"]).casefold()))


def build_crosswalk(manifest: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    audits = load_curated_source_audits(manifest)
    rows: list[dict[str, object]] = []
    for item in manifest:
        is_canonical = item["is_canonical"] == "yes"
        destination, mode, rationale = destination_for(str(item["path"]), str(item["corpus"]), is_canonical)
        sp_target = str(item["sp_target"])
        claim_ids = str(item["claim_ids"])
        evidence_status = str(item["evidence_status"])
        corpus = str(item["corpus"])
        if is_canonical and corpus in audits:
            audit = audits[corpus][str(item["unit_id"])]
            if corpus == "books":
                decision = audit["decision"]
                if decision == "out-of-scope":
                    destination = "archive-only"
                    mode = "curated-exclusion"
                else:
                    destination = "background"
                    mode = "consultation-without-copy"
                rationale = f"Auditoría bibliográfica `{decision}`: {audit['rationale_limitation']}"
            else:
                destination = audit["destino"]
                if destination not in VALID_DESTINATIONS:
                    raise ValueError(f"Invalid curated work destination: {destination}")
                decision = audit["decision"]
                mode = {
                    "monograph": "candidate-extraction",
                    "background": "provenance-only",
                    "archive-only": "curated-exclusion",
                }[destination]
                rationale = f"Auditoría temática `{decision}`: {audit['racional']}"
            sp_target = str(item["sp_target"])
            claim_ids = str(item["claim_ids"])
            evidence_status = "candidate"
        canonical_path = str(item["path"]) if is_canonical else str(item["canonical_duplicate"])
        rows.append(
            {
                "unit_id": item["unit_id"],
                "path": item["path"],
                "corpus": item["corpus"],
                "sha256": item["sha256"],
                "canonical_path": canonical_path,
                "is_exact_duplicate": "no" if is_canonical else "yes",
                "destination": destination,
                "incorporation_mode": mode,
                "sp_target": sp_target,
                "claim_ids": claim_ids,
                "claim_link_status": item["claim_link_status"],
                "claim_relation": item["claim_relation"],
                "claim_link_reason": item["claim_link_reason"],
                "evidence_locator": item["evidence_locator"],
                "evidence_status": evidence_status,
                "evidence_status_note": item["evidence_status_note"],
                "rationale": rationale,
            }
        )
    return rows


def latex_line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def apply_semantic_formal_audit(
    rows: list[dict[str, object]], claims: Sequence[ClaimRecord]
) -> None:
    """Merge the completed per-result audit into the canonical inventory.

    A verdict records review completion and scope; it never promotes a claim or
    changes the evidence state by itself.
    """

    if not FORMAL_SEMANTIC_AUDIT.is_file():
        raise FileNotFoundError(
            f"Falta la auditoría semántica formal: {FORMAL_SEMANTIC_AUDIT}"
        )
    with FORMAL_SEMANTIC_AUDIT.open(
        "r", encoding="utf-8-sig", newline=""
    ) as stream:
        semantic_rows = list(csv.DictReader(stream))

    semantic_by_id: dict[str, dict[str, str]] = {}
    for audit in semantic_rows:
        result_id = audit["result_id"].strip()
        if not result_id:
            raise ValueError("Auditoría semántica formal con result_id vacío")
        if result_id in semantic_by_id:
            raise ValueError(f"result_id duplicado en auditoría semántica: {result_id}")
        semantic_by_id[result_id] = audit

    inventory_ids = {str(row["result_id"]) for row in rows}
    semantic_ids = set(semantic_by_id)
    if inventory_ids != semantic_ids:
        missing = sorted(inventory_ids - semantic_ids)
        stale = sorted(semantic_ids - inventory_ids)
        raise ValueError(
            "Cobertura formal semántica incompleta: "
            f"missing={len(missing)}, stale={len(stale)}"
        )

    claims_by_id = {claim.claim_id: claim for claim in claims}
    excluded_claim_markers = {"", "NONE", "NONE_IN_DOCS_04"}
    audited_columns = (
        "assumptions_audited",
        "domain_audited",
        "units_audited",
        "proof_audited",
        "dependencies_audited",
        "counterexample_audited",
        "evidence_link_audited",
    )
    for row in rows:
        result_id = str(row["result_id"])
        audit = semantic_by_id[result_id]
        if audit["source_path"].replace("\\", "/") != row["path"]:
            raise ValueError(f"Ruta divergente en auditoría semántica: {result_id}")
        if audit["label"].strip() != row["label"]:
            raise ValueError(f"Etiqueta divergente en auditoría semántica: {result_id}")

        verdict = audit["normalized_verdict"].strip().upper()
        if verdict not in FORMAL_AUDIT_VERDICTS:
            raise ValueError(f"Veredicto formal inválido: {result_id}:{verdict}")
        promotion_decision = re.sub(
            r"\s+", " ", audit["promotion_decision"].strip()
        )
        if not promotion_decision or promotion_decision == "auto-promote":
            raise ValueError(f"Decisión de promoción inválida: {result_id}")

        exact_claim_ids = sorted(
            {
                claim_id.strip()
                for claim_id in audit["claim_id"].split(";")
                if claim_id.strip() not in excluded_claim_markers
            }
        )
        unknown_claim_ids = [
            claim_id for claim_id in exact_claim_ids if claim_id not in claims_by_id
        ]
        if unknown_claim_ids:
            raise ValueError(
                f"Claims desconocidos en auditoría semántica {result_id}: "
                + ",".join(unknown_claim_ids)
            )

        row["linked_claim_ids"] = ";".join(exact_claim_ids)
        row["claim_ledger_states"] = ";".join(
            sorted({claims_by_id[claim_id].ledger_state for claim_id in exact_claim_ids})
        )
        row["audit_status"] = verdict
        for column in audited_columns:
            row[column] = "yes"

        rationale = re.sub(r"\s+", " ", audit["rationale"].strip())
        notes = [
            f"Auditoría semántica {verdict}: {rationale}",
            f"Decisión: {promotion_decision}.",
            "No hay promoción automática.",
        ]
        if row["duplicate_label_within_corpus"] == "yes":
            notes.append(
                "Etiqueta duplicada dentro del corpus; no migrar hasta resolverla."
            )
        row["notes"] = " ".join(notes)


def parse_formal_results(claims: Sequence[ClaimRecord]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    corpus_counts = Counter()
    for corpus in ("paper", "thesis"):
        root = CORPUS_ROOTS[corpus]
        for path in sorted(root.rglob("*.tex"), key=lambda item: relative_path(item).casefold()):
            rel = relative_path(path)
            text = read_text(path)
            source_sha256 = sha256_file(path)
            matches = list(FORMAL_BEGIN_RE.finditer(text))
            linked = claims_for_path(rel, claims)
            linked_ids = ";".join(claim.claim_id for claim in linked)
            linked_states = ";".join(sorted({claim.ledger_state for claim in linked}))
            for index, match in enumerate(matches):
                corpus_counts[corpus] += 1
                environment = match.group(1)
                title = re.sub(r"\s+", " ", (match.group(2) or "")).strip()
                end_token = f"\\end{{{environment}}}"
                end_offset = text.find(end_token, match.end())
                if end_offset < 0:
                    end_offset = match.end()
                else:
                    end_offset += len(end_token)
                next_offset = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                block = text[match.start() : end_offset]
                label_match = LABEL_RE.search(block)
                label = label_match.group(1).strip() if label_match else ""
                proof_match = PROOF_RE.search(text, end_offset, next_offset)
                proof_line = latex_line_number(text, proof_match.start()) if proof_match else ""
                line = latex_line_number(text, match.start())
                result_key = label or f"{Path(rel).stem}-L{line}"
                result_id = f"{corpus.upper()}-FR-{corpus_counts[corpus]:04d}-{result_key}"
                if corpus == "paper":
                    evidence_status = "candidate"
                    notes = "Resultado de la monografía candidata; no está promovido por coincidencia de archivo."
                else:
                    evidence_status = "pending-audit"
                    notes = "El enlace al ledger es de nivel archivo; falta correspondencia exacta resultado-afirmación-prueba."
                rows.append(
                    {
                        "result_id": result_id,
                        "corpus": corpus,
                        "path": rel,
                        "source_sha256": source_sha256,
                        "line": line,
                        "end_line": latex_line_number(text, end_offset),
                        "environment": environment,
                        "title": title,
                        "label": label,
                        "label_occurrences_within_corpus": "",
                        "duplicate_label_within_corpus": "",
                        "inline_proof_detected": "yes" if proof_match else "no",
                        "proof_line": proof_line,
                        "linked_claim_ids": linked_ids,
                        "claim_ledger_states": linked_states,
                        "evidence_status": evidence_status,
                        "audit_status": "pending-audit",
                        "assumptions_audited": "no",
                        "domain_audited": "no",
                        "units_audited": "no",
                        "proof_audited": "no",
                        "dependencies_audited": "no",
                        "counterexample_audited": "no",
                        "evidence_link_audited": "no",
                        "notes": notes,
                    }
                )
    label_counts = Counter(
        (str(row["corpus"]), str(row["label"]))
        for row in rows
        if str(row["label"])
    )
    for row in rows:
        label = str(row["label"])
        count = label_counts[(str(row["corpus"]), label)] if label else 0
        row["label_occurrences_within_corpus"] = count
        row["duplicate_label_within_corpus"] = "yes" if count > 1 else "no"
        if count > 1:
            row["notes"] = f"{row['notes']} Etiqueta duplicada dentro del corpus; no migrar hasta resolverla."
    apply_semantic_formal_audit(rows, claims)
    return rows


def style_and_config_snapshot() -> list[dict[str, object]]:
    role_paths: list[tuple[str, str]] = [
        ("thesis/main.tex", "VIU document root"),
        ("thesis/viu-mrob-thesis.sty", "VIU LaTeX style"),
        ("thesis/build.ps1", "reference build interface"),
        ("thesis/config/math-commands.tex", "canonical math commands"),
        ("thesis/config/metadata.tex", "administrative metadata"),
        ("thesis/config/protected-tikz-figures.json", "protected TikZ contract"),
        ("thesis/config/sp1-n1-frozen-pages.json", "historical frozen-page contract"),
        ("thesis/figures/protected/01-distributed-coalition-scenario.tex", "protected TikZ fig:problema"),
        ("thesis/figures/protected/02-unicycle-geometry.tex", "protected TikZ fig:robot"),
        ("thesis/sections/mainmatter/05-theoretical-framework.tex", "protected TikZ figures in theoretical framework"),
    ]
    result: list[dict[str, object]] = []
    for rel, role in role_paths:
        path = REPO_ROOT / rel
        result.append(
            {
                "path": rel,
                "role": role,
                "exists": path.is_file(),
                "bytes": path.stat().st_size if path.is_file() else None,
                "sha256": sha256_file(path) if path.is_file() else None,
            }
        )
    return result


def count_corpus_files(manifest: Sequence[dict[str, object]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for corpus in CORPORA:
        rows = [row for row in manifest if row["corpus"] == corpus]
        pdf_rows = [row for row in rows if row["media_type"] == "application/pdf"]
        output[corpus] = {
            "files": len(rows),
            "bytes": sum(int(row["bytes"]) for row in rows),
            "unique_sha256": len({str(row["sha256"]) for row in rows}),
            "pdf_files": len(pdf_rows),
            "unique_pdf_sha256": len({str(row["sha256"]) for row in pdf_rows}),
        }
    return output


def snapshot_payload(
    manifest: Sequence[dict[str, object]], formal_rows: Sequence[dict[str, object]]
) -> dict[str, object]:
    counts = count_corpus_files(manifest)
    paper_formals = sum(row["corpus"] == "paper" for row in formal_rows)
    thesis_formals = sum(row["corpus"] == "thesis" for row in formal_rows)
    duplicate_formal_labels = sorted(
        {
            (str(row["corpus"]), str(row["label"]))
            for row in formal_rows
            if row["duplicate_label_within_corpus"] == "yes"
        }
    )
    audit_columns = (
        "assumptions_audited",
        "domain_audited",
        "units_audited",
        "proof_audited",
        "dependencies_audited",
        "counterexample_audited",
        "evidence_link_audited",
    )
    formal_audit_complete = all(
        row["audit_status"] in FORMAL_AUDIT_VERDICTS
        and all(row[column] == "yes" for column in audit_columns)
        for row in formal_rows
    )
    validations = {
        "books_pdf_files_expected_42": counts["books"]["pdf_files"] == EXPECTED_PDF_COUNTS["books"],
        "books_unique_pdf_sha256_expected_37": counts["books"]["unique_pdf_sha256"] == EXPECTED_UNIQUE_PDF_COUNTS["books"],
        "work_pdf_files_expected_43": counts["work"]["pdf_files"] == EXPECTED_PDF_COUNTS["work"],
        "work_unique_pdf_sha256_expected_33": counts["work"]["unique_pdf_sha256"] == EXPECTED_UNIQUE_PDF_COUNTS["work"],
        "all_pdf_page_counts_available": all(
            not str(row["pages_or_section"]).startswith("pages:unknown")
            for row in manifest
            if row["media_type"] == "application/pdf"
        ),
        "paper_formal_results_match_planned_104": paper_formals == PLANNED_PAPER_FORMAL_COUNT,
        "formal_labels_unique_within_corpus": not duplicate_formal_labels,
        "formal_semantic_audit_complete": formal_audit_complete,
    }
    warnings: list[dict[str, object]] = []
    if paper_formals != PLANNED_PAPER_FORMAL_COUNT:
        warnings.append(
            {
                "code": "PAPER_FORMAL_COUNT_SOURCE_DRIFT",
                "planned": PLANNED_PAPER_FORMAL_COUNT,
                "observed": paper_formals,
                "handling": "Se registran todos los resultados observados; no se descarta ninguno para forzar el recuento histórico.",
            }
        )
    if duplicate_formal_labels:
        warnings.append(
            {
                "code": "DUPLICATE_FORMAL_LABELS",
                "labels": [
                    {"corpus": corpus, "label": label}
                    for corpus, label in duplicate_formal_labels
                ],
                "handling": "Las filas se conservan y se bloquea su migración hasta resolver la etiqueta duplicada.",
            }
        )
    return {
        "schema_version": 2,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "repository": {
            "root_name": REPO_ROOT.name,
            "head_commit": run_git("rev-parse", "HEAD"),
            "branch": run_git("branch", "--show-current") or None,
            "working_tree": git_status_summary(),
        },
        "scope": {
            "corpora": list(CORPORA),
            "source_roots": {
                corpus: relative_path(root) for corpus, root in CORPUS_ROOTS.items()
            },
            "copy_policy": "hash-and-index-only",
            "books_copied_to_pre_thesis": False,
        },
        "corpus_counts": counts,
        "formal_result_counts": {
            "paper_observed": paper_formals,
            "paper_planned_baseline": PLANNED_PAPER_FORMAL_COUNT,
            "thesis_observed": thesis_formals,
            "total_observed": len(formal_rows),
            "audit_status_counts": dict(
                sorted(Counter(str(row["audit_status"]) for row in formal_rows).items())
            ),
            "semantic_audit_source": relative_path(FORMAL_SEMANTIC_AUDIT),
            "definition": "teorema/proposición/lema/corolario/conjetura and English equivalents; observations and definitions excluded",
        },
        "traceability": {
            "claim_link_status_counts": dict(
                sorted(Counter(str(row["claim_link_status"]) for row in manifest).items())
            ),
            "claim_relation_counts": dict(
                sorted(Counter(str(row["claim_relation"]) for row in manifest).items())
            ),
            "symbol_status_counts": dict(
                sorted(Counter(str(row["symbol_status"]) for row in manifest).items())
            ),
            "unassigned_sp_targets": sum(
                "unassigned" in str(row["sp_target"]).split(";") for row in manifest
            ),
            "interpretation": (
                "Los estados de aplicabilidad distinguen enlaces resueltos, campos no aplicables "
                "y revisión semántica pendiente; no convierten fuentes candidatas en evidencia."
            ),
        },
        "style_config_and_protected_sources": style_and_config_snapshot(),
        "validations": validations,
        "warnings": warnings,
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build() -> None:
    claims = parse_claim_ledger()
    if not claims:
        raise RuntimeError("No se pudo analizar ninguna fila de docs/04_CLAIMS_EVIDENCE.md")
    manifest = build_manifest(claims)
    crosswalk = build_crosswalk(manifest)
    formal_rows = parse_formal_results(claims)
    write_csv(EVIDENCE_DIR / "source-manifest.csv", MANIFEST_COLUMNS, manifest)
    write_csv(EVIDENCE_DIR / "content-crosswalk.csv", CROSSWALK_COLUMNS, crosswalk)
    write_csv(EVIDENCE_DIR / "formal-results-audit.csv", FORMAL_AUDIT_COLUMNS, formal_rows)
    write_json(EVIDENCE_DIR / "source-snapshot.json", snapshot_payload(manifest, formal_rows))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def check_formula_injection(rows: Sequence[dict[str, str]], path: Path) -> list[str]:
    issues: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        for column, value in row.items():
            if value is not None and value.lstrip().startswith(("=", "+", "-", "@")):
                issues.append(f"{path.name}:{row_number}:{column}:possible-spreadsheet-formula")
    return issues


def check() -> int:
    required = {
        "source-manifest.csv": MANIFEST_COLUMNS,
        "content-crosswalk.csv": CROSSWALK_COLUMNS,
        "formal-results-audit.csv": FORMAL_AUDIT_COLUMNS,
    }
    issues: list[str] = []
    loaded: dict[str, list[dict[str, str]]] = {}
    for name, columns in required.items():
        path = EVIDENCE_DIR / name
        if not path.is_file():
            issues.append(f"missing:{name}")
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != tuple(columns):
                issues.append(f"columns:{name}")
            loaded[name] = list(reader)
        issues.extend(check_formula_injection(loaded[name], path))

    snapshot_path = EVIDENCE_DIR / "source-snapshot.json"
    if not snapshot_path.is_file():
        issues.append("missing:source-snapshot.json")
        snapshot: dict[str, object] = {}
    else:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    manifest = loaded.get("source-manifest.csv", [])
    crosswalk = loaded.get("content-crosswalk.csv", [])
    formal = loaded.get("formal-results-audit.csv", [])
    current_claims = parse_claim_ledger()
    registered_claim_ids = {claim.claim_id for claim in current_claims}
    current_files = {relative_path(path) for _, path in enumerate_source_files()}
    manifest_paths = {row["path"] for row in manifest}
    if current_files != manifest_paths:
        missing = sorted(current_files - manifest_paths)
        stale = sorted(manifest_paths - current_files)
        issues.append(f"manifest-path-set:missing={len(missing)}:stale={len(stale)}")

    for row in manifest:
        path = REPO_ROOT / row["path"]
        if path.is_file() and sha256_file(path) != row["sha256"]:
            issues.append(f"hash-mismatch:{row['path']}")
        if row["evidence_status"] not in VALID_EVIDENCE_STATUSES:
            issues.append(f"invalid-evidence-status:{row['path']}")
        if not row["evidence_status_note"]:
            issues.append(f"missing-evidence-status-note:{row['path']}")
        elif row["evidence_status"] in VALID_EVIDENCE_STATUSES and row[
            "evidence_status_note"
        ] != evidence_status_note(row["evidence_status"]):
            issues.append(f"evidence-status-note-drift:{row['path']}")
        canonical = row["path"] if row["is_canonical"] == "yes" else row["canonical_duplicate"]
        if not canonical:
            issues.append(f"missing-canonical:{row['path']}")

        sp_tokens = row["sp_target"].split(";") if row["sp_target"] else []
        if (
            not sp_tokens
            or len(sp_tokens) != len(set(sp_tokens))
            or any(token not in VALID_SP_TOKENS for token in sp_tokens)
        ):
            issues.append(f"invalid-sp-target:{row['path']}:{row['sp_target']}")

        claim_ids = row["claim_ids"].split(";") if row["claim_ids"] else []
        if len(claim_ids) != len(set(claim_ids)):
            issues.append(f"duplicate-claim-id:{row['path']}")
        for claim_id in claim_ids:
            if claim_id not in registered_claim_ids:
                issues.append(f"unknown-claim-id:{row['path']}:{claim_id}")
        if row["claim_link_status"] not in VALID_CLAIM_LINK_STATUSES:
            issues.append(f"invalid-claim-link-status:{row['path']}")
        if bool(claim_ids) != (row["claim_link_status"] == "linked"):
            issues.append(f"claim-link-status-mismatch:{row['path']}")
        if row["claim_relation"] not in VALID_CLAIM_RELATIONS:
            issues.append(f"invalid-claim-relation:{row['path']}")
        if (
            row["claim_link_status"] == "pending-semantic-review"
            and row["claim_relation"] != "future-required"
        ):
            issues.append(f"pending-claim-relation-mismatch:{row['path']}")
        elif (
            row["claim_link_status"] == "reviewed-unlinked"
            and row["claim_relation"] != "candidate-only"
        ):
            issues.append(f"reviewed-claim-relation-mismatch:{row['path']}")
        elif (
            row["claim_link_status"] == "not-applicable"
            and row["claim_relation"] != "none"
        ):
            issues.append(f"not-applicable-claim-relation-mismatch:{row['path']}")
        if not row["claim_link_reason"]:
            issues.append(f"missing-claim-link-reason:{row['path']}")
        if claim_ids:
            expected_locator = "docs/04_CLAIMS_EVIDENCE.md::" + ";".join(claim_ids)
        elif row["claim_link_status"] == "reviewed-unlinked":
            expected_locator = (
                "pre-thesis/evidence/source-claim-review.csv::" + row["unit_id"]
            )
        else:
            expected_locator = ""
        if row["evidence_locator"] != expected_locator:
            issues.append(f"evidence-locator-mismatch:{row['path']}")

        if row["symbol_status"] not in VALID_SYMBOL_STATUSES:
            issues.append(f"invalid-symbol-status:{row['path']}")
        if bool(row["symbols"]) != (row["symbol_status"] == "indexed"):
            issues.append(f"symbol-status-mismatch:{row['path']}")
        if not row["symbol_note"]:
            issues.append(f"missing-symbol-note:{row['path']}")
        if path.is_file() and row["symbols"] != detect_symbols(path):
            issues.append(f"symbol-index-drift:{row['path']}")

    manifest_by_id = {row["unit_id"]: row for row in manifest}
    manifest_by_path = {row["path"]: row for row in manifest}
    curated_audits = load_curated_source_audits(manifest) if manifest else {}
    source_reviews = (
        load_source_claim_reviews(manifest, curated_audits) if manifest else {}
    )
    for row in manifest:
        corpus = row["corpus"]
        if row["is_canonical"] == "yes":
            if corpus == "books":
                audit = curated_audits[corpus][row["unit_id"]]
                expected_claim_ids = audit["claim_ids"]
                expected_sp_target = audit["scope"]
            elif corpus == "work":
                audit = curated_audits[corpus][row["unit_id"]]
                expected_claim_ids = ""
                expected_sp_target = audit["sp_scope"]
            else:
                expected_claim_ids = ";".join(
                    claim.claim_id for claim in claims_for_path(row["path"], current_claims)
                )
                expected_sp_target = infer_sp_target(row["path"], corpus)
        else:
            canonical_row = manifest_by_path.get(row["canonical_duplicate"])
            if canonical_row is None:
                continue
            expected_claim_ids = canonical_row["claim_ids"]
            expected_sp_target = canonical_row["sp_target"]
        if row["claim_ids"] != expected_claim_ids:
            issues.append(f"claim-ledger-drift:{row['path']}")
        if row["sp_target"] != expected_sp_target:
            issues.append(f"sp-target-drift:{row['path']}")

        expected_trace = claim_traceability_for(
            row, curated_audits, source_reviews
        )
        observed_trace = (
            row["claim_link_status"],
            row["claim_relation"],
            row["claim_link_reason"],
            row["evidence_locator"],
        )
        if observed_trace != expected_trace:
            issues.append(f"claim-traceability-drift:{row['path']}")
        if (REPO_ROOT / row["path"]).is_file():
            expected_symbol_status, expected_symbol_note = symbol_traceability_for(row)
            if (row["symbol_status"], row["symbol_note"]) != (
                expected_symbol_status,
                expected_symbol_note,
            ):
                issues.append(f"symbol-traceability-drift:{row['path']}")

    if len(crosswalk) != len(manifest):
        issues.append(f"crosswalk-row-count:{len(crosswalk)}!={len(manifest)}")
    for row in crosswalk:
        if row["unit_id"] not in manifest_by_id:
            issues.append(f"orphan-crosswalk:{row['unit_id']}")
            continue
        if row["destination"] not in VALID_DESTINATIONS:
            issues.append(f"invalid-destination:{row['unit_id']}:{row['destination']}")
        if not row["destination"]:
            issues.append(f"missing-destination:{row['unit_id']}")
        manifest_row = manifest_by_id[row["unit_id"]]
        for field in (
            "path",
            "corpus",
            "sha256",
            "sp_target",
            "claim_ids",
            "claim_link_status",
            "claim_relation",
            "claim_link_reason",
            "evidence_locator",
            "evidence_status",
            "evidence_status_note",
        ):
            if row[field] != manifest_row[field]:
                issues.append(f"crosswalk-drift:{row['unit_id']}:{field}")

    counts = Counter(row["corpus"] for row in formal)
    expected_formal = [
        {column: str(row[column]) for column in FORMAL_AUDIT_COLUMNS}
        for row in parse_formal_results(current_claims)
    ]
    expected_formal_counts = Counter(row["corpus"] for row in expected_formal)
    if formal != expected_formal:
        issues.append("formal-inventory-drift")
    if counts["paper"] != expected_formal_counts["paper"]:
        issues.append("formal-count-drift:paper")
    if counts["thesis"] != expected_formal_counts["thesis"]:
        issues.append("formal-count-drift:thesis")
    for row in formal:
        if row["evidence_status"] not in VALID_EVIDENCE_STATUSES:
            issues.append(f"invalid-formal-evidence-status:{row['result_id']}")
        if row["audit_status"] not in FORMAL_AUDIT_VERDICTS:
            issues.append(f"invalid-formal-audit-status:{row['result_id']}")
        for column in (
            "assumptions_audited",
            "domain_audited",
            "units_audited",
            "proof_audited",
            "dependencies_audited",
            "counterexample_audited",
            "evidence_link_audited",
        ):
            if row[column] != "yes":
                issues.append(f"incomplete-formal-audit:{row['result_id']}:{column}")

    pdf_rows = [row for row in manifest if row["media_type"] == "application/pdf"]
    pdf_counts = Counter(row["corpus"] for row in pdf_rows)
    unique_pdf_counts = {
        corpus: len({row["sha256"] for row in pdf_rows if row["corpus"] == corpus})
        for corpus in ("books", "work")
    }
    for corpus, expected in EXPECTED_PDF_COUNTS.items():
        if pdf_counts[corpus] != expected:
            issues.append(f"pdf-count:{corpus}:{pdf_counts[corpus]}!={expected}")
    for corpus, expected in EXPECTED_UNIQUE_PDF_COUNTS.items():
        if unique_pdf_counts[corpus] != expected:
            issues.append(f"unique-pdf-count:{corpus}:{unique_pdf_counts[corpus]}!={expected}")

    if any(
        row["corpus"] == "books"
        and not row["path"].startswith("material/books/")
        for row in manifest
    ):
        issues.append("unexpected-books-source-root")

    observed_head = str(snapshot.get("repository", {}).get("head_commit", "")) if isinstance(snapshot.get("repository"), dict) else ""
    current_head = run_git("rev-parse", "HEAD")
    if observed_head != current_head:
        issues.append(f"snapshot-head-drift:{observed_head}!={current_head}")

    if issues:
        print("INVENTORY CHECK FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("INVENTORY CHECK PASSED")
    print(f"manifest_rows={len(manifest)}")
    print(f"crosswalk_rows={len(crosswalk)}")
    print(f"books_pdf={pdf_counts['books']} unique={unique_pdf_counts['books']}")
    print(f"work_pdf={pdf_counts['work']} unique={unique_pdf_counts['work']}")
    print(f"formal_results_paper={counts['paper']} thesis={counts['thesis']} total={len(formal)}")
    print(f"paper_formal_plan_baseline={PLANNED_PAPER_FORMAL_COUNT} source_drift={counts['paper'] != PLANNED_PAPER_FORMAL_COUNT}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate generated inventory against current source files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        return check()
    build()
    return check()


if __name__ == "__main__":
    sys.exit(main())
