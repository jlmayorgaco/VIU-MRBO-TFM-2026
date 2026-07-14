# Stage 2.5 fresh citation audit — batch C

**Date:** 2026-07-14  
**Declared inputs:** references.bib and .aris/citation-audit/contexts.txt  
**Scope:** the 35 assigned keys only. Earlier CITATION_AUDIT outputs were not used as evidence.  
**Method:** fresh exact-title, DOI, arXiv-ID, and site-restricted web queries. Metadata was checked against publisher pages, IEEE proceedings/Xplore, arXiv, official institutional or author repositories, and manufacturer/standards-owner pages. Crossref was queried independently for every claimed DOI as a registry corroboration. No bibliography or manuscript files were edited.

## Result

| Verdict | Count |
|---|---:|
| KEEP | 33 |
| FIX | 2 |
| REPLACE | 0 |
| REMOVE | 0 |

- Existence: **35 YES**, 0 NO, 0 UNCERTAIN.
- Metadata/identifier: **33 correct**, **2 need correction**.
- Context: 20 cited keys, 30 recorded uses: **30 SUPPORTS**, 0 WEAK, 0 WRONG. The remaining 15 keys are uncited (N/A).
- Blockers: **none**. This batch is a metadata warning only; it contains no existence or wrong-context failure.

## Required metadata fixes

1. **omronRobotics2026** — the official OMRON page is live and its title, organization, URL, and product data are valid, but it exposes no publication/update date. The current year = {2026} is therefore an access-year inference already represented by urldate, not verified publication metadata. Remove year or replace it only if OMRON supplies a dated version record; retain urldate.
2. **villani2009optimal** — add the canonical Springer DOI **10.1007/978-3-540-71050-9**. Author, combined title/subtitle, series, volume, publisher, and bibliographic year 2009 are correct.

## Per-key ledger

Axes are E = existence, M = metadata, I = DOI/URL/eprint identity, and C = every current included-paper context in contexts.txt. “Correct” means that the fields currently present agree with the canonical record.

