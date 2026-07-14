"""Tests for the VIU submit-ready document gate."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "submit_ready_gate.py"
SPEC = importlib.util.spec_from_file_location("submit_ready_gate", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
submit_ready_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = submit_ready_gate
SPEC.loader.exec_module(submit_ready_gate)


def write_minimal_latex(tmp_path: Path, include_ai_declaration: bool = True) -> Path:
    (tmp_path / "viu-mrob-midreport.sty").write_text("% local style placeholder\n", encoding="utf-8")
    ai_section = (
        r"""
\section{Declaracion de uso de IA generativa}
Se declara el uso de herramientas de inteligencia artificial como apoyo editorial,
con revision humana completa del contenido tecnico y de las fuentes.
"""
        if include_ai_declaration
        else ""
    )
    main_tex = tmp_path / "main.tex"
    main_tex.write_text(
        rf"""
\documentclass[12pt,a4paper]{{article}}
\usepackage{{viu-mrob-midreport}}
\setviutitle{{Titulo TFM}}
\setviustudent{{Estudiante}}
\setviututor{{Tutor}}
\setviuedition{{2025--26}}
\setviudate{{1 de julio de 2026}}
\setviuheadertitle{{Titulo corto}}
\begin{{document}}
\makeviucover
\begin{{viuabstract}}
Resumen del trabajo con una descripcion suficiente del problema y su evidencia.
\keywords{{AMR, transporte cooperativo, validacion}}
\end{{viuabstract}}
\tableofcontents
\section{{Nomenclatura}}
Definiciones basicas.
\section{{Introduccion}}
Texto introductorio con soporte bibliografico \citep{{smith2024}}.
\section{{Objetivos}}
Objetivo general y objetivos especificos.
\section{{Hipotesis de partida}}
Hipotesis falsables.
\section{{Metodologia}}
Metodo, escenarios, metricas y semillas.
\section{{Marco teorico}}
Estado del arte y fundamentos.
\section{{Resultados y analisis}}
\subsection{{Validacion de los resultados}}
Resultados principales y validacion.
\section{{Conclusiones y recomendaciones}}
Conclusiones acotadas por la evidencia.
{ai_section}
\section{{Referencias bibliograficas}}
\bibliographystyle{{apalike}}
\bibliography{{references}}
\appendix
\section{{Anexo reproducibilidad}}
Material complementario.
\end{{document}}
""",
        encoding="utf-8",
    )
    (tmp_path / "references.bib").write_text(
        """
@article{smith2024,
  title={Distributed allocation},
  author={Smith, Ada},
  journal={Robotics Journal},
  year={2024}
}
""",
        encoding="utf-8",
    )
    return main_tex


def read_report(output_dir: Path) -> dict[str, object]:
    reports = list(output_dir.glob("*_submit_ready_report.json"))
    assert len(reports) == 1
    return json.loads(reports[0].read_text(encoding="utf-8"))


def test_submit_ready_gate_accepts_minimal_latex_with_similarity_report(tmp_path: Path) -> None:
    main_tex = write_minimal_latex(tmp_path)
    report = tmp_path / "similarity.txt"
    report.write_text("Similitud total: 4%", encoding="utf-8")
    output_dir = tmp_path / "out"

    exit_code = submit_ready_gate.main(
        [
            "--file",
            str(main_tex),
            "--similarity-report",
            str(report),
            "--output-dir",
            str(output_dir),
            "--min-words",
            "10",
            "--min-citations",
            "1",
            "--min-bib-entries",
            "1",
        ]
    )

    payload = read_report(output_dir)
    assert exit_code == 0
    assert payload["status"] in {"PASS", "PASS_WITH_WARNINGS"}
    assert payload["counts"]["blockers"] == 0


def test_submit_ready_gate_blocks_missing_ai_declaration(tmp_path: Path) -> None:
    main_tex = write_minimal_latex(tmp_path, include_ai_declaration=False)
    report = tmp_path / "similarity.txt"
    report.write_text("Similitud total: 4%", encoding="utf-8")
    output_dir = tmp_path / "out"

    exit_code = submit_ready_gate.main(
        [
            "--file",
            str(main_tex),
            "--similarity-report",
            str(report),
            "--output-dir",
            str(output_dir),
            "--min-words",
            "10",
            "--min-citations",
            "1",
            "--min-bib-entries",
            "1",
        ]
    )

    payload = read_report(output_dir)
    checks = {finding["check"] for finding in payload["findings"]}
    assert exit_code == 1
    assert payload["status"] == "FAIL"
    assert "declaracion-ia" in checks


def test_submit_ready_gate_blocks_high_similarity_report(tmp_path: Path) -> None:
    main_tex = write_minimal_latex(tmp_path)
    report = tmp_path / "similarity.txt"
    report.write_text("Similarity score: 31%", encoding="utf-8")
    output_dir = tmp_path / "out"

    exit_code = submit_ready_gate.main(
        [
            "--file",
            str(main_tex),
            "--similarity-report",
            str(report),
            "--output-dir",
            str(output_dir),
            "--min-words",
            "10",
            "--min-citations",
            "1",
            "--min-bib-entries",
            "1",
        ]
    )

    payload = read_report(output_dir)
    checks = {finding["check"] for finding in payload["findings"]}
    assert exit_code == 1
    assert payload["status"] == "FAIL"
    assert "similarity-score" in checks


def test_latex_to_plain_omits_tikzpicture_source() -> None:
    raw = r"""
