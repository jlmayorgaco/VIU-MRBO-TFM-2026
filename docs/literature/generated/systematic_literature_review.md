# Systematic literature review draft

Generated: 2026-06-24

## Executive summary

This review maps 5665 unique arXiv records (2010-2026) linked to 4 search-topic slices. The triage layer identified 174 high-priority, 2510 medium-priority, and 2981 low-priority records for the thesis question.

Full-text extraction was completed for 173 high-priority papers using the first pages of each PDF, while all records were classified from metadata, abstracts, and local topic labels. This is therefore a strong systematic mapping draft and a defensible starting point for a focused SLR, but not yet a final PRISMA review across IEEE/ACM/Scopus/Web of Science.

The evidence base is concentrated around distributed control, graph/network coordination, task allocation, cooperative transport, formation geometry, learning-based coordination, and warehouse/logistics robotics. The strongest thesis-relevant cluster is the intersection of multi-robot task allocation, coalition/payload constraints, distributed consensus/control, and cooperative transport.

## Method

The review follows the repository protocol in `docs/literature/systematic_review_protocol.md`. The search corpus was produced from arXiv API queries and organized by topic/year. Records were deduplicated by arXiv identifier, linked back to PDF paths, and inserted into `literature.sqlite`. Screening priority was assigned by transparent keyword rules over title, abstract, topic labels, and extracted text for high-priority records.

The method intentionally separates three layers:

1. Bibliographic corpus construction.
2. Systematic mapping and triage.
3. Focused full-text screening and evidence extraction.

Only the first two layers and an initial high-priority full-text pass are complete in this draft.

## Corpus profile

| Measure | Value |
|---|---:|
| Unique records | 5665 |
| High-priority records | 174 |
| Medium-priority records | 2510 |
| Low-priority records | 2981 |
| Topic/year links | 5931 |
| High-priority text extractions | 173 |

### PRISMA-style flow draft

| Stage | Records | Note |
|---|---:|---|
| Records identified from local arXiv corpus | 5665 | Deduplicated by arXiv identifier from available topic/year manifests. |
| Records prioritized for title/abstract screening | 174 | High-priority triage based on transparent keyword and topic rules. |
| Reports retrieved for full-text triage | 173 | PDF text extracted for high-priority records. |
| Reports not retrieved | 1 | High-priority records without an available local PDF at extraction time. |
| Studies included in narrative synthesis draft | 174 | Provisional inclusion for mapping; final inclusion requires manual reason-coded screening. |

This is a PRISMA-style accounting table for the local arXiv corpus. It is not yet a final PRISMA flow diagram because non-arXiv databases and manual exclusion reasons have not been completed.

### Dominant concepts in high-priority records

| Concept | Records |
|---|---:|
| graph network topology | 169 |
| robustness safety resilience | 156 |
| communication constraints | 146 |
| distributed control consensus | 143 |
| planning mapf navigation | 135 |
| optimization mpc | 134 |
| learning marl gnn | 92 |
| warehouse AMR logistics | 87 |
| formation rigidity geometry | 81 |
| task allocation coalitions | 69 |

### Recent growth pattern

| Year | Records | Cooperative transport | Task allocation / coalitions | Distributed control | Learning / MARL / GNN | Robustness / safety |
|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 571 | 10 | 31 | 171 | 127 | 239 |
| 2022 | 569 | 9 | 26 | 174 | 141 | 226 |
| 2023 | 576 | 9 | 24 | 164 | 163 | 234 |
| 2024 | 581 | 10 | 36 | 178 | 165 | 276 |
| 2025 | 622 | 16 | 42 | 219 | 130 | 317 |
| 2026 | 486 | 17 | 34 | 126 | 132 | 250 |

## Thematic synthesis

### 1. Distributed coordination is the organizing backbone

The corpus shows that distributed and decentralized coordination remains the central architectural response to scale, communication limits, and robot-team heterogeneity. Classical consensus, event-triggered control, distributed optimization, and local-neighborhood policies appear repeatedly as mechanisms for replacing centralized assignment or planning. For the thesis, this supports a design stance in which allocation, quorum formation, and control should be expressed as local update laws rather than as a single monolithic optimizer.

The strongest limitation is that many distributed-control papers prove convergence under idealized graph, sensing, or timing assumptions. That means they are useful for mathematical grounding, but must be filtered before being used as evidence for warehouse-scale cooperative transport.

### 2. Cooperative transport is a multi-layer problem, not only a control problem