| Key | E | M | I | C (all recorded uses) | Verdict |
|---|---|---|---|---|---|
| olfati2004consensus | YES | Correct: Olfati-Saber and Murray; IEEE TAC 49(9), 1520–1533 (2004) | DOI correct | 05-theoretical-framework/index.tex:19 SUPPORTS the consensus/networked distributed-control literature block | KEEP |
| olfati2007consensus | YES | Correct: three authors; Proceedings of the IEEE 95(1), 215–233 (2007) | DOI correct | 05-theoretical-framework/index.tex:19 SUPPORTS the consensus/networked distributed-control literature block | KEEP |
| omronRobotics2026 | YES | **Unverified year**; organization and live page title are correct | Official URL correct and live | 05-theoretical-framework/index.tex:401 SUPPORTS: the official comparison lists LD, MD, and HD families and HD-1500 at 1500 kg | **FIX** |
| ortega2002interconnection | YES | Correct: four authors; Automatica 38(4), 585–596 (2002) | DOI correct | N/A | KEEP |
| ottoFleet2026 | YES | Correct conservative web record: organization/title; no unsupported publication year is asserted | Official URL correct and live | 05-theoretical-framework/index.tex:397 SUPPORTS: Fleet Manager explicitly manages traffic and scales from five to 100 AMRs | KEEP |
| paul2023collective | YES | Correct: six authors; ICRA 2023, 5779–5785 | DOI correct | 05-theoretical-framework/index.tex:352 SUPPORTS: MRTA-collective transport includes workloads/deadlines, flight and communication range, payload constraints, GNNs, and topological descriptors | KEEP |
| qiu2024cbpa | YES | Correct: five authors; CAC 2024, 5294–5299 | DOI and arXiv:2412.10087 correct | 05-theoretical-framework/index.tex:370 SUPPORTS: CBPA extends CBBA using payload-assignment matrices exchanged in consensus | KEEP |
| quijano2017population | YES | Correct: six authors; IEEE Control Systems Magazine 37(1), 70–97 (2017) | DOI correct | 01-introduction.tex:20; 05-theoretical-framework/index.tex:20,167 SUPPORT population games, evolutionary dynamics, distributed control, and aggregate strategy mass | KEEP |
| rahwan2015coalition | YES | Correct: four authors; Artificial Intelligence 229, 139–174 (2015) | DOI correct | 01-introduction.tex:16 SUPPORTS coalition-structure generation and its combinatorial search/constraint abstraction | KEEP |
| ren2008distributed | YES | Correct: Ren and Beard; Springer monograph, copyright/bibliographic year 2008 | DOI correct | 05-theoretical-framework/index.tex:19 SUPPORTS distributed consensus in cooperative multi-vehicle control | KEEP |
| rimon1992exact | YES | Correct: Rimon and Koditschek; IEEE TRA 8(5), 501–518 (1992) | DOI correct | 05-theoretical-framework/index.tex:236 SUPPORTS navigation functions that avoid spurious minima under explicit geometric hypotheses | KEEP |
| rohmer2013vrep | YES | Correct: Rohmer, Singh, Freese; IROS 2013, 1321–1326 | DOI correct | N/A | KEEP |
| rosenfelder2024force | YES | Correct issue citation: Robotica 42(2), 611–624 (2024); first published online 18 Dec 2023 | DOI correct | N/A | KEEP |
| sandholm1999coalition | YES | Correct: five authors; Artificial Intelligence 111(1–2), 209–238 (1999) | DOI correct | 01-introduction.tex:16 SUPPORTS coalition-structure search complexity and worst-case guarantees | KEEP |
| sandholm2010population | YES | Correct: William H. Sandholm; MIT Press, 2010 | Official publisher record/ISBN verified; no book DOI found | 01-introduction.tex:20; 05-theoretical-framework/index.tex:20,167 SUPPORT the population-game representation, payoffs, equilibria, and aggregate mass dynamics | KEEP |
| sandryhaila2013dsp | YES | Correct: Sandryhaila and Moura; IEEE TSP 61(7), 1644–1656 (2013) | DOI and arXiv:1210.4752 correct | N/A | KEEP |
| sandryhaila2014frequency | YES | Correct: Sandryhaila and Moura; IEEE TSP 62(12), 3042–3054 (2014) | DOI and arXiv:1307.0468 correct | N/A | KEEP |
| shan2024distributed | YES | Correct: four authors; Robotics and Autonomous Systems 178:104722 (2024) | DOI correct | N/A | KEEP |
| shibata2022learning | YES | Correct: five authors, title, arXiv submission year 2022 | arXiv:2212.02692 correct | 05-theoretical-framework/index.tex:361 SUPPORTS unknown object weights, global priorities/communication, distributed policy, and variable robot/object counts | KEEP |
| shibata2023event | YES | Correct: three authors; Robotics and Autonomous Systems 159:104307 (2023) | DOI and arXiv:2212.01958 correct | N/A | KEEP |
| shida2024infeasible | YES | Correct final publication: four authors; SII 2025, 1548–1555 | DOI correct; arXiv:2404.11817 is the 2024 preprint | 05-theoretical-framework/index.tex:364 SUPPORTS infeasible/untransportable tasks and deadlock avoidance | KEEP |
| shmoys1993generalized | YES | Correct: Shmoys and Tardos; Mathematical Programming 62, 461–474 (1993) | DOI correct | N/A | KEEP |
| tabuada2007event | YES | Correct: Paulo Tabuada; IEEE TAC 52(9), 1680–1685 (2007) | DOI correct | N/A | KEEP |
| theraulaz1999stigmergy | YES | Correct: Theraulaz and Bonabeau; Artificial Life 5(2), 97–116 (1999) | DOI correct | N/A | KEEP |
| tuci2018cooperative | YES | Correct: three authors; Frontiers in Robotics and AI 5:59 (2018) | DOI correct | 01-introduction.tex:7,18; 05-theoretical-framework/index.tex:22,273 SUPPORT cooperative transport, pushing/grasping/caging diversity, information/communication choices, and frequent fixed-team/contact assumptions | KEEP |
| vanderschraft2017l2gain | YES | Correct: Arjan van der Schaft; third edition, Springer, 2017 | DOI correct | N/A | KEEP |
| vda2026vda5050 | YES | Correct: VDA/VDMA, Version 3.0.0, 17 March 2026 | Official publication URL/PDF correct | N/A | KEEP |
| verginis2018communication | YES | Correct: three authors; ECC 2018, 733–738 | DOI correct | N/A | KEEP |
| vickrey1961counterspeculation | YES | Correct: William Vickrey; Journal of Finance 16(1), 8–37 (1961) | DOI correct | N/A | KEEP |
| villani2009optimal | YES | Correct author/title/series/volume/publisher/year | **Canonical DOI missing: 10.1007/978-3-540-71050-9** | N/A | **FIX** |
| wurman2008coordinating | YES | Correct: Wurman, D’Andrea, Mountz; AI Magazine 29(1), 9–19 (2008) | AAAI DOI correct | 01-introduction.tex:5 and 05-theoretical-framework/index.tex:21 SUPPORT Kiva’s mobile shelves, fixed workstations, large fleets, and centralized warehouse coordination | KEEP |
| yi2019operator | YES | Correct: Peng Yi and Lacra Pavel; Automatica 102, 111–121 (2019) | DOI correct | 06-results-and-analysis/sp4-motion.tex:106 SUPPORTS v-GNE computation with a globally shared affine constraint and primal–dual/shared-multiplier characterization | KEEP |
| zhang2024coalition | YES | Correct: five authors; IROS 2024, 3439–3446 | DOI correct | 05-theoretical-framework/index.tex:140 SUPPORTS heterogeneous coalitions under multiple finite resource constraints | KEEP |
| zhou2026cttapf | YES | Correct: Zhou, Bode, Hunt; 2026 | arXiv:2605.16097 correct | 05-theoretical-framework/index.tex:356 SUPPORTS integrated team formation, task assignment, and collision-free path finding in CT-TAPF | KEEP |
| zhuang2026safe | YES | Correct: Zhuang, Huang, Yang; 2026 | arXiv:2603.06356 correct | 05-theoretical-framework/index.tex:383 SUPPORTS consensus, safety, event-triggered CBFs, reduced communication, and cooperative manipulation | KEEP |

