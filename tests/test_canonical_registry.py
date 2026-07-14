"""Regression gates for promoted TFM evidence and theory/citation bindings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.tfm_submit_utils import CANONICAL_SPS, ROOT, audit_file, canonical_file, failed_checks_from_audit


PROMOTED = {
    "SP1": "SP1_HOMOGENEOUS_v1_1",
    "SP2": "SP2_HETEROGENEOUS_GAME_v1_2",
    "SP3": "SP3_WRENCH_NASH_GAME_v1_1",
    "SP4": "SP4_DOCKING_GAME_CONFIRMATORY_v3",
    "SP5": "SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2",
}


def test_promoted_sp_registry_has_complete_core_artifacts() -> None:
    for sp, experiment_id in PROMOTED.items():
        meta = CANONICAL_SPS[sp]
        assert experiment_id in str(meta.config)
        assert experiment_id in str(meta.result_dir)
        assert (ROOT / meta.config).is_file()
        assert (ROOT / meta.result_dir / "report.md").is_file()
        assert canonical_file(sp, "runs.csv").is_file()
        assert canonical_file(sp, "summary.csv").is_file()
        assert failed_checks_from_audit(audit_file(sp)) == 0


def test_run_canonical_uses_promoted_sp1_sp5_protocols() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    block = makefile.split("run-canonical:", 1)[1].split("clean-generated:", 1)[0]
    for experiment_id in PROMOTED.values():
        assert experiment_id in block
    for legacy in (
        "SP1_MC_recruitment_comparison",
        "SP2_MC_capacity_comparison",
        "SP5_MC_cooperative_transport_high_power",
    ):
        assert legacy not in block


def test_theory_validation_and_thesis_figure_bindings_are_current() -> None:
    manifest = json.loads((ROOT / "results/theory_validation/manifest.json").read_text(encoding="utf-8"))
    assert manifest["all_passed"] is True
    expected = (
        "fig_v1_kkt_wrench_allocation.png",
        "fig_v2_hamiltonian_hocbf.png",
        "fig_v3_practical_iss.png",
    )
    theory = (ROOT / "docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex").read_text(encoding="utf-8")
    for name in expected:
        assert name in theory
        assert list((ROOT / "results/theory_validation").rglob(name))
    for stale in ("fig_v1_share_vs_theory", "fig_v2_poa_curve", "fig_v3_stability_boundary"):
        assert stale not in theory


def test_citation_audit_is_bound_to_current_included_sources() -> None:
    report_root = ROOT / "docs/doc-05-final-report"
    audit = json.loads((report_root / "CITATION_AUDIT.json").read_text(encoding="utf-8"))
    assert audit["verdict"] == "WARN"
    assert audit["reason_code"] == (
        "local_citation_verification_passed_external_cross_family_and_similarity_pending"
    )
    assert audit["details"]["total_entries"] == 110
    assert audit["details"]["cited_entries"] == 61
    assert audit["details"]["citation_uses"] == 123
    assert audit["details"]["current_unresolved_keys"] == []
    for relative, tagged_hash in audit["audited_input_hashes"].items():
        expected = tagged_hash.removeprefix("sha256:")
        assert hashlib.sha256((report_root / relative).read_bytes()).hexdigest() == expected

    freshness = json.loads(
        (report_root / "CITATION_AUDIT_FRESHNESS.json").read_text(encoding="utf-8")
    )
    assert freshness["status"] == "WARN_EXTERNAL"
    assert freshness["citation_status"] == "PASS_LOCAL"
    assert freshness["unresolved_cited_keys"] == 0
    assert freshness["current_pdf_sha256"] == hashlib.sha256(
        (report_root / "main.pdf").read_bytes()
    ).hexdigest()