High-priority transport papers consistently decompose the problem into coupled layers: task selection, robot coalition sizing, payload support geometry, path or trajectory generation, low-level tracking, and collision/communication constraints. Recent work on collective transport and assembly planning makes this explicit by combining task allocation, payload or subassembly constraints, geometric carrying configurations, and distributed execution.

This directly motivates the TFM architecture: Smith-style population dynamics or market dynamics can handle allocation pressure, but they need a second layer that turns fractional or preference-like decisions into physically feasible robot coalitions and rigid/contact formations.

### 3. Coalition formation and MRTA are the closest allocation literature

The most thesis-relevant allocation literature lies around MRTA, CBBA-like consensus bundle methods, auctions/markets, coalition formation, and resource allocation. These methods are valuable because they already formalize scarce robots, task demands, changing payloads, and local communication. However, many MRTA papers stop at assignment and do not model the wrench, rigid formation, or contact feasibility layer needed for cooperative load transport.

A useful gap statement is therefore: the literature often treats task allocation and cooperative transport control as adjacent but separate layers; fewer papers close the loop between distributed allocation, integer coalition feasibility, and physical formation/load constraints.

### 4. Graph theory is the common language between communication, formation, and allocation

Graph concepts appear in three roles. First, communication graphs encode who can exchange information. Second, rigidity and bearing/distance graphs encode whether a formation shape can be maintained. Third, task or environment graphs encode warehouse topology, exploration frontiers, or allocation structure. This is one of the strongest bridges for the thesis because it allows a single mathematical language to relate network connectivity, quorum construction, and formation validity.

The review also indicates a risk: generic graph/network papers can be mathematically interesting but weakly transferable. They should be used only when their assumptions map clearly to robot communication, formation, or warehouse-task graphs.

### 5. Game theory and market dynamics are useful when scarcity and incentives matter

Game-theoretic papers contribute useful mechanisms for distributed resource allocation, payoff shaping, potential games, Stackelberg interactions, evolutionary dynamics, and mean-field abstractions. Their relevance is strongest when the robot team faces scarce capacity, heterogeneous costs, or competing task demands. This maps well to the Smith-QR direction because Smith dynamics can be interpreted as population/game dynamics over task alternatives.

The evidence is less direct for physical transport. Many game-theoretic models are abstract and require an explicit bridge from payoff definitions to measurable robot quantities such as wrench deficit, travel cost, communication load, queue pressure, or payload risk.

### 6. Learning methods are growing, but they do not replace structure

MARL, graph neural networks, and learned decentralized policies appear strongly in recent high-priority records. The most relevant papers use learning to improve scalability, transfer, or local decision policies, often with graph encoders or hierarchical task-priority structures. The recurring pattern is not pure end-to-end learning, but structured learning: learning is embedded inside task allocation, message passing, graph abstraction, or hierarchical control.

For the TFM, this suggests MARL should be treated as a comparator or extension, not as the core explanatory mechanism. A hand-designed distributed mechanism remains more auditable for thesis validation, while learning-based methods can benchmark adaptability under changing team size, object weights, and communication constraints.

### 7. Robustness, safety, and communication are under-integrated

Robustness appears through resilient consensus, fault/attack models, H-infinity or Lyapunov arguments, safety-critical control, collision avoidance, and communication constraints. However, the evidence map suggests these are often treated as separate problem families rather than integrated with transport allocation and formation.

This is a defensible research gap for the thesis: a complete cooperative-transport architecture should jointly handle allocation scarcity, communication degradation, coalition closure, formation/contact feasibility, and robustness metrics.

## Key high-priority studies