## Fresh lookup log

Each row records the actual query pattern and the strongest primary/official supporting URL used. DOI records were also independently re-queried through Crossref by exact DOI.

| Key | Fresh query | Primary/official evidence |
|---|---|---|
| olfati2004consensus | "Consensus Problems in Networks of Agents with Switching Topology and Time-Delays" 10.1109/TAC.2004.834113 | [IEEE DOI](https://doi.org/10.1109/TAC.2004.834113) |
| olfati2007consensus | "Consensus and Cooperation in Networked Multi-Agent Systems" 10.1109/JPROC.2006.887293 | [IEEE DOI](https://doi.org/10.1109/JPROC.2006.887293) |
| omronRobotics2026 | site:automation.omron.com LD Series Autonomous Mobile Robots 1500 kg | [OMRON Robotics](https://robotics.omron.com/products/mobile-robots/ld-series/) |
| ortega2002interconnection | "Interconnection and damping assignment passivity-based control of port-controlled Hamiltonian systems" | [Elsevier](https://www.sciencedirect.com/science/article/pii/S0005109801002783) |
| ottoFleet2026 | site:ottomotors.com fleet manager traffic large fleets | [OTTO Fleet Manager](https://ottomotors.com/fleet-manager/) |
| paul2023collective | "Efficient Planning of Multi-Robot Collective Transport" DOI | [arXiv](https://arxiv.org/abs/2303.08933); [IEEE DOI](https://doi.org/10.1109/ICRA48891.2023.10161517) |
| qiu2024cbpa | "Consensus-Based Dynamic Task Allocation for Multi-Robot System Considering Payloads Consumption" DOI | [arXiv](https://arxiv.org/abs/2412.10087); [IEEE Xplore](https://ieeexplore.ieee.org/document/10865375/) |
| quijano2017population | "The Role of Population Games and Evolutionary Dynamics in Distributed Control Systems" DOI | [UPC institutional record](https://www.iri.upc.edu/publications/show/1783); [IEEE DOI](https://doi.org/10.1109/MCS.2016.2621479) |
| rahwan2015coalition | site:sciencedirect.com "Coalition structure generation: A survey" | [Elsevier](https://www.sciencedirect.com/science/article/pii/S0004370215001198) |
| ren2008distributed | site:springer.com "Distributed Consensus in Multi-vehicle Cooperative Control" | [Springer](https://link.springer.com/book/10.1007/978-1-84800-015-5) |
| rimon1992exact | "Exact Robot Navigation Using Artificial Potential Functions" 10.1109/70.163777 | [Technion institutional record](https://cris.technion.ac.il/en/publications/exact-robot-navigation-using-artificial-potential-functions-2/); [IEEE DOI](https://doi.org/10.1109/70.163777) |
| rohmer2013vrep | "V-REP: A versatile and scalable robot simulation framework" DOI | [Coppelia Robotics](https://www.coppeliarobotics.com/research); [IEEE DOI](https://doi.org/10.1109/IROS.2013.6696520) |
| rosenfelder2024force | site:cambridge.org/core/journals/robotica "Force-Based Organization and Control Scheme" | [Cambridge Core](https://www.cambridge.org/core/journals/robotica/article/forcebased-organization-and-control-scheme-for-the-nonprehensile-cooperative-transportation-of-objects/DE6BDFEAB8548EB96C2FFB186AF12B65) |
| sandholm1999coalition | site:sciencedirect.com "Coalition structure generation with worst case guarantees" | [Elsevier](https://www.sciencedirect.com/science/article/pii/S0004370299000363) |
| sandholm2010population | site:mitpress.mit.edu "Population Games and Evolutionary Dynamics" | [MIT Press](https://mitpress.mit.edu/9780262195874/population-games-and-evolutionary-dynamics/) |
| sandryhaila2013dsp | "Discrete Signal Processing on Graphs" 10.1109/TSP.2013.2238935 | [arXiv](https://arxiv.org/abs/1210.4752); [author’s CMU publication list](https://users.ece.cmu.edu/~asandryh/publications.html) |
| sandryhaila2014frequency | "Discrete Signal Processing on Graphs: Frequency Analysis" 10.1109/TSP.2014.2321121 | [arXiv](https://arxiv.org/abs/1307.0468); [author’s CMU publication list](https://users.ece.cmu.edu/~asandryh/publications.html) |
| shan2024distributed | site:sciencedirect.com "A Distributed Multi-Robot Task Allocation Method for Time-Constrained Dynamic Collective Transport" | [Elsevier](https://www.sciencedirect.com/science/article/pii/S0921889024001052) |
| shibata2022learning | site:arxiv.org "Learning Locally, Communicating Globally" cooperative transport | [arXiv](https://arxiv.org/abs/2212.02692) |
| shibata2023event | "10.1016/j.robot.2022.104307" | [Elsevier](https://www.sciencedirect.com/science/article/pii/S0921889022001968); [arXiv](https://arxiv.org/abs/2212.01958) |
| shida2024infeasible | "Reinforcement Learning of Multi-Robot Task Allocation for Multi-Object Transportation with Infeasible Tasks" | [IEEE Xplore](https://ieeexplore.ieee.org/document/10870902/); [arXiv](https://arxiv.org/abs/2404.11817) |
| shmoys1993generalized | "An Approximation Algorithm for the Generalized Assignment Problem" 10.1007/BF01585178 | [Cornell author-hosted paper](https://www.cs.cornell.edu/people/eva/Approx.Algorithm.Generalized.Assignment.Prob.pdf); [Springer DOI](https://doi.org/10.1007/BF01585178) |
| tabuada2007event | "Event-Triggered Real-Time Scheduling of Stabilizing Control Tasks" DOI | [IEEE Xplore](https://ieeexplore.ieee.org/document/4303247); [IEEE DOI](https://doi.org/10.1109/TAC.2007.904277) |
| theraulaz1999stigmergy | site:direct.mit.edu/artl "A Brief History of Stigmergy" | [MIT Press](https://direct.mit.edu/artl/article/5/2/97/2318/A-Brief-History-of-Stigmergy) |
| tuci2018cooperative | site:frontiersin.org "Cooperative Object Transport in Multi-Robot Systems" | [Frontiers](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2018.00059/full) |
| vanderschraft2017l2gain | site:springer.com "L2-Gain and Passivity Techniques in Nonlinear Control" third edition | [Springer](https://link.springer.com/book/10.1007/978-3-319-49992-5) |
| vda2026vda5050 | site:vda.de "VDA 5050" "3.0.0" | [VDA publication](https://www.vda.de/en/news/publications/publication/vda-5050); [official PDF](https://www.vda.de/dam/jcr%3A09f03b91-13e2-4db3-bf30-4f221710071b/VDA5050_EN.pdf) |
| verginis2018communication | "10.23919/ECC.2018.8550305" | [KTH institutional record](https://kth.diva-portal.org/smash/record.jsf?pid=diva2%3A1281027); [IEEE DOI](https://doi.org/10.23919/ECC.2018.8550305) |
| vickrey1961counterspeculation | site:onlinelibrary.wiley.com "Counterspeculation, Auctions, and Competitive Sealed Tenders" | [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1961.tb02789.x) |
| villani2009optimal | site:springer.com "Optimal Transport: Old and New" Villani 2009 | [Springer](https://link.springer.com/book/10.1007/978-3-540-71050-9) |
| wurman2008coordinating | site:ojs.aaai.org/aimagazine "Coordinating Hundreds of Cooperative Autonomous Vehicles in Warehouses" | [AI Magazine / AAAI](https://ojs.aaai.org/aimagazine/index.php/aimagazine/article/view/2082/0) |
| yi2019operator | site:sciencedirect.com "An Operator Splitting Approach for Distributed Generalized Nash Equilibria Computation" | [Elsevier](https://www.sciencedirect.com/science/article/pii/S0005109819300081) |
| zhang2024coalition | "10.1109/IROS58592.2024.10801429" | [IEEE Xplore](https://ieeexplore.ieee.org/document/10801429/); [IROS proceedings TOC](https://www.proceedings.com/content/077/077922webtoc.pdf) |
| zhou2026cttapf | arXiv 2605.16097 | [arXiv](https://arxiv.org/abs/2605.16097) |
| zhuang2026safe | arXiv 2603.06356 "Safe Consensus of Cooperative Manipulation" | [arXiv](https://arxiv.org/abs/2603.06356) |

## Context cautions and non-errors

- The Sandholm (1999) and Rahwan (2015) citations directly support coalition-structure generation and its combinatorial/constraint abstraction. The manuscript’s later wrench/geometric-feasibility observation is a synthesis by the thesis; it should not be rewritten as a theorem proved by those sources.
- Rosenfelder et al. was first published online in December 2023 but belongs to Robotica volume 42, issue 2 (2024). The current year 2024 is the correct issue citation and is not metadata drift.
- The key shida2024infeasible reflects the 2024 arXiv preprint; the entry correctly cites the final SII 2025 publication. A key name is not rendered bibliographic metadata and needs no change.
- The OMRON context remains fully supported despite the metadata FIX: the live official page’s comparison table includes LD, MD, and HD-1500 and states the 1500 kg maximum.
- IEEE Xplore returned JavaScript/robot interstitials for some recent records. This was not a blocker because exact DOI metadata, official proceedings tables of contents, and the corresponding arXiv primary records independently agreed.

## Disposition

All 35 works/pages exist. No citation in batch C should be replaced or removed, and no included-paper use is unsupported. Apply only the two metadata corrections above, then re-run this batch against the changed references.bib to close the warning.
