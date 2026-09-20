from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_v3_full_corpus_bibliometrics.py"
spec = importlib.util.spec_from_file_location("build_v3_full_corpus_bibliometrics", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def corpus() -> list[dict[str, str]]:
    return module.read_csv(module.CORPUS_PATH)


def test_fractional_family_weights_sum_to_one_per_document() -> None:
    rows = corpus()
    assert len(rows) == 244
    for row in rows:
        weights = module.family_weights(row)
        assert weights
        assert set(weights).issubset(module.FAMILY_ORDER)
        assert math.isclose(sum(weights.values()), 1.0, abs_tol=1e-12)


def test_period_shares_sum_to_one_without_multilabel_inflation() -> None:
    temporal = module.build_temporal_tables(corpus())
    for period in module.PERIOD_ORDER:
        denominator = temporal["period_denominators"][period]
        weighted_total = sum(
            temporal["period_family"][period][family]
            for family in module.FAMILY_ORDER
        )
        assert weighted_total == denominator


def test_moving_diversity_is_normalized() -> None:
    temporal = module.build_temporal_tables(corpus())
    values = [
        float(row["normalized_shannon_diversity"])
        for row in temporal["diversity_rows"]
        if row["normalized_shannon_diversity"]
    ]
    assert values
    assert all(0.0 <= value <= 1.0 for value in values)


def test_author_core_obeys_declared_thresholds() -> None:
    _, core, components, _ = module.author_graph(corpus())
    assert components
    assert all(len(component) >= 3 for component in components)
    assert all(core.nodes[node]["paper_count"] >= 2 for node in core.nodes)
    assert set(core.nodes) == set().union(*components)


def test_topic_communities_are_deterministic_and_nonempty() -> None:
    graph, backbone, communities, modularity = module.topic_graph(corpus())
    assert graph.number_of_nodes() == 20
    assert graph.number_of_edges() == 90
    assert backbone.number_of_edges() <= graph.number_of_edges()
    assert set(graph.nodes) == set().union(*communities)
    assert len(communities) == 3
    assert -1.0 <= modularity <= 1.0

