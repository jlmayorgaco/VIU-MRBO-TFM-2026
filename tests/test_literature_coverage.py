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


def test_repository_ledger_renders_all_canonical_rows() -> None:
    ledger_path = Path("references/LITERATURE_LEDGER.md")

    fragment = render_latex_fragment(ledger_path.read_text(encoding="utf-8"))

    assert fragment.count(r"\coveragegeneratedrow{") == 9
    assert r"\coveragegeneratedrow{SP0}{Asignaci\'on 1--1}" in fragment
    assert r"\coveragegeneratedrow{SP8}{Escala / red}" in fragment
    assert "Ledger SHA-256:" in fragment


def test_theoretical_framework_keeps_architecture_and_comparison_sources() -> None:
    chapter_source = Path(
        "thesis/sections/mainmatter/05-theoretical-framework.tex"
    ).read_text(encoding="utf-8")

    assert r"\label{fig:tf-problem-gap}" in chapter_source
    assert r"\label{tab:tf-comparison}" in chapter_source
    assert r"\LiteraturePeriods" not in chapter_source
    assert r"\coveragegeneratedrow" not in chapter_source