| Year | arXiv | Study | Main concepts | Validation signals |
|---:|---|---|---|---|
| 2014 | 1402.2871 | Planning for Decentralized Control of Multiple Robots Under Uncertainty | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, real robot, survey |
| 2020 | 2008.00679 | Cooperative Control of Mobile Robots with Stackelberg Learning | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, simulation, real robot, open source |
| 2023 | 2311.00192 | Large-Scale Multi-Robot Assembly Planning for Autonomous Manufacturing | cooperative transport, task allocation coalitions, distributed control consensus, formation rigidity geometry | theory, simulation, real robot, open source |
| 2025 | 2509.16482 | Robot Conga: A Leader-Follower Walking Approach to Sequential Path Following in Multi-A... | task allocation coalitions, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, real robot, open source |
| 2021 | 2105.00389 | Multi-Robot Coordination and Planning in Uncertain and Adversarial Environments | task allocation coalitions, distributed control consensus, formation rigidity geometry, graph network topology | theory, real robot, survey |
| 2026 | 2604.11954 | Dynamic Multi-Robot Task Allocation under Uncertainty and Communication Constraints: A... | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, simulation, open source, survey |
| 2022 | 2212.02692 | Learning Locally, Communicating Globally: Reinforcement Learning of Multi-robot Task Al... | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, simulation, real robot, open source |
| 2026 | 2605.26430 | Multi-Robot Box Transport over Different Surfaces with Decentralized Role-based Proport... | cooperative transport, task allocation coalitions, distributed control consensus, formation rigidity geometry | theory, simulation, real robot, survey |
| 2022 | 2211.06917 | Distributed Data-Driven Predictive Control for Multi-Agent Collaborative Legged Locomotion | cooperative transport, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, real robot, survey |
| 2023 | 2309.04257 | A Tutorial on Distributed Optimization for Cooperative Robotics: from Setups and Algori... | task allocation coalitions, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, survey |
| 2024 | 2412.10087 | Consensus-Based Dynamic Task Allocation for Multi-Robot System Considering Payloads Con... | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, simulation, real robot |
| 2024 | 2404.11817 | Reinforcement Learning of Multi-robot Task Allocation for Multi-object Transportation w... | cooperative transport, task allocation coalitions, distributed control consensus, formation rigidity geometry | simulation, open source, survey |
| 2026 | 2604.15475 | NeuroMesh: A Unified Neural Inference Framework for Decentralized Multi-Robot Collabora... | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, simulation, real robot, open source |
| 2026 | 2603.06356 | Safe Consensus of Cooperative Manipulation with Hierarchical Event-Triggered Control Ba... | cooperative transport, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, real robot, survey |
| 2023 | 2306.12331 | Decentralized Aerial Transportation and Manipulation of a Cable-Slung Payload With Swar... | cooperative transport, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, survey |
| 2026 | 2606.09610 | Shape Formation for the Cooperative Transportation of Arbitrary Objects Using Multi-Age... | cooperative transport, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, survey |
| 2021 | 2109.14755 | Decentralized Role Assignment in Multi-Agent Teams via Empirical Game-Theoretic Analysis | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, simulation, survey |
| 2024 | 2404.02362 | Task-priority Intermediated Hierarchical Distributed Policies: Reinforcement Learning o... | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | simulation, real robot, survey |
| 2026 | 2606.04248 | RSC: Decentralized Rigid Formation Flocking for Large-Scale Swarms via Hybrid Predictiv... | cooperative transport, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, real robot, survey |
| 2020 | 2007.09243 | Multi-robot Cooperative Object Transportation using Decentralized Deep Reinforcement Le... | cooperative transport, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, open source, survey |
| 2021 | 2108.06886 | Decentralized multi-AMR Task Allocation based on Multi-Agent Reinforcement Learning wit... | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, simulation, survey |
| 2024 | 2409.18031 | Reasoning Multi-Agent Behavioral Topology for Interactive Autonomous Driving | task allocation coalitions, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, open source, survey |
| 2025 | 2503.19135 | Cooperative Control of Multi-Quadrotors for Transporting Cable-Suspended Payloads: Obst... | cooperative transport, task allocation coalitions, distributed control consensus, graph network topology | theory, simulation, survey |
| 2025 | 2503.20723 | Multi-Robot Coordination Under Physical Limitations | cooperative transport, distributed control consensus, formation rigidity geometry, graph network topology | theory, simulation, real robot |
| 2025 | 2510.26536 | RoboOS-NeXT: A Unified Memory-based Framework for Lifelong, Scalable, and Robust Multi-... | cooperative transport, task allocation coalitions, formation rigidity geometry, graph network topology | theory, simulation, real robot, open source |

## Author and community signals

The author-productivity table should not be interpreted as impact ranking, because the corpus is arXiv-first and query-dependent. It is useful for identifying recurring research groups for citation chasing.

