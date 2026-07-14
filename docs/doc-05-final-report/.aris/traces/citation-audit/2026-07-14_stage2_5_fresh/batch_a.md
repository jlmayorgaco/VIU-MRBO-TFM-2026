# Stage 2.5 fresh citation audit — batch A

**Date:** 2026-07-14  
**Input:** `references.bib` and current included-paper uses in `.aris/citation-audit/contexts.txt`  
**Keys audited:** 36  
**Independence:** prior `CITATION_AUDIT*` outputs were not used as evidence. Each entry was checked afresh against a publisher, DOI registry/resolver, official proceedings, arXiv, SSRN, or the cited organization's own page.

## Summary

| Verdict | Count |
|---|---:|
| KEEP | 30 |
| FIX | 6 |
| REPLACE | 0 |
| REMOVE | 0 |

- Existence: **36 YES**, 0 NO, 0 UNCERTAIN.
- Metadata: **30 clean**, **6 need correction/completion**.
- Context: 16 keys are used in the included paper, for **23 uses**: **21 SUPPORTS**, **2 WEAK**, **0 WRONG**. The other 20 keys have context `N/A`.
- No hallucinated DOI, title, venue, or paper was found. No blocker prevented online verification.
- `WEAK` does not mean contradictory: both weak uses are broad synthesis claims supported only indirectly by the cited review and should be tightened or backed by a coalition-formation source.

Axis notation below is `E` = existence, `M` = metadata/identifier, `C` = context. `P` means pass.

## Per-key evidence and verdicts

