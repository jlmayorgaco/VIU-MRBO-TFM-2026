from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "stage4_synthesize.py"
spec = importlib.util.spec_from_file_location("stage4_synthesize", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_split_terms_drops_empty_values() -> None:
    assert module.split_terms("auction;; consensus; ") == ["auction", "consensus"]


def test_presence_counts_are_derived_from_values() -> None:
    import pandas as pd

    result = module.presence_counts(pd.DataFrame({"x": ["a", "", "b"]}), "x")
    assert result == {"observed": 2, "not_observed": 1}


def test_analysis_index_has_data_driven_category_counts() -> None:
    result = module.make_analysis(99, "test", "Test", {"a": 2, "b": 1}, "test")
    assert result["categories"] == 2
    assert result["records_counted"] == 3
    assert (module.TABLES / "analysis_99_test.csv").exists()
    assert (module.FIGURES / "analysis_99_test.png").exists()
    (module.TABLES / "analysis_99_test.csv").unlink()
    (module.FIGURES / "analysis_99_test.png").unlink()
