from pathlib import Path

import pytest

from viu_mrob_tfm.literature_coverage import (
    LedgerEntry,
    coverage_counts,
    parse_verified_entries,
    render_latex_fragment,
)


def test_parser_expands_ranges_and_ignores_non_verified_rows() -> None:
    ledger = """
| `a` | VERIFICADA | Author (1998). Title. | url | SP1--SP3 | claim | evidence | note |
| `b` | PARCIAL | Author (2001). Title. | url | SP0 | claim | evidence | note |
| `c` | VERIFICADA | Author (2024). Title. | url | Contexto, SP6, SP8 | claim | evidence | note |
"""

    entries = parse_verified_entries(ledger)

    assert entries == (
        LedgerEntry("a", 1998, frozenset({1, 2, 3})),
        LedgerEntry("c", 2024, frozenset({6, 8})),
    )


def test_coverage_counts_once_per_sp_and_period() -> None:
    entries = (
        LedgerEntry("a", 1998, frozenset({1, 2})),
        LedgerEntry("b", 2003, frozenset({1})),
        LedgerEntry("c", 2024, frozenset({8})),
    )

    counts = coverage_counts(entries)

    assert counts[1] == (0, 2, 0, 0, 0, 0, 0)
    assert counts[2] == (0, 1, 0, 0, 0, 0, 0)
    assert counts[8] == (0, 0, 0, 0, 0, 0, 1)


def test_verified_row_without_year_is_rejected() -> None:
    ledger = (
        "| `a` | VERIFICADA | Author. Title. | url | SP0 | claim | evidence | note |"
    )

    with pytest.raises(ValueError, match="no publication year"):
        parse_verified_entries(ledger)


def test_verified_undated_web_row_requires_auditable_metadata() -> None:
    ledger = """
| `web` | VERIFICADA | Example Robotics. (s. f.). *Industrial AMR catalogue*. | [Official site](https://example.org/amr) | Contexto, SP1 | Declared product scope. | Official primary page verified on 2026-09-08. | Commercial scope only. |
"""

    assert parse_verified_entries(ledger) == (
        LedgerEntry("web", None, frozenset({1})),
    )


@pytest.mark.parametrize(
    ("reference", "url_cell", "evidence", "message"),
    (
        ("(s. f.). *Title*.", "https://example.org", "Checked.", "no author"),
        ("Author. (s. f.).", "https://example.org", "Checked.", "no title"),
        ("Author. (s. f.). *Title*.", "Official site", "Checked.", "no HTTP"),
        ("Author. (s. f.). *Title*.", "https://example.org", "—", "no verification evidence"),
    ),
)
def test_verified_undated_web_row_rejects_missing_required_metadata(
    reference: str,
    url_cell: str,
    evidence: str,
    message: str,
) -> None:
    ledger = (
        f"| `web` | VERIFICADA | {reference} | {url_cell} | SP1 | claim | "
        f"{evidence} | note |"
    )

    with pytest.raises(ValueError, match=message):
        parse_verified_entries(ledger)


def test_repository_ledger_renders_all_canonical_rows() -> None:
    ledger_path = Path("references/LITERATURE_LEDGER.md")

    fragment = render_latex_fragment(ledger_path.read_text(encoding="utf-8"))

    assert fragment.count(r"\coveragegeneratedrow{") == 9
    assert r"\coveragegeneratedrow{SP0}{Asignaci\'on 1--1}" in fragment
    assert r"\coveragegeneratedrow{SP8}{Escala / red}" in fragment
    assert "Ledger SHA-256:" in fragment


def test_theoretical_framework_keeps_restored_literature_figures() -> None:
    chapter_source = Path(
        "pre-thesis/sections/source-snapshot/mainmatter/05-theoretical-framework.tex"
    ).read_text(encoding="utf-8")
    intro_contract = Path("pre-thesis/sections/intro-contracts.tex").read_text(
        encoding="utf-8"
    )
    method_comparison = Path(
        "pre-thesis/sections/method-comparison.tex"
    ).read_text(encoding="utf-8")

    assert r"\label{fig:tf-problem-gap}" in intro_contract
    assert r"\label{tab:tf-comparison}" in method_comparison
    assert r"\label{fig:tf-literature-timeline}" in chapter_source
    assert r"\input{shared/generated-macros/literature-coverage.tex}" in chapter_source
    assert r"\label{fig:tf-methodological-map}" in chapter_source
    assert chapter_source.count(r"\label{fig:tf-literature-timeline}") == 1
    assert chapter_source.count(r"\label{fig:tf-methodological-map}") == 1