| Key | Verdict | Axes | Recorded lookup query → supporting source | Finding / action |
|---|---|---|---|---|
| `agilox2026` | **FIX** | E=YES; M=FIX; C=SUPPORTS(1) | `site:agilox.net/en X-SWARM master computer` → [AGILOX official product page](https://www.agilox.net/en/) | Corporate author, title and URL are valid; the undated product page explicitly says X-SWARM makes a master computer superfluous. `year={2026}` is not evidenced as a publication year. Remove the year and retain `urldate`, or cite a dated 2026 AGILOX document instead. |
| `amazon2025millionRobots` | **KEEP** | E=YES; M=P; C=N/A | `site:aboutamazon.com amazon million robots Scott Dresser June 30 2025` → [Amazon official article](https://www.aboutamazon.com/news/operations/amazon-million-robots-ai-foundation-model) | Exact title, Scott Dresser, 30 June 2025 and URL verified. |
| `amazon2026robotsFulfillment` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `"Amazon uses robots that sort, lift, and carry packages" "June 4, 2026"` → [Amazon official article](https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center) | Exact title and Tyler Greenawalt verified; Amazon's own tag index dates the page 4 June 2026. The page directly describes robots moving inventory to storage and picking stations. |
| `ames2017cbf` | **KEEP** | E=YES; M=P; C=SUPPORTS(2) | `10.1109/TAC.2016.2638961 Control Barrier Function Based Quadratic Programs` → [DOI](https://doi.org/10.1109/TAC.2016.2638961), [author preprint](https://arxiv.org/abs/1609.06408) | Authors, title, IEEE TAC 62(8), 3861–3876 (2017), and DOI match. The paper establishes input inequalities and forward invariance under stated hypotheses. |
| `an2023cooperative` | **KEEP** | E=YES; M=P; C=SUPPORTS(2) | `10.1109/OJCS.2023.3238324 cooperative object transport` → [IEEE Xplore](https://ieeexplore.ieee.org/document/10023955) | Six authors, title, IEEE OJCS 4, 23–36 (2023), and DOI match. The review directly covers cooperative object transport, platforms, communication, control approaches and challenges. |
| `azadeh2019warehouse` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `10.1287/trsc.2018.0873 Robotized Automated Warehouse Systems` → [INFORMS article](https://pubsonline.informs.org/doi/10.1287/trsc.2018.0873) | Exact three authors, title, Transportation Science 53(4), 917–945 (2019), and DOI verified. It is explicitly a review of robotized and automated warehouse systems. |
| `aziz2021complexity` | **FIX** | E=YES; M=FIX; C=N/A | `"Multi-Robot Task Allocation—Complexity and Approximation" AAMAS 2021` → [official AAMAS paper](https://aamas.csc.liv.ac.uk/Proceedings/aamas2021/pdfs/p133.pdf), [DOI](https://doi.org/10.5555/3463952.3463974) | Authors, title, AAMAS 2021 and pages 133–141 are correct. Add the canonical DOI `10.5555/3463952.3463974` (currently omitted). |
| `barreiro2017distributed` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `10.1109/TSMC.2016.2523934` → [DOI/IEEE](https://doi.org/10.1109/TSMC.2016.2523934), [author manuscript](https://upcommons.upc.edu/bitstream/handle/2117/104264/1716-Distributed-Population-Dynamics_-Optimization-and-Control-Applications.pdf) | The DOI, authors, final 2017 volume 47(2), pages 304–314 and title match. It develops distributed population dynamics on non-complete information graphs for optimization/control applications. |
| `barreiro2021uav` | **KEEP** | E=YES; M=P; C=N/A | `10.1016/j.jfranklin.2021.05.002` → [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0016003221002878) | Seven authors, title, JFI 358(10), 5334–5352 (2021), and DOI verified. |
| `benaim2003deterministic` | **KEEP** | E=YES; M=P; C=N/A | `10.1111/1468-0262.00429` → [Wiley/Econometrica](https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00429) | Title, Benaïm and Weibull, Econometrica 71(3), 873–903 (2003), and DOI match. |
| `bezerra2025learning` | **KEEP** | E=YES; M=P; C=N/A | `10.1109/LRA.2025.3592080` → [DOI/IEEE](https://doi.org/10.1109/LRA.2025.3592080), [arXiv record](https://arxiv.org/abs/2412.20397) | Three authors, exact title, RA-L 10(9), 9216–9223 (2025), and DOI verified; the older arXiv posting explains the 2024 preprint date but does not invalidate the 2025 journal record. |
| `bhatt2026box` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `2605.26430 Bhatt multi-robot box transport` → [arXiv](https://arxiv.org/abs/2605.26430) | Title, five authors, identifier and 26 May 2026 posting verified. The abstract explicitly gives push/support/prevent roles, varying inclination/friction, Isaac Sim tests, and four-TurtleBot physical validation. |
| `bicchi1995closure` | **KEEP** | E=YES; M=P; C=N/A | `10.1177/027836499501400402` → [SAGE/DOI](https://doi.org/10.1177/027836499501400402) | Author, exact title, IJRR 14(4), 319–334 (1995), and DOI match. |
| `bostonStretch2026` | **FIX** | E=YES; M=FIX; C=SUPPORTS(1) | `site:bostondynamics.com/products/stretch trailer unloading containers` → [Boston Dynamics product page](https://bostondynamics.com/products/stretch/) | The official page supports box handling and trailer/container unloading, but it is undated; `year={2026}` is not a demonstrated publication year. Remove it and retain `urldate`, or cite the [dated 2026 brochure](https://bostondynamics.com/wp-content/uploads/2026/03/Stretch-Brochure-2026-Final-1.pdf). |
| `brambilla2013swarm` | **KEEP** | E=YES; M=P; C=N/A | `10.1007/s11721-012-0075-2` → [Springer/DOI](https://doi.org/10.1007/s11721-012-0075-2) | Four authors, title, Swarm Intelligence 7(1), 1–41 (2013), and DOI match. |
| `brown2025assembly` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `10.1016/j.robot.2025.105179` → [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0921889025002763) | Four authors, title, RAS 194, article 105179 (Dec. 2025), and DOI match. Its algorithmic stack explicitly combines robot/subteam allocation, collaborative transport configuration, geometric planning, and distributed collision-avoiding control. |
| `bullo2009distributed` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `"Distributed Control of Robotic Networks" Bullo Cortés Martínez Princeton` → [Princeton University Press front matter](https://assets.press.princeton.edu/chapters/s9101.pdf), [DOI](https://doi.org/10.1515/9781400831470) | Authors, full title, Princeton University Press, 2009 and e-book DOI verified. The book directly covers distributed algorithms, robotic networks and motion coordination. |
| `cherukuri2016primaldual` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `10.1016/j.sysconle.2015.10.006` → [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0167691115002078) | Authors, title, Systems & Control Letters 87, 10–15 (2016), and DOI match. The paper states the regularity assumptions and proves asymptotic convergence of constrained primal–dual dynamics. |
| `choi2009consensus` | **KEEP** | E=YES; M=P; C=SUPPORTS(2) | `10.1109/TRO.2009.2022423` → [IEEE Xplore](https://ieeexplore.ieee.org/document/5072249/) | Authors, title, IEEE T-RO 25(4), 912–926 (2009), and DOI match. It introduces CBAA/CBBA, using market-based bidding and consensus-based conflict resolution for decentralized robust task allocation. |
| `clarke1971multipart` | **KEEP** | E=YES; M=P; C=N/A | `10.1007/BF01726210` → [Springer/DOI](https://doi.org/10.1007/BF01726210) | Edward H. Clarke, title, Public Choice 11(1), 17–33 (1971), and DOI match. |
| `descartes2024workforceChallenge` | **KEEP** | E=YES; M=P; C=N/A | `site:descartes.com "76%" workforce shortages January 30 2024` → [Descartes official release](https://www.descartes.com/resources/news/descartes-study-reveals-76-supply-chain-and-logistics-operations-are-experiencing) | Corporate author, exact headline, 30 January 2024 and URL verified. |
| `dhl2023warehouseRobotics` | **KEEP** | E=YES; M=P; C=N/A | `site:dhl.com "Warehouse robotics: is this the moment of truth?"` → [DHL official article](https://www.dhl.com/global-en/delivered/innovation/warehouse-robotics-and-automation.html) | Corporate author, title, January 2023 and URL verified. |
| `dias2006market` | **KEEP** | E=YES; M=P; C=SUPPORTS(2) | `10.1109/JPROC.2006.876939` → [DOI/IEEE](https://doi.org/10.1109/JPROC.2006.876939), [CMU Robotics Institute record](https://publications.ri.cmu.edu/market-based-multirobot-coordination-a-survey-and-analysis-2) | Four authors, title, Proceedings of the IEEE 94(7), 1257–1270 (2006), and DOI match. The survey directly supports the MRTA/market framing and discussion of bids, costs, contracts and distributed coordination. |
| `dijkstra1959note` | **KEEP** | E=YES; M=P; C=N/A | `10.1007/BF01386390` → [Springer/DOI](https://doi.org/10.1007/BF01386390) | Author, exact historical spelling “connexion,” Numerische Mathematik 1, 269–271 (1959), and DOI match. |
| `dinh2026bsplines` | **FIX** | E=YES; M=FIX; C=N/A | `10.2139/ssrn.5276334` → [SSRN record](https://ssrn.com/abstract=5276334), [DOI](https://doi.org/10.2139/ssrn.5276334) | The record is real and was posted 30 May 2025. Correct first author from **Cong Khoa Dinh** to **Cong Khanh Dinh**. The key suffix `2026` is inconsistent with the actual 2025 record (the rendered `year={2025}` is correct). Remove or substantiate the note “Pendiente de publicación en revista,” which is not part of the SSRN record. |
| `dorigo2021swarm` | **FIX** | E=YES; M=FIX; C=N/A | `10.1109/JPROC.2021.3072740` → [DOI/IEEE](https://doi.org/10.1109/JPROC.2021.3072740) | Authors, venue, volume/issue/pages/year and DOI are correct. Canonical title is **“Swarm Robotics: Past, Present, and Future [Point of View]”**; restore the omitted suffix. |
| `dutta2021hedonic` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `10.1109/CASE49439.2021.9551582` → [IEEE Xplore](https://ieeexplore.ieee.org/document/9551582), [author-institution record](https://digitalcommons.unf.edu/unf_faculty_publications/1161/) | Five authors, title, CASE 2021, pages 639–644 and DOI match. The paper models heterogeneous robot capabilities, multi-robot tasks and distributed hedonic coalition formation. |
| `ebel2024cooperative` | **KEEP** | E=YES; M=P; C=N/A | `10.1016/j.robot.2023.104612` → [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0921889023002518) | Authors, title, RAS 173, article 104612 (March 2024), and DOI match; the 2023 string in the DOI reflects online registration, not the final volume year. |
| `farivarnejad2022multirobot` | **KEEP** | E=YES; M=P; C=SUPPORTS(2), WEAK(2) | `10.1146/annurev-control-042920-095844` → [Annual Reviews](https://www.annualreviews.org/content/journals/10.1146/annurev-control-042920-095844) | Authors, title, Annual Review volume 5, 205–219 (2022), and DOI match. Strong for the taxonomy of collective-transport control and centralized/decentralized autonomy; only indirect for temporary/adaptive coalition formation and for the claim that control work usually presupposes a fixed coalition/contact configuration. |
| `feinerman2018physics` | **KEEP** | E=YES; M=P; C=N/A | `10.1038/s41567-018-0107-y` → [Nature Physics](https://www.nature.com/articles/s41567-018-0107-y) | Five authors, title, Nature Physics 14(7), 683–693 (2018), and DOI match. |
| `ferrari1992grasps` | **KEEP** | E=YES; M=P; C=N/A | `10.1109/ROBOT.1992.219918` → [IEEE Xplore](https://ieeexplore.ieee.org/document/219918) | Ferrari and Canny, title, ICRA 1992, pages 2290–2295 and DOI match. |
| `fisher1978submodular` | **FIX** | E=YES; M=FIX; C=N/A | `"An analysis of approximations for maximizing submodular set functions—II"` → [Springer chapter](https://link.springer.com/chapter/10.1007/BFb0121195) | Authors, title, book, year and pages are correct. Add canonical DOI `10.1007/BFb0121195`; for complete book metadata add editors M. L. Balinski and A. J. Hoffman and series/volume *Mathematical Programming Studies*, vol. 8. |
| `franci2022stochasticgne` | **KEEP** | E=YES; M=P; C=N/A | `10.1016/j.automatica.2021.110101` → [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0005109821006300) | Authors, title, Automatica 137, article 110101 (2022), and DOI match. A later corrigendum exists, but it does not change this entry's identity/metadata. |
| `friston2010free` | **KEEP** | E=YES; M=P; C=N/A | `10.1038/nrn2787` → [Nature Reviews Neuroscience](https://www.nature.com/articles/nrn2787) | Karl Friston, title, volume 11(2), 127–138 (2010), and DOI match. |
| `garey1978strong` | **KEEP** | E=YES; M=P; C=N/A | `10.1145/322077.322090` → [ACM DOI](https://doi.org/10.1145/322077.322090), [DBLP record](https://dblp.org/rec/journals/jacm/GareyJ78.html) | Garey and Johnson, exact quoted title, JACM 25(3), 499–508 (1978), and DOI match. |
| `geekplus2026` | **KEEP** | E=YES; M=P; C=SUPPORTS(1) | `site:geekplus.com/en AMR automated storage WMS MES` → [Geek+ official site](https://www.geekplus.com/en) | Corporate author, descriptive title and URL are valid for an undated page; omission of `year` is therefore appropriate. The page explicitly lists mobile robots/AMR, storage systems and integration with WMS/ERP/MES. |

## Context-use ledger

Only included-paper uses are listed. Line numbers are those recorded in the supplied fresh context extraction.

| Key | File:line | Context verdict | Reason |
|---|---|---|---|
| `farivarnejad2022multirobot` | `sections/mainmatter/01-introduction.tex:7` | **WEAK** | The review establishes collective transport by multiple robots for oversized/heavy payloads, but not the stronger temporary coalition-sizing mechanism asserted in the sentence. |
| `an2023cooperative` | `sections/mainmatter/01-introduction.tex:7` | **SUPPORTS** | The survey explicitly treats multi-robot cooperative object transport, platforms and task/control challenges; appropriate in the citation cluster. |
| `choi2009consensus` | `sections/mainmatter/01-introduction.tex:16` | **SUPPORTS** | CBBA is exactly a decentralized multi-assignment/bundle auction with consensus conflict resolution. |
| `farivarnejad2022multirobot` | `sections/mainmatter/01-introduction.tex:18` | **WEAK** | The paper reviews control strategies by platform/payload interaction and autonomy, but “con frecuencia parte de una coalición o contacto ya definido” is an inference rather than an explicit reviewed result. |
| `barreiro2017distributed` | `sections/mainmatter/01-introduction.tex:20` | **SUPPORTS** | Distributed population dynamics are developed for partial-information graphs with optimization/control applications. |
| `dias2006market` | `sections/mainmatter/05-theoretical-framework/index.tex:18` | **SUPPORTS** | It is a foundational survey of market-based multirobot coordination. |
| `bullo2009distributed` | `sections/mainmatter/05-theoretical-framework/index.tex:19` | **SUPPORTS** | The monograph is directly about distributed control of robotic networks and motion-coordination algorithms. |
| `azadeh2019warehouse` | `sections/mainmatter/05-theoretical-framework/index.tex:21` | **SUPPORTS** | It is a review of robotized and automated warehouse systems, including robotic mobile fulfillment. |
| `farivarnejad2022multirobot` | `sections/mainmatter/05-theoretical-framework/index.tex:22` | **SUPPORTS** | It is a dedicated review of multirobot collective transport. |
| `an2023cooperative` | `sections/mainmatter/05-theoretical-framework/index.tex:22` | **SUPPORTS** | It is a dedicated review of multi-robot systems in cooperative object transport. |
| `dias2006market` | `sections/mainmatter/05-theoretical-framework/index.tex:132` | **SUPPORTS** | The paper explains market-based coordination through revenues/costs, bids, auctions and task contracts. |
| `choi2009consensus` | `sections/mainmatter/05-theoretical-framework/index.tex:133` | **SUPPORTS** | CBAA/CBBA provide consensus-based decentralized auctions and conflict-free robust allocations under their assumptions. |
| `dutta2021hedonic` | `sections/mainmatter/05-theoretical-framework/index.tex:140` | **SUPPORTS** | It addresses heterogeneous capabilities/resources and tasks requiring multi-robot coalitions with distributed formation. |
| `ames2017cbf` | `sections/mainmatter/05-theoretical-framework/index.tex:238` | **SUPPORTS** | The paper derives CBF inequality constraints explicitly on control inputs. |
| `farivarnejad2022multirobot` | `sections/mainmatter/05-theoretical-framework/index.tex:273` | **SUPPORTS** | The review explicitly categorizes centralized, leader–follower and decentralized/autonomous transport control. |
| `brown2025assembly` | `sections/mainmatter/05-theoretical-framework/index.tex:354` | **SUPPORTS** | Its full stack includes robot/subteam allocation, collaborative carrying configurations, spatial/geometric planning and distributed execution control. |
| `bhatt2026box` | `sections/mainmatter/05-theoretical-framework/index.tex:374` | **SUPPORTS** | The arXiv abstract names the three roles, terrain/friction variations, proportional/rule control and physical TurtleBot validation. |
| `amazon2026robotsFulfillment` | `sections/mainmatter/05-theoretical-framework/index.tex:393` | **SUPPORTS** | Amazon directly describes Sequoia/Hercules/Titan and other systems moving inventory to storage or picking/packing stages. |
| `geekplus2026` | `sections/mainmatter/05-theoretical-framework/index.tex:395` | **SUPPORTS** | Geek+ directly lists AMR/moving robots, mobile storage/ASRS and WMS/MES integration. |
| `agilox2026` | `sections/mainmatter/05-theoretical-framework/index.tex:402` | **SUPPORTS** | AGILOX explicitly states X-SWARM operates without a master computer and distributes orders among communicating AMRs. |
| `bostonStretch2026` | `sections/mainmatter/05-theoretical-framework/index.tex:404` | **SUPPORTS** | Boston Dynamics explicitly markets Stretch for autonomously handling boxes and unloading trailers/containers. |
| `cherukuri2016primaldual` | `sections/mainmatter/06-results-and-analysis/sp4-motion.tex:108` | **SUPPORTS** | The source states differentiability/Lipschitz/concavity-convexity and solution assumptions used for convergence; the manuscript correctly says it does not prove the full nonlinear trajectory. |
| `ames2017cbf` | `sections/mainmatter/06-results-and-analysis/sp4-motion.tex:162` | **SUPPORTS** | Forward invariance under the CBF conditions is central to the source; the manuscript appropriately confines the claim to its declared model/hypotheses and separately notes saturation risks. |

## Required fixes before final aggregation

1. Remove unsupported publication years from `agilox2026` and `bostonStretch2026`, or replace the cited pages with genuinely dated 2026 documents.
2. Add DOI `10.5555/3463952.3463974` to `aziz2021complexity`.
3. Correct `dinh2026bsplines`: `Cong Khoa Dinh` → `Cong Khanh Dinh`; remove/substantiate the journal-publication note; consider normalizing the uncited key to a `2025` suffix.
4. Restore `[Point of View]` in the canonical title of `dorigo2021swarm`.
5. Add DOI `10.1007/BFb0121195` and preferably editors/series volume to `fisher1978submodular`.
6. Consider tightening or adding a coalition-formation citation to the two `WEAK` Farivarnejad contexts; no current citation is `WRONG`.

## Blockers

None. All 36 entries were located and checked online. This batch alone therefore yields **WARN / metadata_drift**, not FAIL: there are FIX items but no REPLACE/REMOVE verdicts.