\begin{figure}
\begin{tikzpicture}[flow/.style={-{Latex[length=2.3mm]},line width=0.9pt}]
\node {Visible node text from drawing source};
\end{tikzpicture}
\caption{Real caption text}
\end{figure}
"""

    plain = submit_ready_gate.latex_to_plain(raw)
    norm = submit_ready_gate.normalize_for_search(plain)

    assert "flow style" not in norm
    assert "visible node text" not in norm
    assert "real caption text" in norm


def test_page_budget_excludes_front_matter_and_separates_appendices() -> None:
    pages = ["Portada", "Contenido\n1. Introduccion\nA. Desarrollo matematico extendido"]
    pages += ["1. Introduccion\nTexto principal", "Texto principal", "Texto principal"]
    pages += ["Conclusiones\nTexto final\n" + ("contenido " * 30) + "\nA. Desarrollo matematico extendido"]
    pages += ["Material complementario"] * 2
    pages += ["Referencias bibliograficas\nFuente", "Fuente adicional"]

    budget = submit_ready_gate.calculate_page_budget(pages)

    assert budget is not None
    assert budget["main_pages"] == 6
    assert budget["appendix_pages"] == 3
    assert budget["appendix_shares_main_page"] is True


def test_human_writing_flags_formulaic_contrast_and_punctuation_density() -> None:
    contrast = "No es una mejora, sino un cambio de criterio. "
    punctuated = (
        "Este párrafo presenta un dato medido con semilla controlada; compara el resultado "
        "con una referencia común; valida la diferencia con una métrica estable; y documenta "
        "la conclusión para mantener trazabilidad experimental."
    )
    text = (contrast * 3) + "\n\n" + "\n\n".join([punctuated] * 6)
    doc = submit_ready_gate.DocumentSource(
        path=Path("manuscript.tex"),
        kind="tex",
        raw_text=text,
        plain_text=text,
        included_files=(),
        missing_includes=(),
        notes=(),
    )
    findings: list[submit_ready_gate.Finding] = []

    submit_ready_gate.check_human_writing(doc, findings, warn_density=4.0, block_density=12.0)

    checks = {finding.check for finding in findings}
    assert "contrastive-reframing" in checks
    assert "semicolon-density" in checks


def test_figure_attribution_blocks_caption_without_source_note() -> None:
    raw = r"""
\begin{figure}
\includegraphics{result.png}
\caption{Resultado experimental.}
\label{fig:result}
\end{figure}
"""
    doc = submit_ready_gate.DocumentSource(
        path=Path("manuscript.tex"),
        kind="tex",
        raw_text=raw,
        plain_text="Resultado experimental.",
        included_files=(),
        missing_includes=(),
        notes=(),
    )
    findings: list[submit_ready_gate.Finding] = []

    submit_ready_gate.check_figure_attribution(doc, findings)

    assert any(finding.check == "source-note" for finding in findings)


def test_style_prose_excludes_tikz_and_table_syntax_but_keeps_caption() -> None:
    raw = r"""
Texto narrativo directo.
\begin{table}
a; b; c: d \\
\end{table}
\begin{figure}
\begin{tikzpicture}
\draw (0,0) -- (1,1);
\end{tikzpicture}
\caption{Diagrama del método.}
\viuownsource
\end{figure}
"""
    doc = submit_ready_gate.DocumentSource(
        path=Path("manuscript.tex"),
        kind="tex",
        raw_text=raw,
        plain_text=submit_ready_gate.latex_to_plain(raw),
        included_files=(),
        missing_includes=(),
        notes=(),
    )

    prose = submit_ready_gate.prose_for_style_checks(doc)

    assert "Texto narrativo directo" in prose
    assert "Diagrama del método" in prose
    assert "--" not in prose
    assert ";" not in prose


def test_style_prose_figure_marker_does_not_remove_neighbor_sections() -> None:
    raw = r"""
% BEGIN included: docs/sections/introduction.tex
Texto de introduccion.

% BEGIN included: docs/figures/diagram.tex
\begin{figure}\caption{Diagrama propio.}\viuownsource\end{figure}

% BEGIN included: docs/sections/methodology.tex
Texto de metodologia.
"""
    doc = submit_ready_gate.DocumentSource(
        path=Path("manuscript.tex"),
        kind="tex",
        raw_text=raw,
        plain_text=submit_ready_gate.latex_to_plain(raw),
        included_files=(),
        missing_includes=(),
        notes=(),
    )

    prose = submit_ready_gate.prose_for_style_checks(doc)

    assert "Texto de introduccion" in prose
    assert "Texto de metodologia" in prose
    assert "Diagrama propio" in prose


def test_parse_bib_paths_accepts_biblatex_resource(tmp_path: Path) -> None:
    bib = tmp_path / "references.bib"
    bib.write_text("@book{key, title={Title}, year={2024}}\n", encoding="utf-8")

    paths = submit_ready_gate.parse_bib_paths(
        r"\addbibresource{references.bib}", tmp_path
    )

    assert paths == [bib.resolve()]


def test_claim_safety_accepts_explicit_scope_limiter() -> None:
    text = "La validación sigue siendo mesoscópica, sin despliegue industrial."
    doc = submit_ready_gate.DocumentSource(
        path=Path("manuscript.tex"),
        kind="tex",
        raw_text=text,
        plain_text=text,
        included_files=(),
        missing_includes=(),
        notes=(),
    )
    findings: list[submit_ready_gate.Finding] = []

    submit_ready_gate.check_claim_safety(doc, findings)

    assert not findings


def test_claim_safety_reads_scope_limiter_across_wrapped_lines() -> None:
    text = "Quedan fuera la validación física,\nla certificación y el despliegue industrial."
    doc = submit_ready_gate.DocumentSource(
        path=Path("manuscript.tex"),
        kind="tex",
        raw_text=text,
        plain_text=text,
        included_files=(),
        missing_includes=(),
        notes=(),
    )
    findings: list[submit_ready_gate.Finding] = []

    submit_ready_gate.check_claim_safety(doc, findings)

    assert not findings
