from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "audit_pre_thesis_bibliography.py"
SPEC = importlib.util.spec_from_file_location("pre_thesis_bib_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def test_parser_preserves_nested_bibtex_values() -> None:
    entries = AUDIT.parse_bibtex(ROOT / "pre-thesis" / "bibliography" / "references.bib")
    by_key = {entry.key: entry for entry in entries}

    assert len(entries) == len(by_key)
    assert by_key["ames2017cbf"].fields["title"].casefold().startswith("control barrier")
    assert by_key["activmedia2003pioneer"].fields["author"] == "{ActivMedia Robotics, LLC}"


def test_latex_accents_do_not_create_false_surname_mismatches() -> None:
    expected = AUDIT.author_surnames(
        r"Cherukuri, Ashish and Mallada, Enrique and Cort{\'e}s, Jorge"
    )

    assert expected == ["cherukuri", "mallada", "cortes"]
    assert AUDIT.surname_equivalent(r"Mart{\'i}nez-Piazuelo", "martinez piazuelo")
    assert AUDIT.surname_equivalent(r"Nedi{\'c}", "nedic")


def test_reviewed_url_override_survives_transient_http_failure(monkeypatch) -> None:
    entry = AUDIT.BibEntry(
        entry_type="manual",
        key="manual",
        fields={"title": "Primary manual", "url": "https://example.invalid/manual.pdf"},
    )
    monkeypatch.setattr(AUDIT, "_fetch_url", lambda _url: (0, _url, "", "timeout"))

    row = AUDIT.verify_url(
        entry,
        {
            "verified": True,
            "source_url": "https://example.invalid/manual.pdf",
            "title": "Primary manual",
            "authors": "Manufacturer",
            "year": "2026",
            "notes": "Reviewed against the primary document.",
        },
    )

    assert row["http_status"] == 0
    assert row["existence_verdict"] == "VERIFIED"
    assert row["bibliographic_verdict"] == "VERIFIED"


def test_citation_extraction_reports_counts_and_ignores_comments(tmp_path: Path) -> None:
    (tmp_path / "sample.tex").write_text(
        "\\textcite{alpha} and \\parencite{beta,gamma}.\n% \\cite{ghost}\n",
        encoding="utf-8",
    )

    counts, scanned = AUDIT.extract_citations(tmp_path)

    assert counts == {"alpha": 1, "beta": 1, "gamma": 1}
    assert scanned == [(tmp_path / "sample.tex").as_posix()]


def test_nocite_key_is_part_of_rendered_reference_set(tmp_path: Path) -> None:
    (tmp_path / "sample.tex").write_text(r"\nocite{kept}", encoding="utf-8")

    counts, _ = AUDIT.extract_citations(tmp_path)

    assert counts == {"kept": 1}


def test_only_active_input_graph_contributes_citations(tmp_path: Path) -> None:
    (tmp_path / "main.tex").write_text(
        "\\input{active}\n\\iffalse\\input{disabled}\\fi\n",
        encoding="utf-8",
    )
    (tmp_path / "active.tex").write_text(r"\cite{kept}", encoding="utf-8")
    (tmp_path / "disabled.tex").write_text(r"\cite{hidden}", encoding="utf-8")
    (tmp_path / "unreachable.tex").write_text(r"\cite{unreachable}", encoding="utf-8")

    counts, scanned = AUDIT.extract_citations(tmp_path)

    assert counts == {"kept": 1}
    assert {Path(path).name for path in scanned} == {"main.tex", "active.tex"}
