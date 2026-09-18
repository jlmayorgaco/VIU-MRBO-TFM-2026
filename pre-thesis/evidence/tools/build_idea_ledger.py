#!/usr/bin/env python3
"""Index machine-identifiable ideas without promoting them as evidence.

The source manifest is deliberately file-level.  This companion ledger records
document titles, PDF bookmarks, fallback heading candidates, LaTeX headings,
labeled observations/figures/tables/equations and formal-result declarations.
A row is an editorial unit, not an assertion that the underlying statement is
correct or unique. Similar normalized titles are flagged only as review
candidates; they are never silently merged.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "pre-thesis" / "evidence"
MANIFEST_PATH = EVIDENCE_DIR / "source-manifest.csv"
CROSSWALK_PATH = EVIDENCE_DIR / "content-crosswalk.csv"
FORMAL_PATH = EVIDENCE_DIR / "formal-results-audit.csv"
LABELED_REVIEW_PATH = EVIDENCE_DIR / "labeled-unit-review-decisions.json"
LEDGER_PATH = EVIDENCE_DIR / "idea-ledger.csv"
SUMMARY_PATH = EVIDENCE_DIR / "idea-ledger-summary.json"
CLAIMS_PATH = REPO_ROOT / "docs" / "04_CLAIMS_EVIDENCE.md"

LEDGER_COLUMNS = (
    "idea_id",
    "source_unit_id",
    "corpus",
    "path",
    "source_sha256",
    "kind",
    "locator",
    "depth",
    "title",
    "normalized_title",
    "title_overlap_group",
    "title_overlap_status",
    "sp_target",
    "claim_ids",
    "claim_relation",
    "evidence_status",
    "destination",
    "incorporation_mode",
    "formal_context_result_ids",
    "formal_context_verdicts",
    "formal_context_claim_ids",
    "formal_context_status",
    "semantic_review_status",
    "rationale",
)

LATEX_HEADING_RE = re.compile(
    r"\\(chapter|section|subsection|subsubsection)\*?\{([^\n{}]*(?:\{[^\n{}]*\}[^\n{}]*)*)\}",
    re.MULTILINE,
)
LATEX_LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
LATEX_SEMANTIC_ENVIRONMENTS = {
    "latex-observation": (("observacion", "observation"), "obs:"),
    "latex-figure": (("figure", "figure*"), "fig:"),
    "latex-table": (("table", "table*"), "tab:"),
    "latex-equation": (
        (
            "equation",
            "equation*",
            "align",
            "align*",
            "gather",
            "gather*",
            "multline",
            "multline*",
        ),
        "eq:",
    ),
}
NUMBERED_HEADING_RE = re.compile(
    r"^(?:(?:\d+(?:\.\d+){0,5})|(?:[IVXLCDM]{1,8}))[.)]?\s+\S",
    re.IGNORECASE,
)
NAMED_HEADING_RE = re.compile(
    r"^(?:cap[ií]tulo|parte|ap[eé]ndice|anexo|secci[oó]n|section|chapter|part)\b",
    re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def safe_cell(value: object) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[\r\n]+", " ", text).strip()
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=LEDGER_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: safe_cell(row.get(key, "")) for key in LEDGER_COLUMNS})


def clean_text(value: object) -> str:
    text = str(value or "").replace("\ufffd", "?")
    text = re.sub(r"\\(?:textbf|emph|textit|texorpdfstring)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", "").replace("}", "").replace("~", " ")
    return re.sub(r"\s+", " ", text).strip(" \t.-")


def extract_braced_command(text: str, command: str) -> str:
    """Return the first balanced braced argument of a LaTeX command."""

    command_re = re.compile(
        rf"\\{re.escape(command)}(?:\s*\[[^\]]*\])?\s*\{{"
    )
    match = command_re.search(text)
    if match is None:
        return ""
    opening = match.end() - 1
    depth = 0
    for index in range(opening, len(text)):
        character = text[index]
        if character == "{" and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif character == "}" and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return text[opening + 1 : index]
    return ""


def latex_semantic_units(text: str) -> list[dict[str, object]]:
    """Locate labeled non-formal LaTeX units without judging their validity."""

    nouns = {
        "latex-observation": "Observación",
        "latex-figure": "Figura",
        "latex-table": "Tabla",
        "latex-equation": "Ecuación",
    }
    units: list[dict[str, object]] = []
    seen: set[tuple[str, str, int]] = set()
    for kind, (environments, label_prefix) in LATEX_SEMANTIC_ENVIRONMENTS.items():
        for environment in environments:
            pattern = re.compile(
                rf"\\begin\{{{re.escape(environment)}\}}"
                r"\s*(?:\[([^\]]*)\])?"
                rf"(.*?)\\end\{{{re.escape(environment)}\}}",
                re.DOTALL,
            )
            for environment_match in pattern.finditer(text):
                option = environment_match.group(1) or ""
                body = environment_match.group(2)
                caption = extract_braced_command(body, "caption")
                for label_match in LATEX_LABEL_RE.finditer(body):
                    label = label_match.group(1).strip()
                    if not label.startswith(label_prefix):
                        continue
                    offset = environment_match.start(2) + label_match.start()
                    line = text.count("\n", 0, offset) + 1
                    key = (kind, label, line)
                    if key in seen:
                        continue
                    seen.add(key)
                    raw_title = option if kind == "latex-observation" else caption
                    title = clean_text(raw_title) or f"{nouns[kind]} {label}"
                    units.append(
                        {
                            "kind": kind,
                            "label": label,
                            "line": line,
                            "title": title,
                        }
                    )
    return sorted(
        units,
        key=lambda item: (int(item["line"]), str(item["kind"]), str(item["label"])),
    )


def normalized_title(title: str) -> str:
    value = unicodedata.normalize("NFKD", clean_text(title)).casefold()
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def stable_id(*parts: object) -> str:
    payload = "\x1f".join(str(part) for part in parts)
    return "IDEA-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def infer_sp(title: str, inherited: str) -> str:
    value = normalized_title(title)
    patterns = (
        ("SP1", ("coalicion", "reclut", "asignacion", "allocation", "cuota", "population game", "nash")),
        ("SP2", ("cargo", "caging", "contact", "wrench", "transporte", "transport", "fuerza", "robot", "control")),
        ("SP3", ("trafico", "traffic", "ruta", "routing", "pasillo", "congestion", "topologia", "comunicacion", "network")),
    )
    matches = [sp for sp, tokens in patterns if any(token in value for token in tokens)]
    if len(matches) == 1:
        return matches[0]
    return inherited if inherited and inherited != "unassigned" else "transversal"


def destination_status(destination: str, corpus: str) -> tuple[str, str]:
    if destination == "archive-only":
        return "archive-only", "La unidad fuente se conserva solo por trazabilidad."
    if destination == "background":
        return "consultation-indexed", "Tema de consulta; requiere cita primaria verificada antes de respaldar una afirmación."
    if corpus == "thesis":
        return "incorporated-source", "Unidad de la fuente VIU; el claim exacto se gobierna por el ledger de evidencia."
    return "pending-semantic-review", "Idea candidata; no se promueve por aparecer en un borrador o marcador."


def row_for(
    source: dict[str, str],
    crosswalk: dict[str, str],
    *,
    kind: str,
    locator: str,
    depth: int,
    title: str,
    rationale: str = "",
) -> dict[str, object]:
    review_status, default_rationale = destination_status(crosswalk["destination"], source["corpus"])
    cleaned = clean_text(title) or Path(source["path"]).stem
    return {
        "idea_id": stable_id(source["path"], kind, locator, cleaned),
        "source_unit_id": source["unit_id"],
        "corpus": source["corpus"],
        "path": source["path"],
        "source_sha256": source["sha256"],
        "kind": kind,
        "locator": locator,
        "depth": depth,
        "title": cleaned,
        "normalized_title": normalized_title(cleaned),
        "sp_target": infer_sp(cleaned, crosswalk["sp_target"]),
        "claim_ids": crosswalk["claim_ids"],
        "claim_relation": crosswalk.get("claim_relation", ""),
        "evidence_status": crosswalk["evidence_status"],
        "destination": crosswalk["destination"],
        "incorporation_mode": crosswalk["incorporation_mode"],
        "semantic_review_status": review_status,
        "rationale": rationale or default_rationale,
    }


def pdf_title(reader: PdfReader, path: Path) -> str:
    metadata = reader.metadata or {}
    return clean_text(metadata.get("/Title")) or path.stem


def flatten_outline(reader: PdfReader, items: Sequence[Any], depth: int = 0) -> list[tuple[int, int | None, str]]:
    output: list[tuple[int, int | None, str]] = []
    for item in items:
        if isinstance(item, list):
            output.extend(flatten_outline(reader, item, depth + 1))
            continue
        title = clean_text(getattr(item, "title", None) or (item.get("/Title") if hasattr(item, "get") else item))
        if not title:
            continue
        try:
            page = int(reader.get_destination_page_number(item)) + 1
        except Exception:
            page = None
        output.append((depth, page, title))
    return output


def heading_candidate(line: str) -> bool:
    value = clean_text(line)
    if not 4 <= len(value) <= 180 or len(value.split()) > 22:
        return False
    letters = [character for character in value if character.isalpha()]
    uppercase = bool(letters) and sum(character.isupper() for character in letters) / len(letters) >= 0.88
    return bool(NUMBERED_HEADING_RE.match(value) or NAMED_HEADING_RE.match(value) or (uppercase and len(letters) >= 6))


def fallback_pdf_headings(reader: PdfReader) -> list[tuple[int, int, str]]:
    output: list[tuple[int, int, str]] = []
    seen: set[tuple[int, str]] = set()
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            continue
        ordinal = 0
        for raw_line in text.splitlines():
            title = clean_text(raw_line)
            signature = normalized_title(title)
            if not signature or not heading_candidate(title) or (page_number, signature) in seen:
                continue
            seen.add((page_number, signature))
            ordinal += 1
            output.append((page_number, ordinal, title))
    return output


def pdf_rows(source: dict[str, str], crosswalk: dict[str, str]) -> list[dict[str, object]]:
    path = REPO_ROOT / source["path"]
    reader = PdfReader(path, strict=False)
    rows = [row_for(source, crosswalk, kind="document", locator="document", depth=0, title=pdf_title(reader, path))]
    outline = flatten_outline(reader, reader.outline)
    if outline:
        for ordinal, (depth, page, title) in enumerate(outline, start=1):
            locator = f"bookmark:{ordinal}:page:{page if page is not None else 'unknown'}"
            rows.append(row_for(source, crosswalk, kind="pdf-bookmark", locator=locator, depth=depth, title=title))
    else:
        for page, ordinal, title in fallback_pdf_headings(reader):
            rows.append(
                row_for(
                    source,
                    crosswalk,
                    kind="pdf-heading-candidate",
                    locator=f"page:{page}:heading:{ordinal}",
                    depth=0,
                    title=title,
                    rationale="Encabezado inferido porque el PDF no tiene marcadores; requiere revisión manual.",
                )
            )
    return rows


def latex_rows(source: dict[str, str], crosswalk: dict[str, str]) -> list[dict[str, object]]:
    path = REPO_ROOT / source["path"]
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = [row_for(source, crosswalk, kind="document", locator="document", depth=0, title=path.stem)]
    depths = {"chapter": 0, "section": 1, "subsection": 2, "subsubsection": 3}
    for ordinal, match in enumerate(LATEX_HEADING_RE.finditer(text), start=1):
        line = text.count("\n", 0, match.start()) + 1
        command, title = match.groups()
        rows.append(
            row_for(
                source,
                crosswalk,
                kind="latex-heading",
                locator=f"line:{line}:heading:{ordinal}",
                depth=depths[command],
                title=title,
            )
        )
    rationale_by_kind = {
        "latex-observation": (
            "Observación etiquetada del borrador; requiere contraste con prueba, "
            "código o datos antes de respaldar un claim."
        ),
        "latex-figure": (
            "Figura etiquetada; su pie localiza una idea visual, pero no constituye "
            "evidencia independiente."
        ),
        "latex-table": (
            "Tabla etiquetada; su contenido requiere verificar fuentes o datos antes "
            "de usarlo como evidencia."
        ),
        "latex-equation": (
            "Ecuación etiquetada; el registro no valida sus supuestos, unidades ni "
            "derivación."
        ),
    }
    for unit in latex_semantic_units(text):
        item = row_for(
            source,
            crosswalk,
            kind=str(unit["kind"]),
            locator=f"line:{unit['line']}:label:{unit['label']}",
            depth=4,
            title=str(unit["title"]),
            rationale=rationale_by_kind[str(unit["kind"])],
        )
        # A file-level mapping cannot validate a specific caption, observation,
        # table or equation.  Preserve its destination and provenance, but force
        # an explicit semantic review before any row-level claim association.
        item["claim_ids"] = ""
        item["claim_relation"] = ""
        item["evidence_status"] = "candidate"
        item["semantic_review_status"] = "pending-semantic-review"
        rows.append(item)
    return rows


def apply_title_overlap(rows: list[dict[str, object]]) -> None:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        signature = str(row["normalized_title"])
        if len(signature) >= 8 and row["kind"] != "document":
            groups[signature].append(row)
    for signature, members in groups.items():
        paths = {str(member["path"]) for member in members}
        group = "TITLE-" + hashlib.sha256(signature.encode("utf-8")).hexdigest()[:12]
        for member in members:
            member["title_overlap_group"] = group
            member["title_overlap_status"] = "candidate-cross-source-overlap" if len(paths) > 1 else "repeated-within-source"
    for row in rows:
        row.setdefault("title_overlap_group", "")
        row.setdefault("title_overlap_status", "unique-title")


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def claim_ledger_ids() -> set[str]:
    ids: set[str] = set()
    for line in CLAIMS_PATH.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\|\s*([^|]+?)\s*\|", line)
        if match is None:
            continue
        value = match.group(1).strip()
        if value.startswith("C") and " " not in value:
            ids.add(value)
    return ids


def load_labeled_review_decisions() -> dict[str, dict[str, object]]:
    payload = json.loads(LABELED_REVIEW_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported labeled-unit review schema")
    bindings = payload.get("source_bindings")
    decisions = payload.get("decisions")
    if not isinstance(bindings, list) or not isinstance(decisions, list):
        raise ValueError("labeled-unit review must define source_bindings and decisions")
    binding_hashes: dict[str, str] = {}
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError("invalid labeled-unit source binding")
        path = str(binding.get("path", ""))
        source_sha256 = str(binding.get("source_sha256", ""))
        if not path or not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
            raise ValueError("invalid labeled-unit source path or SHA-256")
        if path in binding_hashes:
            raise ValueError(f"duplicate labeled-unit source binding: {path}")
        binding_hashes[path] = source_sha256

    allowed_destinations = {
        "thesis-body",
        "thesis-appendix",
        "monograph",
        "background",
        "archive-only",
    }
    known_claims = claim_ledger_ids()
    by_id: dict[str, dict[str, object]] = {}
    required = {
        "idea_id",
        "path",
        "locator",
        "claim_ids",
        "claim_relation",
        "evidence_status",
        "destination",
        "incorporation_mode",
        "semantic_review_status",
        "rationale",
    }
    for decision in decisions:
        if not isinstance(decision, dict) or not required.issubset(decision):
            raise ValueError("incomplete labeled-unit review decision")
        idea_id = str(decision["idea_id"])
        path = str(decision["path"])
        claims = decision["claim_ids"]
        if idea_id in by_id:
            raise ValueError(f"duplicate labeled-unit decision: {idea_id}")
        if path not in binding_hashes:
            raise ValueError(f"decision lacks source binding: {idea_id}")
        if not isinstance(claims, list) or not claims:
            raise ValueError(f"decision must name at least one claim: {idea_id}")
        unknown_claims = sorted(set(str(item) for item in claims) - known_claims)
        if unknown_claims:
            raise ValueError(
                f"decision references unknown claims: {idea_id}:{','.join(unknown_claims)}"
            )
        if str(decision["destination"]) not in allowed_destinations:
            raise ValueError(f"invalid decision destination: {idea_id}")
        for key in (
            "claim_relation",
            "evidence_status",
            "incorporation_mode",
            "semantic_review_status",
            "rationale",
        ):
            if not str(decision[key]).strip():
                raise ValueError(f"blank {key} in labeled-unit decision: {idea_id}")
        normalized = dict(decision)
        normalized["source_sha256"] = binding_hashes[path]
        normalized["claim_ids"] = sorted(set(str(item) for item in claims))
        by_id[idea_id] = normalized
    return by_id


def apply_labeled_unit_reviews(rows: list[dict[str, object]]) -> None:
    decisions = load_labeled_review_decisions()
    rows_by_id = {str(row["idea_id"]): row for row in rows}
    missing = sorted(set(decisions) - set(rows_by_id))
    if missing:
        raise ValueError(f"labeled-unit decisions reference missing rows: {missing}")
    for idea_id, decision in decisions.items():
        row = rows_by_id[idea_id]
        if str(row["kind"]) not in LATEX_SEMANTIC_ENVIRONMENTS:
            raise ValueError(f"decision does not reference a labeled unit: {idea_id}")
        if row["formal_context_status"] != "outside-formal-result":
            raise ValueError(f"decision overlaps an audited formal result: {idea_id}")
        for key in ("path", "source_sha256", "locator"):
            if str(row[key]) != str(decision[key]):
                raise ValueError(f"stale labeled-unit decision binding: {idea_id}:{key}")
        row["claim_ids"] = ";".join(decision["claim_ids"])
        for key in (
            "claim_relation",
            "evidence_status",
            "destination",
            "incorporation_mode",
            "semantic_review_status",
            "rationale",
        ):
            row[key] = str(decision[key])


def apply_formal_context(
    rows: list[dict[str, object]], formal_rows: Sequence[dict[str, str]]
) -> None:
    """Bind labeled LaTeX apparatus to an enclosing audited formal result.

    Containment is exact and deliberately narrow: a label inherits the audit
    context only when its source line lies inside the recorded formal-result
    environment.  The row-level ``claim_ids`` field remains untouched because
    context is not evidence promotion.
    """

    by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for formal in formal_rows:
        by_path[formal["path"]].append(formal)

    for row in rows:
        row["formal_context_result_ids"] = ""
        row["formal_context_verdicts"] = ""
        row["formal_context_claim_ids"] = ""
        row["formal_context_status"] = "not-applicable"
        if str(row["kind"]) not in LATEX_SEMANTIC_ENVIRONMENTS:
            continue
        locator_match = re.match(r"line:(\d+):label:", str(row["locator"]))
        if locator_match is None:
            raise ValueError(f"invalid labeled-unit locator: {row['locator']}")
        line = int(locator_match.group(1))
        matches = [
            formal
            for formal in by_path.get(str(row["path"]), [])
            if int(formal["line"]) <= line <= int(formal["end_line"])
        ]
        if len(matches) > 1:
            raise ValueError(
                "labeled unit lies in overlapping formal results: "
                f"{row['path']}:{row['locator']}"
            )
        if not matches:
            row["formal_context_status"] = "outside-formal-result"
            continue
        match = matches[0]
        verdict = match["audit_status"]
        claims = sorted(set(split_ids(match["linked_claim_ids"])))
        row["formal_context_result_ids"] = match["result_id"]
        row["formal_context_verdicts"] = verdict
        row["formal_context_claim_ids"] = ";".join(claims)
        row["formal_context_status"] = "within-audited-formal-result"
        row["semantic_review_status"] = f"formal-context-{verdict.casefold()}"
        row["rationale"] = (
            f"El localizador cae dentro de {match['result_id']}, auditado como "
            f"{verdict}. Este contexto no convierte el elemento en evidencia ni "
            "le asigna por sí mismo un claim."
        )


def build_rows() -> list[dict[str, object]]:
    manifest = read_csv(MANIFEST_PATH)
    crosswalk = {row["unit_id"]: row for row in read_csv(CROSSWALK_PATH)}
    formal_rows = read_csv(FORMAL_PATH)
    rows: list[dict[str, object]] = []
    for source in manifest:
        if source["is_canonical"] != "yes" or source["unit_id"] not in crosswalk:
            continue
        suffix = Path(source["path"]).suffix.casefold()
        if suffix == ".pdf" and source["corpus"] in {"books", "work"}:
            rows.extend(pdf_rows(source, crosswalk[source["unit_id"]]))
        elif suffix == ".tex" and source["corpus"] in {"paper", "thesis"}:
            rows.extend(latex_rows(source, crosswalk[source["unit_id"]]))

    sources_by_path = {row["path"]: row for row in manifest if row["is_canonical"] == "yes"}
    for formal in formal_rows:
        source = sources_by_path.get(formal["path"])
        if source is None or source["unit_id"] not in crosswalk:
            continue
        title = formal["title"] or formal["label"] or formal["result_id"]
        item = row_for(
            source,
            crosswalk[source["unit_id"]],
            kind="formal-result",
            locator=f"{formal['result_id']}:lines:{formal['line']}-{formal['end_line']}",
            depth=4,
            title=title,
            rationale=(
                f"Resultado formal auditado: {formal['audit_status']}. La clasificación "
                "no se promueve automáticamente; consulte formal-results-audit.csv."
            ),
        )
        item["claim_ids"] = formal["linked_claim_ids"]
        item["claim_relation"] = (
            "audited-formal-result" if formal["linked_claim_ids"] else ""
        )
        item["semantic_review_status"] = f"formal-{formal['audit_status'].casefold()}"
        rows.append(item)

    rows.sort(key=lambda row: (str(row["corpus"]), str(row["path"]).casefold(), str(row["locator"])))
    apply_formal_context(rows, formal_rows)
    apply_labeled_unit_reviews(rows)
    apply_title_overlap(rows)
    return rows


def summary(rows: Sequence[dict[str, object]]) -> dict[str, object]:
    labeled = [
        row for row in rows if str(row["kind"]) in LATEX_SEMANTIC_ENVIRONMENTS
    ]
    formal_context = [
        row
        for row in labeled
        if row["formal_context_status"] == "within-audited-formal-result"
    ]
    reviewed = [
        row
        for row in labeled
        if str(row["semantic_review_status"]).startswith("reviewed-")
    ]
    pending = [
        row
        for row in labeled
        if row["semantic_review_status"] == "pending-semantic-review"
    ]
    return {
        "schema_version": 4,
        "definition": "Machine-identifiable editorial units; no automatic evidence promotion or semantic deduplication.",
        "row_count": len(rows),
        "source_count": len({str(row["source_unit_id"]) for row in rows}),
        "by_corpus": dict(sorted(Counter(str(row["corpus"]) for row in rows).items())),
        "by_kind": dict(sorted(Counter(str(row["kind"]) for row in rows).items())),
        "by_destination": dict(sorted(Counter(str(row["destination"]) for row in rows).items())),
        "by_review_status": dict(sorted(Counter(str(row["semantic_review_status"]) for row in rows).items())),
        "labeled_unit_count": len(labeled),
        "labeled_formal_context_count": len(formal_context),
        "labeled_outside_formal_count": len(labeled) - len(formal_context),
        "labeled_reviewed_count": len(reviewed),
        "labeled_pending_count": len(pending),
        "labeled_reviewed_by_relation": dict(
            sorted(Counter(str(row["claim_relation"]) for row in reviewed).items())
        ),
        "labeled_reviewed_by_status": dict(
            sorted(Counter(str(row["semantic_review_status"]) for row in reviewed).items())
        ),
        "labeled_formal_context_by_verdict": dict(
            sorted(Counter(str(row["formal_context_verdicts"]) for row in formal_context).items())
        ),
        "title_overlap_rows": sum(str(row["title_overlap_status"]) != "unique-title" for row in rows),
        "limitations": [
            "PDF bookmarks and heading heuristics register candidates, not truth claims.",
            "Labeled observations, captions, tables, and equations are editorial locators, not validated claims.",
            "Formal context is inherited only by exact source-line containment; proof-adjacent labels outside the formal environment require an explicit hash-bound fragment decision.",
            "Normalized-title overlap is a review signal, not proof of semantic duplication.",
            "Only hash-bound fragment decisions may populate row-level claim IDs; definitions, limitations, protocols, context and evidence summaries remain distinct roles.",
            "Blank claim IDs identify non-supporting or unadjudicated heuristic rows and cannot support conclusions.",
        ],
    }


def render_csv(rows: Sequence[dict[str, object]]) -> bytes:
    import io

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=LEDGER_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: safe_cell(row.get(key, "")) for key in LEDGER_COLUMNS})
    return b"\xef\xbb\xbf" + stream.getvalue().encode("utf-8")


def quick_index_check() -> int:
    """Validate the frozen ledger against the already hash-checked manifest.

    This deliberately avoids reopening thousands of PDF pages.  A full
    ``--check`` remains available when the extracted titles themselves must be
    reproduced byte for byte.
    """

    if not LEDGER_PATH.is_file() or not SUMMARY_PATH.is_file():
        print("IDEA LEDGER INDEX CHECK FAILED\n- generated ledger artifacts are missing")
        return 1
    rows = read_csv(LEDGER_PATH)
    manifest = read_csv(MANIFEST_PATH)
    formal = read_csv(FORMAL_PATH)
    labeled_decisions = load_labeled_review_decisions()
    summary_payload = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    manifest_by_id = {row["unit_id"]: row for row in manifest}
    issues: list[str] = []
    if rows and set(rows[0]) != set(LEDGER_COLUMNS):
        issues.append("ledger columns differ from the current schema")
    if len(rows) != int(summary_payload.get("row_count", -1)):
        issues.append("row count differs from summary")
    if len({row["idea_id"] for row in rows}) != len(rows):
        issues.append("duplicate idea_id")
    for row in rows:
        source = manifest_by_id.get(row["source_unit_id"])
        if source is None:
            issues.append(f"orphan source_unit_id:{row['source_unit_id']}")
            continue
        if row["path"] != source["path"] or row["source_sha256"] != source["sha256"]:
            issues.append(f"source binding mismatch:{row['idea_id']}")
    expected_documents = {
        row["unit_id"]
        for row in manifest
        if row["is_canonical"] == "yes"
        and (
            (row["media_type"] == "application/pdf" and row["corpus"] in {"books", "work"})
            or (Path(row["path"]).suffix.casefold() == ".tex" and row["corpus"] in {"paper", "thesis"})
        )
    }
    observed_documents = {
        row["source_unit_id"] for row in rows if row["kind"] == "document"
    }
    if expected_documents != observed_documents:
        issues.append(
            "document source coverage differs:"
            f"missing={len(expected_documents - observed_documents)}:"
            f"stale={len(observed_documents - expected_documents)}"
        )
    expected_formals = {row["result_id"] for row in formal}
    observed_formals = {
        row["locator"].split(":lines:", 1)[0]
        for row in rows
        if row["kind"] == "formal-result"
    }
    if expected_formals != observed_formals:
        issues.append(
            "formal result coverage differs:"
            f"missing={len(expected_formals - observed_formals)}:"
            f"stale={len(observed_formals - expected_formals)}"
        )
    canonical_latex_paths = {
        row["path"]
        for row in manifest
        if row["is_canonical"] == "yes"
        and row["corpus"] in {"paper", "thesis"}
        and Path(row["path"]).suffix.casefold() == ".tex"
    }
    expected_labeled_units: set[tuple[str, str, str]] = set()
    for path in canonical_latex_paths:
        text = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        expected_labeled_units.update(
            (path, str(unit["kind"]), f"line:{unit['line']}:label:{unit['label']}")
            for unit in latex_semantic_units(text)
        )
    observed_labeled_units = {
        (row["path"], row["kind"], row["locator"])
        for row in rows
        if row["kind"] in LATEX_SEMANTIC_ENVIRONMENTS
    }
    if expected_labeled_units != observed_labeled_units:
        issues.append(
            "labeled LaTeX coverage differs:"
            f"missing={len(expected_labeled_units - observed_labeled_units)}:"
            f"stale={len(observed_labeled_units - expected_labeled_units)}"
        )
    formal_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for formal_row in formal:
        formal_by_path[formal_row["path"]].append(formal_row)
    formal_context_count = 0
    formal_context_verdicts: Counter[str] = Counter()
    for row in rows:
        if row["kind"] not in LATEX_SEMANTIC_ENVIRONMENTS:
            if (
                row.get("formal_context_status") != "not-applicable"
                or row.get("formal_context_result_ids")
                or row.get("formal_context_verdicts")
                or row.get("formal_context_claim_ids")
            ):
                issues.append(f"invalid non-labeled formal context:{row['idea_id']}")
            continue
        locator_match = re.match(r"line:(\d+):label:", row["locator"])
        if locator_match is None:
            issues.append(f"invalid labeled locator:{row['idea_id']}")
            continue
        line = int(locator_match.group(1))
        matches = [
            formal_row
            for formal_row in formal_by_path.get(row["path"], [])
            if int(formal_row["line"]) <= line <= int(formal_row["end_line"])
        ]
        if len(matches) > 1:
            issues.append(f"overlapping formal context:{row['idea_id']}")
            continue
        if not matches:
            if (
                row.get("formal_context_status") != "outside-formal-result"
                or row.get("formal_context_result_ids")
                or row.get("formal_context_verdicts")
                or row.get("formal_context_claim_ids")
            ):
                issues.append(f"stale outside-formal context:{row['idea_id']}")
                continue
            decision = labeled_decisions.get(row["idea_id"])
            if decision is None:
                if (
                    row.get("claim_ids")
                    or row.get("claim_relation")
                    or row.get("evidence_status") != "candidate"
                    or row.get("semantic_review_status")
                    != "pending-semantic-review"
                ):
                    issues.append(f"unreviewed labeled unit was promoted:{row['idea_id']}")
                continue
            expected_fields = {
                "path": decision["path"],
                "source_sha256": decision["source_sha256"],
                "locator": decision["locator"],
                "claim_ids": ";".join(decision["claim_ids"]),
                "claim_relation": decision["claim_relation"],
                "evidence_status": decision["evidence_status"],
                "destination": decision["destination"],
                "incorporation_mode": decision["incorporation_mode"],
                "semantic_review_status": decision["semantic_review_status"],
                "rationale": decision["rationale"],
            }
            if any(str(row.get(key, "")) != str(value) for key, value in expected_fields.items()):
                issues.append(f"stale labeled-unit review:{row['idea_id']}")
            continue
        formal_row = matches[0]
        expected_claims = ";".join(
            sorted(set(split_ids(formal_row["linked_claim_ids"])))
        )
        expected_semantic_status = (
            f"formal-context-{formal_row['audit_status'].casefold()}"
        )
        if (
            row.get("formal_context_status") != "within-audited-formal-result"
            or row.get("formal_context_result_ids") != formal_row["result_id"]
            or row.get("formal_context_verdicts") != formal_row["audit_status"]
            or row.get("formal_context_claim_ids") != expected_claims
            or row.get("semantic_review_status") != expected_semantic_status
            or row.get("claim_ids")
            or row.get("claim_relation")
            or row["idea_id"] in labeled_decisions
        ):
            issues.append(f"stale audited formal context:{row['idea_id']}")
            continue
        formal_context_count += 1
        formal_context_verdicts[formal_row["audit_status"]] += 1
    expected_formal_context_verdicts = {
        key: value for key, value in sorted(formal_context_verdicts.items())
    }
    if formal_context_count != summary_payload.get("labeled_formal_context_count"):
        issues.append("labeled formal-context count differs from summary")
    if expected_formal_context_verdicts != summary_payload.get(
        "labeled_formal_context_by_verdict"
    ):
        issues.append("labeled formal-context verdicts differ from summary")
    reviewed_rows = [
        row
        for row in rows
        if row["kind"] in LATEX_SEMANTIC_ENVIRONMENTS
        and row["semantic_review_status"].startswith("reviewed-")
    ]
    pending_rows = [
        row
        for row in rows
        if row["kind"] in LATEX_SEMANTIC_ENVIRONMENTS
        and row["semantic_review_status"] == "pending-semantic-review"
    ]
    if {row["idea_id"] for row in reviewed_rows} != set(labeled_decisions):
        issues.append("reviewed labeled-unit set differs from decisions")
    if len(reviewed_rows) != summary_payload.get("labeled_reviewed_count"):
        issues.append("labeled reviewed count differs from summary")
    if len(pending_rows) != summary_payload.get("labeled_pending_count"):
        issues.append("labeled pending count differs from summary")
    reviewed_relations = dict(
        sorted(Counter(row["claim_relation"] for row in reviewed_rows).items())
    )
    reviewed_statuses = dict(
        sorted(Counter(row["semantic_review_status"] for row in reviewed_rows).items())
    )
    if reviewed_relations != summary_payload.get("labeled_reviewed_by_relation"):
        issues.append("labeled reviewed relations differ from summary")
    if reviewed_statuses != summary_payload.get("labeled_reviewed_by_status"):
        issues.append("labeled reviewed statuses differ from summary")
    if issues:
        print("IDEA LEDGER INDEX CHECK FAILED")
        for issue in issues[:25]:
            print(f"- {issue}")
        if len(issues) > 25:
            print(f"- ... {len(issues) - 25} additional issues")
        return 1
    print(f"IDEA LEDGER INDEX CHECK PASSED rows={len(rows)}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-index", action="store_true")
    args = parser.parse_args(argv)
    if args.check and args.check_index:
        parser.error("--check and --check-index are mutually exclusive")
    if args.check_index:
        return quick_index_check()
    rows = build_rows()
    csv_bytes = render_csv(rows)
    summary_bytes = (json.dumps(summary(rows), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if args.check:
        issues = []
        if not LEDGER_PATH.is_file() or LEDGER_PATH.read_bytes() != csv_bytes:
            issues.append("idea-ledger.csv is missing or stale")
        if not SUMMARY_PATH.is_file() or SUMMARY_PATH.read_bytes() != summary_bytes:
            issues.append("idea-ledger-summary.json is missing or stale")
        if issues:
            print("IDEA LEDGER CHECK FAILED")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print(f"IDEA LEDGER CHECK PASSED rows={len(rows)}")
        return 0
    LEDGER_PATH.write_bytes(csv_bytes)
    SUMMARY_PATH.write_bytes(summary_bytes)
    print(f"IDEA LEDGER BUILT rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
