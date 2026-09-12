from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "stage1b.py"
spec = importlib.util.spec_from_file_location("stage1b", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def screen(title: str, abstract: str = "") -> dict[str, str]:
    return module.screen_record(
        {
            "candidate_id": "TEST",
            "title": title,
            "abstract": abstract,
            "document_type": "journal-article",
            "provenance_sources": "test",
            "provenance_queries": "test",
        }
    )


def test_explicit_multi_robot_allocation_without_abstract_is_included() -> None:
    result = screen("Multi-Robot Task Allocation")

    assert result["screening_decision"] == "include_fulltext"
    assert result["screening_basis"] == "title_metadata_without_abstract"
    assert result["evidence_status"] == "not_evidence"


def test_swarm_uav_assignment_is_not_lost_as_single_robot() -> None:
    result = screen("Swarm UAVs Task and Resource Dynamic Assignment Algorithm")

    assert result["screening_decision"] == "include_fulltext"
    assert result["exclusion_reason"] == ""


def test_explicit_uav_ugv_cooperation_is_included() -> None:
    result = screen("Switched UAV-UGV Cooperation Scheme for Target Detection")

    assert result["screening_decision"] == "include_fulltext"
    assert result["exclusion_reason"] == ""


def test_heterogeneous_robot_coalition_title_is_not_marked_single_robot() -> None:
    result = screen("Scheduling Using Attention-Based Dynamic Coalitions of Heterogeneous Robots")

    assert result["screening_decision"] in {"include_fulltext", "maybe_fulltext"}
    assert result["exclusion_reason"] == ""


def test_run_on_multiagent_robot_title_is_deferred_or_included() -> None:
    result = screen("A Multiagent Robot Trash-Collecting Team")

    assert result["screening_decision"] in {"include_fulltext", "maybe_fulltext"}
    assert result["exclusion_reason"] == ""


def test_generic_multi_robot_title_is_deferred_to_full_text() -> None:
    result = screen("A Survey on Multi-Robot Systems")

    assert result["screening_decision"] == "maybe_fulltext"
    assert result["exclusion_reason"] == ""


def test_single_robot_problem_without_multi_robot_axis_is_excluded() -> None:
    result = screen("Contact Force Control for a Mobile Robot")

    assert result["screening_decision"] == "exclude"
    assert result["exclusion_reason"] == "no_multi_robot_component"


def test_retraction_note_is_not_added_to_full_text_queue() -> None:
    result = screen("Retraction Note: Strategic Allocation in Multi-Robot Systems")

    assert result["screening_decision"] == "exclude"
    assert result["exclusion_reason"] == "non_research_item"
