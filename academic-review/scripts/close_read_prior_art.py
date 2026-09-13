"""Generate a bounded, traceable close-reading ledger for the nearest prior art.

The source matrix is the evidence boundary.  The notes below are deliberately
conservative reading notes: they record what the local full text or publisher
preview supports and what it does not support.  This is not a novelty proof and
does not replace author verification before manuscript use.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = ROOT / "academic-review/data/processed/fulltext_evidence_matrix.csv"
DEFAULT_CSV = ROOT / "academic-review/data/processed/prior_art_close_reading.csv"
DEFAULT_REPORT = ROOT / "academic-review/reports/prior_art_close_reading.md"


MANUAL_NOTES: dict[str, dict[str, str]] = {
    "CDE40EBBE4028": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "1-page local PDF; abstract/overview and structural term evidence",
        "source_pages_or_sections": "p. 1, abstract/overview; Cooperate Task of Multiple Robots System",
        "tfm_axes": "SP2 contact/caging; distributed object-closure test; formation",
        "what_source_supports": "A distributed algorithm is presented for testing object-caging/object-closure conditions with multiple mobile robots; the paper reports a sufficient-and-necessary checking idea for an irregular object and a simulation demonstration.",
        "what_source_does_not_support": "It does not establish coalition recruitment, heterogeneous capacities, wrench feasibility, transport control, traffic coordination, or a failure-replacement protocol.",
        "confidence": "medium",
        "human_verification_required": "true",
        "allowed_use": "SP2 contact/caging prior art and a bounded motivation for explicit mechanical feasibility checks; do not use as evidence for integrated transport.",
    },
    "C20FBE73D7292": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "16-page local PDF; abstract, algorithm, consensus phase, complexity/convergence discussion, and comparative simulations",
        "source_pages_or_sections": "pp. 1-3, 6, 8-13; Abstract; C. Consensus Phase; D. Analysis of the Approach; Experimental Setup",
        "tfm_axes": "SP1 distributed allocation; local consensus; messages/makespan; navigation abstraction",
        "what_source_supports": "The CBBA-plus-ACS approach distributes bundle inclusion and conflict resolution among UAV agents and compares makespan, travelled distance, and exchanged messages in simulated search-and-rescue scenarios.",
        "what_source_does_not_support": "Its tasks are abstract survivor visits/navigation; it does not demonstrate multi-robot payload contact, heterogeneous wrench sharing, coalition lifting, or physical failure recovery. The reported convergence/near-optimality discussion is algorithm- and parameter-specific, not a global proof for the TFM mechanism.",
        "confidence": "high",
        "human_verification_required": "true",
        "allowed_use": "SP1 distributed-allocation comparator and communication/makespan metric precedent; not a mechanical-transport baseline.",
    },
    "CB157C72BD65E": {
        "review_mode": "agent_close_reading_publisher_html",
        "evidence_basis": "Publisher HTML page with abstract and structural metadata; detailed experimental claims remain access-limited",
        "source_pages_or_sections": "Abstract; A Distributed Task Allocation Algorithm",
        "tfm_axes": "SP1 heterogeneous task allocation; auction/consensus; inter-robot communication",
        "what_source_supports": "The abstract describes CBPAE, a distributed auction-and-consensus procedure for heterogeneous robots, heterogeneous tasks, and priorities, with parallel auction/execution and conflict resolution through inter-robot communication.",
        "what_source_does_not_support": "The available local evidence does not support detailed numerical claims, mechanical transport, contact feasibility, coalition wrench allocation, or recovery after a robot failure.",
        "confidence": "medium",
        "human_verification_required": "true",
        "allowed_use": "SP1 literature context for distributed auction/consensus; cite only abstract-level claims until the author verifies the full text.",
    },
    "CDEDC925F7B23": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "9-page local PDF; model, group-collaboration framework, task allocation, simulation, and failure/rescue passages",
        "source_pages_or_sections": "pp. 1-2, 4-7, 9; Model Assumption; Group Collaboration; Player/Stage simulation; agent-node failure/rescue discussion",
        "tfm_axes": "SP1 group formation; ability/history relevance; SP2 failure signal",
        "what_source_supports": "TARARC uses robot ability and historical relevance to establish groups, includes an agent-node role and group collaboration, and discusses changes in agents plus a rescue strategy in a Player/Stage simulation setting.",
        "what_source_does_not_support": "It does not provide a mechanically grounded payload model, wrench/contact certificate, explicit heterogeneous-load capacity constraints, or an asynchronous recovery experiment comparable to the TFM protocol.",
        "confidence": "medium",
        "human_verification_required": "true",
        "allowed_use": "SP1 group-formation and failure-reconfiguration precedent; use the rescue description as a signal, not as evidence of equivalent recovery performance.",
    },
    "CDB55CB433AE2": {
        "review_mode": "agent_close_reading_publisher_html",
        "evidence_basis": "Open-access publisher/PMC HTML abstract and conclusion-level text",
        "source_pages_or_sections": "Abstract; conclusion/future-work text",
        "tfm_axes": "SP1 dynamic heterogeneous allocation; topology; communication efficiency",
        "what_source_supports": "The two-level clustered CBBA variant combines topology-centrality clustering with resource-balanced, distance-aware K-medoids, followed by local CBBA and inter-cluster coordination; the paper reports simulation comparisons using communication efficiency, task score, and runtime.",
        "what_source_does_not_support": "It does not establish physical payload transport, contact/wrench feasibility, AMR traffic with carried loads, or a failure-replacement law. Its larger-swarm and practical delay issues remain future-work limitations in the available text.",
        "confidence": "medium",
        "human_verification_required": "true",
        "allowed_use": "SP1 communication/topology and dynamic-allocation context; potential comparator for message/runtime measures, not for mechanics.",
    },
    "C23A9081289BD": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "6-page local PDF; system description, decentralized exploration, object pickup/relocation, communication and robustness passages",
        "source_pages_or_sections": "pp. 1-6; Abstract; Multi-Robot Aerial Exploration; control/communication description; conclusion",
        "tfm_axes": "SP2 execution; local communication; obstacle avoidance; failure-robustness signal",
        "what_source_supports": "A decentralized multi-UAV system searches, picks up, and relocates objects using local sensing/control, broadcast state, reactive collision avoidance, and a limited-bandwidth/failure-robustness discussion.",
        "what_source_does_not_support": "The three vehicles are identical and each independently handles objects; the paper does not show a coalition transporting one shared payload, heterogeneous capacity matching, contact-force sharing, or traffic coordination among carrying coalitions.",
        "confidence": "high",
        "human_verification_required": "true",
        "allowed_use": "SP2 decentralized execution and communication/avoidance context; useful negative boundary for independent pickup versus cooperative payload transport.",
    },
    "C82AC458AF2EC": {
        "review_mode": "agent_close_reading_publisher_html",
        "evidence_basis": "Publisher HTML abstract/landing-page evidence; full article details are not locally available",
        "source_pages_or_sections": "Abstract",
        "tfm_axes": "SP2 cooperative rigid-payload transport; nonholonomic kinematics; local accommodation",
        "what_source_supports": "The abstract describes two or more nonholonomic mobile manipulators with passive 2-DOF planar arms transporting a payload at their end effectors, with kinematic compatibility, leader-follower and decentralized variants, local sensing, and correction of relative configuration errors.",
        "what_source_does_not_support": "The available evidence does not support a claim about coalition recruitment, robot/cargo heterogeneity, wrench residual certification, traffic, or failure replacement; it is not evidence that the TFM's full SP1-SP3 integration has been solved.",
        "confidence": "medium",
        "human_verification_required": "true",
        "allowed_use": "Primary SP2 physical-transport precedent and motivation for explicit kinematic/contact constraints; verify full article before detailed comparison.",
    },
    "C96F294D621AC": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "20-page local PDF; abstract, coalition penalty/matching formulation, assumptions, and runtime analysis",
        "source_pages_or_sections": "pp. 1-2, 4, 6-7, 11, 18-19; Abstract; CF-HMRTA formulation; penalty function; runtime analysis; assumptions",
        "tfm_axes": "SP1 heterogeneous coalition formation; skills; temporal constraints; scalability claim",
        "what_source_supports": "CF-HMRTA formulates heterogeneous multi-robot task allocation as bipartite graph matching with skill requirements and temporal constraints; the paper reports an O(|E|) worst-case complexity claim, perfect matching conditions, and simulations with large robot/task counts.",
        "what_source_does_not_support": "It does not provide physical payload/contact mechanics, wrench feasibility, distributed transport control, traffic coordination, or a verified failure-replacement experiment. Reported runtime and complexity are claims of that paper, not reproduced here.",
        "confidence": "high",
        "human_verification_required": "true",
        "allowed_use": "Closest SP1 coalition-formation comparator; use to position capability/constraint matching, while preserving the TFM distinction between strategic feasibility and mechanical feasibility.",
    },
    "C806A699E9EBB": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "4-page local Nature PDF; abstract, experiments, recruitment and conclusion",
        "source_pages_or_sections": "pp. 1-4; abstract/introduction; experimental comparisons; conclusion",
        "tfm_axes": "SP1 recruitment; decentralized threshold control; group-size effects",
        "what_source_supports": "Ant-inspired decentralized threshold control recruits robot groups for foraging and item transport; the experiments vary group size and resource distribution and report effects of clustered versus uniform resources.",
        "what_source_does_not_support": "The evidence does not cover heterogeneous robots or loads, explicit coalition capacity/wrench constraints, AMR collision-free traffic, or a replacement protocol after failures.",
        "confidence": "high",
        "human_verification_required": "true",
        "allowed_use": "Foundational SP1 recruitment precedent and motivation for threshold-based local decisions; not a direct baseline for heterogeneous rigid-load transport.",
    },
    "C06C41AFDC1F1": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "18-page local PDF; abstract, coalition-formation problem, spatial/temporal constraints, algorithm and evaluation passages",
        "source_pages_or_sections": "pp. 1-2, 5, 13-17; Introduction; Abstract; spatial/temporal coalition formulation; completion-time evaluation",
        "tfm_axes": "SP1 coalition formation; spatial/temporal constraints; anytime optimization",
        "what_source_supports": "The work treats coalition formation with spatial and temporal constraints and develops an anytime/efficient allocation formulation that can be used as prior art for constrained coalition selection.",
        "what_source_does_not_support": "It does not establish physical contact, payload wrench feasibility, robot-motion execution, multi-coalition traffic, or fault recovery for carrying coalitions.",
        "confidence": "medium",
        "human_verification_required": "true",
        "allowed_use": "SP1 constrained-coalition background and possible central formulation comparator; do not conflate allocation feasibility with mechanical feasibility.",
    },
    "C740E1AD4CDC9": {
        "review_mode": "agent_close_reading_publisher_html",
        "evidence_basis": "Publisher HTML abstract/landing-page evidence; detailed article access is limited",
        "source_pages_or_sections": "Abstract",
        "tfm_axes": "SP1 dynamic task exchange; weak communication; changing teams",
        "what_source_supports": "The abstract describes a distributed PI-based dynamic allocation method for multi-AUV systems with weak acoustic communication, block information sharing, task exchange, and dynamic addition/deletion of tasks or AUVs.",
        "what_source_does_not_support": "It does not provide evidence for AMR payload transport, mechanical contact, collision-free warehouse traffic, or a comparable coalition-recovery metric.",
        "confidence": "low",
        "human_verification_required": "true",
        "allowed_use": "SP1 dynamic-task and weak-communication context only; verify full text before detailed methodological comparison.",
    },
    "CADFC0AC6330F": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "21-page local PDF; problem, event-triggered communication, security design, theorem/lemma statements and simulations",
        "source_pages_or_sections": "Abstract; Sections II-III; theorem/lemma and proof passages; simulations",
        "tfm_axes": "cross-cutting distributed communication; event triggering; formal safety/security boundary",
        "what_source_supports": "A secure decentralized event-triggered cooperative-localization design uses local inter-robot information and formal analysis under cyber attack; the paper provides theorem/lemma-level statements for its localization design and simulations.",
        "what_source_does_not_support": "It is not a task-allocation or cooperative-payload-transport method and cannot support claims about coalition utility, contact feasibility, traffic, or transport stability in the TFM.",
        "confidence": "high",
        "human_verification_required": "true",
        "allowed_use": "Communication/event-triggering and formal-evidence contrast; useful to keep localization guarantees separate from allocation and mechanics claims.",
    },
    "CD0C4805D863E": {
        "review_mode": "agent_close_reading_publisher_html",
        "evidence_basis": "Publisher HTML abstract/preview; full text is not locally available",
        "source_pages_or_sections": "Abstract",
        "tfm_axes": "cross-cutting taxonomy; communication/computation assumptions",
        "what_source_supports": "The paper proposes a taxonomy for multi-agent robotics organized around communication, computational, and other agent capabilities, providing a vocabulary for stating information assumptions.",
        "what_source_does_not_support": "It does not provide a concrete coalition algorithm, payload mechanics, experimental result for the TFM scenario, or a proof of scalability or robustness.",
        "confidence": "low",
        "human_verification_required": "true",
        "allowed_use": "Terminology and information-assumption framing only.",
    },
    "CEA1C303255D1": {
        "review_mode": "agent_close_reading_publisher_html",
        "evidence_basis": "Publisher HTML abstract/preview; full text is not locally available",
        "source_pages_or_sections": "Abstract",
        "tfm_axes": "SP1 team allocation/cooperation; communication/deadlock concerns",
        "what_source_supports": "The abstract frames multi-robot task allocation, cooperation, and interaction under dynamic workloads, and identifies communication/deadlock complexity while discussing affection-based and stochastic allocation ideas.",
        "what_source_does_not_support": "It does not support detailed algorithmic, physical-transport, traffic, failure-recovery, or quantitative performance claims from the local evidence.",
        "confidence": "low",
        "human_verification_required": "true",
        "allowed_use": "Historical/background context only; no strong claim without author verification of the full chapter.",
    },
    "C6F55B57AF2A5": {
        "review_mode": "agent_close_reading_access_limited",
        "evidence_basis": "Publisher HTML page with abstract-like preview text; article access is blocked/limited locally",
        "source_pages_or_sections": "Available abstract/preview text",
        "tfm_axes": "SP1 decentralized allocation; specialization/respecialization; response thresholds",
        "what_source_supports": "The available preview signals decentralized task allocation for hierarchical domains, specialization/respecialization, and adaptive response-threshold behavior.",
        "what_source_does_not_support": "The local evidence does not support detailed equations, experiments, robot or payload models, failure recovery, or the paper's performance claims beyond the preview wording.",
        "confidence": "low",
        "human_verification_required": "true",
        "allowed_use": "Candidate background reference; do not use for detailed novelty or quantitative comparisons until full text is verified.",
    },
    "C58FD63E3F184": {
        "review_mode": "agent_close_reading_fulltext",
        "evidence_basis": "16-page local PDF; problem statement, MILP comparison, GA/path-planning design, experiments and future-work limitations",
        "source_pages_or_sections": "pp. 2-5, 7-14; Introduction; Problem Statement; MILP Formulation; experiments; future work",
        "tfm_axes": "SP1 centralized allocation baseline; heterogeneous sensing; path planning",
        "what_source_supports": "The paper formulates a centralized inspection allocation with sensing specifications, compares a GA approach with HFBS and MILP/Cplex, and couples assignment with grid/path-planning decisions in simulation.",
        "what_source_does_not_support": "Its task model assigns each task to a single robot and does not establish distributed coalition formation, cooperative load transport, contact/wrench feasibility, or failure replacement; collision avoidance is listed as future work in the available text.",
        "confidence": "high",
        "human_verification_required": "true",
        "allowed_use": "SP1 centralized/oracle baseline context and a clear example of why single-robot assignment is insufficient for the TFM coalition problem.",
    },
}


FIELDS = [
    "candidate_id",
    "title",
    "authors",
    "year",
    "venue",
    "doi",
    "review_mode",
    "evidence_basis",
    "source_pages_or_sections",
    "tfm_axes",
    "what_source_supports",
    "what_source_does_not_support",
    "confidence",
    "human_verification_required",
    "allowed_use",
    "source_matrix_path",
    "fulltext_local_path",
    "source_sha256",
]


def _read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["candidate_id"]: row for row in csv.DictReader(handle)}


def build(matrix_path: Path, csv_path: Path, report_path: Path) -> None:
    rows = _read_rows(matrix_path)
    missing = sorted(set(MANUAL_NOTES) - set(rows))
    if missing:
        raise SystemExit(f"close-reading candidates missing from source matrix: {', '.join(missing)}")

    records: list[dict[str, str]] = []
    for candidate_id, notes in MANUAL_NOTES.items():
        source = rows[candidate_id]
        record = {
            "candidate_id": candidate_id,
            "title": source.get("title", ""),
            "authors": source.get("authors", ""),
            "year": source.get("year", ""),
            "venue": source.get("venue", ""),
            "doi": source.get("doi", ""),
            **notes,
            "source_matrix_path": matrix_path.relative_to(ROOT).as_posix(),
            "fulltext_local_path": source.get("fulltext_local_path", ""),
            "source_sha256": source.get("fulltext_sha256", ""),
        }
        records.append(record)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    axis_counts: dict[str, int] = {}
    for record in records:
        for axis in record["tfm_axes"].split("; "):
            axis_counts[axis] = axis_counts.get(axis, 0) + 1

    lines = [
        "# Bounded close reading of nearest prior art",
        "",
        "This artifact records an agent close reading of 16 candidates selected from the Stage 3 full-text evidence matrix. It is a bounded evidence ledger, not a systematic novelty proof and not a substitute for the author's final verification before manuscript use.",
        "",
        f"Source matrix: `{matrix_path.relative_to(ROOT).as_posix()}`.",
        "Each row keeps the local source path and SHA-256 recorded by Stage 3. Publisher previews and abstract-only pages are explicitly marked as access-limited; their claims must not be expanded into detailed method or performance statements.",
        "",
        "## Axis coverage in this bounded set",
        "",
        "| Axis recorded in reading notes | Candidates |",
        "|---|---:|",
    ]
    for axis, count in sorted(axis_counts.items()):
        lines.append(f"| {axis} | {count} |")
    lines += [
        "",
        "The most direct physical precedent in this set is cooperative rigid-payload transport by nonholonomic mobile manipulators (C82AC458AF2EC), while the closest allocation precedents are heterogeneous coalition matching (C96F294D621AC), constrained coalition formation (C06C41AFDC1F1), local recruitment (C806A699E9EBB), and distributed allocation/consensus (C20FBE73D7292, CB157C72BD65E). These sources address different layers; the bounded reading did not verify an integrated SP1-SP3 mechanism combining heterogeneous coalition selection, mechanical contact/wrench feasibility, carried-load traffic, and failure replacement.",
        "",
        "That last sentence is a bounded-review result: it means the integration was not established by these 16 close readings, not that no such work exists anywhere. The WoS export remains pending because the available session requires institutional authentication.",
        "",
        "## Candidate-level reading notes",
        "",
        "| ID | Source | TFM axis | Confidence | Allowed use |",
        "|---|---|---|---|---|",
    ]
    for record in records:
        source = f"[{record['authors']} ({record['year']})](https://doi.org/{record['doi']})"
        lines.append(
            f"| `{record['candidate_id']}` | {source}<br>{record['title']} | {record['tfm_axes']} | {record['confidence']} | {record['allowed_use']} |"
        )
    lines += [
        "",
        "## Reading discipline",
        "",
        "- `what_source_supports` is the strongest statement permitted by the inspected local evidence.",
        "- `what_source_does_not_support` is a guard against transferring allocation, localization, or abstract-level claims into mechanics or end-to-end transport.",
        "- Every row has `human_verification_required=true` because the final author must inspect the cited passage and decide whether it is appropriate for the VIU memory.",
        "- No claim in this ledger is a new TFM result, and no manuscript chapter was modified.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    build(args.matrix.resolve(), args.csv.resolve(), args.report.resolve())
    print(f"wrote {args.csv}")
    print(f"wrote {args.report}")
    print(f"candidates={len(MANUAL_NOTES)}")


if __name__ == "__main__":
    main()
