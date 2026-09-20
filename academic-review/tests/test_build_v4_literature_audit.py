from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_v4_literature_audit.py"
spec = importlib.util.spec_from_file_location("build_v4_literature_audit", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_v4_metrics_match_the_declared_v3_freeze() -> None:
    root = Path(__file__).resolve().parents[2]
    metrics, input_hashes = module.derive_metrics(root / "academic-review" / "literature-review-v3")

    assert metrics == module.EXPECTED_COUNTS
    assert set(input_hashes) == {"discovery_registry", "analytic_corpus", "close_read_cards"}
    assert all(len(value) == 64 for value in input_hashes.values())


def test_v4_rejects_a_freeze_mismatch() -> None:
    altered = dict(module.EXPECTED_COUNTS)
    altered["analytic_documents"] += 1

    try:
        module.assert_expected(altered)
    except ValueError as error:
        assert "freeze mismatch" in str(error).lower()
    else:
        raise AssertionError("A changed corpus denominator must fail the V4 gate.")
