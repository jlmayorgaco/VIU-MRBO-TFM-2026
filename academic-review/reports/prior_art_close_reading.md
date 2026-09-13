# Bounded close reading of nearest prior art

This artifact records an agent close reading of 16 candidates selected from the Stage 3 full-text evidence matrix. It is a bounded evidence ledger, not a systematic novelty proof and not a substitute for the author's final verification before manuscript use.

Source matrix: `academic-review/data/processed/fulltext_evidence_matrix.csv`.
Each row keeps the local source path and SHA-256 recorded by Stage 3. Publisher previews and abstract-only pages are explicitly marked as access-limited; their claims must not be expanded into detailed method or performance statements.

## Axis coverage in this bounded set

| Axis recorded in reading notes | Candidates |
|---|---:|
| SP1 centralized allocation baseline | 1 |
| SP1 coalition formation | 1 |
| SP1 decentralized allocation | 1 |
| SP1 distributed allocation | 1 |
| SP1 dynamic heterogeneous allocation | 1 |
| SP1 dynamic task exchange | 1 |
| SP1 group formation | 1 |
| SP1 heterogeneous coalition formation | 1 |
| SP1 heterogeneous task allocation | 1 |
| SP1 recruitment | 1 |
| SP1 team allocation/cooperation | 1 |
| SP2 contact/caging | 1 |
| SP2 cooperative rigid-payload transport | 1 |
| SP2 execution | 1 |
| SP2 failure signal | 1 |
| ability/history relevance | 1 |
| anytime optimization | 1 |
| auction/consensus | 1 |
| changing teams | 1 |
| communication efficiency | 1 |
| communication/computation assumptions | 1 |
| communication/deadlock concerns | 1 |
| cross-cutting distributed communication | 1 |
| cross-cutting taxonomy | 1 |
| decentralized threshold control | 1 |
| distributed object-closure test | 1 |
| event triggering | 1 |
| failure-robustness signal | 1 |
| formal safety/security boundary | 1 |
| formation | 1 |
| group-size effects | 1 |
| heterogeneous sensing | 1 |
| inter-robot communication | 1 |
| local accommodation | 1 |
| local communication | 1 |
| local consensus | 1 |
| messages/makespan | 1 |
| navigation abstraction | 1 |
| nonholonomic kinematics | 1 |
| obstacle avoidance | 1 |
| path planning | 1 |
| response thresholds | 1 |
| scalability claim | 1 |
| skills | 1 |
| spatial/temporal constraints | 1 |
| specialization/respecialization | 1 |
| temporal constraints | 1 |
| topology | 1 |
| weak communication | 1 |

The most direct physical precedent in this set is cooperative rigid-payload transport by nonholonomic mobile manipulators (C82AC458AF2EC), while the closest allocation precedents are heterogeneous coalition matching (C96F294D621AC), constrained coalition formation (C06C41AFDC1F1), local recruitment (C806A699E9EBB), and distributed allocation/consensus (C20FBE73D7292, CB157C72BD65E). These sources address different layers; the bounded reading did not verify an integrated SP1-SP3 mechanism combining heterogeneous coalition selection, mechanical contact/wrench feasibility, carried-load traffic, and failure replacement.

That last sentence is a bounded-review result: it means the integration was not established by these 16 close readings, not that no such work exists anywhere. The WoS export remains pending because the available session requires institutional authentication.

## Candidate-level reading notes