| Author | Records | High-priority records | Main concepts |
|---|---:|---:|---|
| Dimos V. Dimarogonas | 47 | 1 | distributed_control_consensus;graph_network_topology;communication_constraints;robustness_safety_resilience;optimization_mpc |
| Karl H. Johansson | 39 | 0 | distributed_control_consensus;graph_network_topology;communication_constraints;robustness_safety_resilience;optimization_mpc |
| Hideaki Ishii | 35 | 1 | distributed_control_consensus;graph_network_topology;robustness_safety_resilience;communication_constraints;optimization_mpc |
| George J. Pappas | 34 | 2 | robustness_safety_resilience;graph_network_topology;communication_constraints;optimization_mpc;distributed_control_consensus |
| Sven Koenig | 31 | 1 | planning_mapf_navigation;warehouse_amr_logistics;optimization_mpc;robustness_safety_resilience;graph_network_topology |
| Frank Allgöwer | 30 | 0 | graph_network_topology;distributed_control_consensus;communication_constraints;robustness_safety_resilience;optimization_mpc |
| Vijay Kumar | 30 | 1 | graph_network_topology;communication_constraints;robustness_safety_resilience;learning_marl_gnn;optimization_mpc |
| Amanda Prorok | 29 | 0 | learning_marl_gnn;planning_mapf_navigation;communication_constraints;graph_network_topology;robustness_safety_resilience |
| Magnus Egerstedt | 28 | 1 | robustness_safety_resilience;communication_constraints;distributed_control_consensus;graph_network_topology;optimization_mpc |
| Pratap Tokekar | 28 | 1 | communication_constraints;planning_mapf_navigation;robustness_safety_resilience;graph_network_topology;learning_marl_gnn |
| Manuel Mazo | 28 | 0 | distributed_control_consensus;communication_constraints;graph_network_topology;robustness_safety_resilience;optimization_mpc |
| Daniel E. Quevedo | 27 | 1 | graph_network_topology;distributed_control_consensus;communication_constraints;robustness_safety_resilience;optimization_mpc |
| Jiaoyang Li | 27 | 0 | planning_mapf_navigation;warehouse_amr_logistics;optimization_mpc;graph_network_topology;robustness_safety_resilience |
| Sandra Hirche | 26 | 1 | distributed_control_consensus;graph_network_topology;communication_constraints;robustness_safety_resilience;optimization_mpc |
| Ramviyas Parasuraman | 26 | 3 | planning_mapf_navigation;communication_constraints;graph_network_topology;distributed_control_consensus;robustness_safety_resilience |

## Evidence gaps

1. Integrated allocation-control gap: many papers solve assignment, consensus, or formation separately; fewer close the loop from allocation pressure to integer coalition closure and physical load feasibility.
2. Physical feasibility gap: MRTA and market papers often do not model payload wrench, contact geometry, or rigid formation constraints.
3. Communication realism gap: many distributed methods assume graph connectivity conditions that are cleaner than warehouse communication degradation.
4. Evaluation gap: real-robot and open-source validations are present but much less frequent than simulations and theoretical demonstrations.
5. Reproducibility gap: several papers report algorithms without enough code/data availability to support benchmark-level comparison.
6. Learning-structure gap: learning methods scale well in some settings, but often require structured priors or retraining to transfer across robot count, object count, and payload distributions.

## Implications for the TFM

The review supports positioning Smith-QR as a layered distributed coordination architecture. Its most defensible novelty is not simply using distributed control or game dynamics, but integrating: allocation pressure, coalition closure, quorum feasibility, formation/contact constraints, and robustness evaluation under communication and resource degradation.

The strongest comparison baselines should come from: CBBA/consensus bundle allocation, decentralized or distributed control, MARL/graph-learning transport policies, centralized or mixed-integer allocation/planning, and classic greedy warehouse dispatching.

The thesis should avoid claiming that game theory alone solves cooperative transport. A stronger claim is that population/game dynamics provide an interpretable allocation layer that becomes useful when coupled to graph/quorum and physical feasibility mechanisms.

## Limitations of this draft

This document is generated from an arXiv-first local corpus. It is not yet a final PRISMA-complete review because IEEE Xplore, ACM Digital Library, Scopus/Web of Science, and backward/forward citation chasing have not been integrated. The candidate screening is a transparent keyword-based triage aid, not a substitute for final reviewer decisions. Full-text extraction was limited to high-priority records and to the first pages of each PDF.

## Generated artifacts

- `output/literature/arxiv_full/review/evidence_map_high_priority.csv`
- `output/literature/arxiv_full/review/concept_counts_all.csv`
- `output/literature/arxiv_full/review/concept_counts_high_priority.csv`
- `output/literature/arxiv_full/review/trend_by_year.csv`
- `output/literature/arxiv_full/review/author_productivity.csv`
- `output/literature/arxiv_full/review/key_studies.csv`
