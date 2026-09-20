from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


BASE = Path(__file__).parents[1]
V3 = BASE / "literature-review-v3"
CORPUS = V3 / "data" / "analytic_corpus_v3.csv"
MANUSCRIPT = V3 / "final" / "REVISION_SISTEMATIZADA_MRTA_COT_AMR_V3.md"


def rows() -> list[dict[str, str]]:
    with CORPUS.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def multilabel_count(data: list[dict[str, str]], field: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in data:
        counts.update(item for item in row[field].split(";") if item)
    return counts


def test_final_review_core_counts_match_generated_corpus() -> None:
    data = rows()
    text = MANUSCRIPT.read_text(encoding="utf-8")
    themes = multilabel_count(data, "theme_signals_title_abstract")
    methods = multilabel_count(data, "method_focus_title_abstract")

    assert len(data) == 244
    assert sum(row["close_reading_eligibility"] == "eligible" for row in data) == 168
    assert themes["SP1_coalition_allocation"] == 115
    assert themes["SP2_physical_transport"] == 15
    assert themes["SP3_planning_traffic"] == 20
    assert methods["consensus_distributed"] == 62
    assert methods["auction_market"] == 40
    assert sum(row["venue"].casefold().startswith("arxiv") for row in data) == 10

    for expected in ("244 documentos", "168 textos", "115 señales", "15 de transporte físico", "20 de planificación/tráfico"):
        assert expected in text


def test_final_review_close_reading_count_is_current() -> None:
    cards = [path for path in (V3 / "close-read").glob("*.md") if path.name != "README.md"]
    text = MANUSCRIPT.read_text(encoding="utf-8")
    assert len(cards) == 20
    assert "Veinte fuentes prioritarias" in text
    assert "Solo 20 trabajos recibieron lectura cercana" in text