| ID | Source | TFM axis | Confidence | Allowed use |
|---|---|---|---|---|
| `CDE40EBBE4028` | [ZhiDong Wang; Yasuhisa Hirata; Kazuhiro Kosuge (2005)](https://doi.org/10.1299/jsmermd.2005.124_4)<br>1P2-S-030 Designing An Algorithm for Testing Object Caging Condition by Multiple Mobile Robots(Cooperation Control of Multi Robot,Mega-Integration in Robotics and Mechatronics to Assist Our Daily Lives) | SP2 contact/caging; distributed object-closure test; formation | medium | SP2 contact/caging prior art and a bounded motivation for explicit mechanical feasibility checks; do not use as evidence for integrated transport. |
| `C20FBE73D7292` | [Farouq Zitouni; Saad Harous; Ramdane Maamri (2020)](https://doi.org/10.1109/access.2020.2971585)<br>A Distributed Approach to the Multi-Robot Task Allocation Problem Using the Consensus-Based Bundle Algorithm and Ant Colony System | SP1 distributed allocation; local consensus; messages/makespan; navigation abstraction | high | SP1 distributed-allocation comparator and communication/makespan metric precedent; not a mechanical-transport baseline. |
| `CB157C72BD65E` | [Gautham P. Das; T.M. McGinnity; Sonya Coleman; Laxmidhar Behera (2014)](https://doi.org/10.1007/s10846-014-0154-2)<br>A Distributed Task Allocation Algorithm for a Multi-Robot System in Healthcare Facilities | SP1 heterogeneous task allocation; auction/consensus; inter-robot communication | medium | SP1 literature context for distributed auction/consensus; cite only abstract-level claims until the author verifies the full text. |
| `CDEDC925F7B23` | [Yanyan Han; Deshi Li; Jian Chen; Xiangguo Yang; Yuxi Hu; Guangmin Zhang (2010)](https://doi.org/10.22266/ijies2010.0630.05)<br>A Multi-Robots Task Allocation Algorithm Based on Relevance and Ability With Group Collaboration | SP1 group formation; ability/history relevance; SP2 failure signal | medium | SP1 group-formation and failure-reconfiguration precedent; use the rescue description as a signal, not as evidence of equivalent recovery performance. |
| `CDB55CB433AE2` | [Yichao Wang; Chunjiang Wang; Shuangyin Ren (2025)](https://doi.org/10.3390/s25216738)<br>A Two-Level Clustered Consensus-Based Bundle Algorithm for Dynamic Heterogeneous Multi-UAV Multi-Task Allocation | SP1 dynamic heterogeneous allocation; topology; communication efficiency | medium | SP1 communication/topology and dynamic-allocation context; potential comparator for message/runtime measures, not for mechanics. |
| `C23A9081289BD` | [Rik Bahnemann; Dominik Schindler; Mina Kamel; Roland Siegwart; Juan Nieto (2017)](https://doi.org/10.1109/ssrr.2017.8088150)<br>A decentralized multi-agent unmanned aerial system to search, pick up, and relocate objects | SP2 execution; local communication; obstacle avoidance; failure-robustness signal | high | SP2 decentralized execution and communication/avoidance context; useful negative boundary for independent pickup versus cooperative payload transport. |
| `C82AC458AF2EC` | [M. Abou-Samah; C. P. Tang; R. M. Bhatt; V. Krovi (2006)](https://doi.org/10.1007/s10514-005-9717-9)<br>A kinematically compatible framework for cooperative payload transport by nonholonomic mobile manipulators | SP2 cooperative rigid-payload transport; nonholonomic kinematics; local accommodation | medium | Primary SP2 physical-transport precedent and motivation for explicit kinematic/contact constraints; verify full article before detailed comparison. |
| `C96F294D621AC` | [Ashish Verma; Avinash Gautam; Ayan Dutta; Virendra Singh Shekhawat; Sudeept Mohan (2025)](https://doi.org/10.1007/s10846-025-02287-4)<br>CF-HMRTA: Coalition Formation for Heterogeneous Multi-Robot Task Allocation | SP1 heterogeneous coalition formation; skills; temporal constraints; scalability claim | high | Closest SP1 coalition-formation comparator; use to position capability/constraint matching, while preserving the TFM distinction between strategic feasibility and mechanical feasibility. |
| `C806A699E9EBB` | [Michael J. B. Krieger; Jean-Bernard Billeter; Laurent Keller (2000)](https://doi.org/10.1038/35023164)<br>Ant-like task allocation and recruitment in cooperative robots | SP1 recruitment; decentralized threshold control; group-size effects | high | Foundational SP1 recruitment precedent and motivation for threshold-based local decisions; not a direct baseline for heterogeneous rigid-load transport. |
| `C06C41AFDC1F1` | [Luca Capezzuto; Danesh Tarapore; Sarvapali D. Ramchurn (2020)](https://doi.org/10.1007/978-3-030-66412-1_38)<br>Anytime and Efficient Coalition Formation with Spatial and Temporal Constraints | SP1 coalition formation; spatial/temporal constraints; anytime optimization | medium | SP1 constrained-coalition background and possible central formulation comparator; do not conflate allocation feasibility with mechanical feasibility. |
| `C740E1AD4CDC9` | [Huizhen Yang; Jie Yang; Qiang Wang; Junfeng Fan; Yuchen Lin (2026)](https://doi.org/10.1007/s00500-025-10894-4)<br>A distributed PI-based dynamic task allocation method for multi-AUV systems | SP1 dynamic task exchange; weak communication; changing teams | low | SP1 dynamic-task and weak-communication context only; verify full text before detailed methodological comparison. |
| `CADFC0AC6330F` | [Tohid Kargar Tasooji; Horacio J. Marquez (2022)](https://doi.org/10.1109/access.2022.3227076)<br>A Secure Decentralized Event-Triggered Cooperative Localization in Multi-Robot Systems Under Cyber Attack | cross-cutting distributed communication; event triggering; formal safety/security boundary | high | Communication/event-triggering and formal-evidence contrast; useful to keep localization guarantees separate from allocation and mechanics claims. |
| `CD0C4805D863E` | [Gregory Dudek; Michael Jenkin; Evangelos Milios; D. Wilkes (1996)](https://doi.org/10.1007/bf00240651)<br>A taxonomy for multi-agent robotics | cross-cutting taxonomy; communication/computation assumptions | low | Terminology and information-assumption framing only. |
| `CEA1C303255D1` | [Sajal Chandra Banik; Keigo Watanabe; Maki K. Habib; Kiyotaka Izumi (2008)](https://doi.org/10.1007/978-3-540-69033-7_17)<br>Affection Based Multi-robot Team Work | SP1 team allocation/cooperation; communication/deadlock concerns | low | Historical/background context only; no strong claim without author verification of the full chapter. |
| `C6F55B57AF2A5` | [Vera A. Kazakova; Gita Sukthankar (2020)](https://doi.org/10.1017/s0269888920000235)<br>Adaptable and stable decentralized task allocation for hierarchical domains | SP1 decentralized allocation; specialization/respecialization; response thresholds | low | Candidate background reference; do not use for detailed novelty or quantitative comparisons until full text is verified. |
| `C58FD63E3F184` | [Hamza Chakraa; Edouard Leclercq; F. Guérin; Dimitri Lefebvre (2023)](https://doi.org/10.1109/access.2023.3315130)<br>A Centralized Task Allocation Algorithm for a Multi-Robot Inspection Mission With Sensing Specifications | SP1 centralized allocation baseline; heterogeneous sensing; path planning | high | SP1 centralized/oracle baseline context and a clear example of why single-robot assignment is insufficient for the TFM coalition problem. |

## Reading discipline

- `what_source_supports` is the strongest statement permitted by the inspected local evidence.
- `what_source_does_not_support` is a guard against transferring allocation, localization, or abstract-level claims into mechanics or end-to-end transport.
- Every row has `human_verification_required=true` because the final author must inspect the cited passage and decide whether it is appropriate for the VIU memory.
- No claim in this ledger is a new TFM result, and no manuscript chapter was modified.
