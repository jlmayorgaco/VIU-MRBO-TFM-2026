from __future__ import annotations

from viu_mrob_tfm.sp1_geo.runner import audit_theory


def _check(name: str) -> dict:
    payload = audit_theory()
    return next(item for item in payload["checks"] if item["gate"] == name)


def test_qpg_logit_matches_small_entropic_convex_reference() -> None:
    check = _check("T2_vgne_kkt")
    assert check["passed"]
    assert check["value"] <= check["tolerance"]


def test_audit_dynamics_is_samplewise_monotone_under_declared_guard() -> None:
    check = _check("T3_sampled_monotonicity")
    assert check["passed"]
    assert check["value"] >= check["tolerance"]
