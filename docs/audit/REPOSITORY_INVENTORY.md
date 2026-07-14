# Repository forensic inventory

Audit baseline: commit `72418e13f1bed1a6d37698e59bf0d07400dc8b10`; dirty worktree with pre-existing and current changes. Nothing was deleted or moved. The file-level SP0 inventory and 23,456 hashes are in `results/sp0/SP0_AUDIT_v1/`.

## Functional tree

| Area | Primary paths | Purpose | Status | Consumers | Outputs |
|---|---|---|---|---|---|
| Domain model | `src/viu_mrob_tfm/domain/` | Robots, loads, world, graph, formation | active | SP1–SP8, allocation, simulations | in-memory typed states |
| Generic allocation | `src/viu_mrob_tfm/allocation/` | Base allocator, greedy, Hungarian, auction proxy, generic SmithQR | active but semantically narrow | simulation engine, SP1 | `Assignment` |
| SP0 protocol | `src/viu_mrob_tfm/sp0/` | Cardinality assignment, population dynamics, closures, MAPPO/IPPO, campaign, postprocess | active historical adapter | SP0 CLI/scripts/tests | Parquet, checkpoints, trajectories, report |
| SP1 recruitment | `src/viu_mrob_tfm/sp1/` | Integer quorum/capacity recruitment, methods, MAPPO, metrics | active development | SP1 runner/tests | CSV, figures, videos, model artifacts |
| SP2–SP8 | `src/viu_mrob_tfm/sp2/` … `sp8/` | Incremental capacity, wrench, motion, transport, recovery, communications, scale studies | active research, heterogeneous semantics | per-SP runners/tests | per-SP results |
| SP9/CoppeliaSim | `src/viu_mrob_tfm/sp9/`, `coppeliasim/`, `scripts/coppelia/` | simulator-gap and scene tooling | experimental/external-runtime | SP9 scripts, manual simulator | scenes, CSV, video, gap report |
| Legacy simulation stack A | `src/viu_mrob_tfm/simulation/`, `src/viu_mrob_tfm/controllers/` | older OOP engine/controller layer | legacy but imported | architecture and simulation tests | simulation results |
| Simulation stack B | `src/viu_mrob_tfm/simulations/` | warehouse/mesoscopic policies and metrics | active but separate | warehouse scripts, SP8-like studies | CSV/figures/videos |
| Experiment runner core | `src/viu_mrob_tfm/experiments/` | registry and generic config runner | active | `viu-run-experiment` | configured runs |
| Minimal protocol prototype | `experiments/minimal_protocol/` | earlier protocol engine | experimental/legacy | `scripts/run_minimal_protocol.py` | prototype manifests/results |
| Common protocol v1 | `src/viu_mrob_tfm/experiment_common/`, `configs/experiments/common/` | lifecycle, stages, cache, failures, schemas | new active draft | future SP0 adapters and SP1–SP8 | validated contracts |
| Configurations | `configs/experiments/`, `configs/scenarios/`, `configs/training/`, `configs/marl/` | scenario/campaign/training definitions | active, not uniformly versioned | runners | frozen/runtime configuration |
| Entrypoints | `src/viu_mrob_tfm/cli/`, `scripts/run_sp*_experiment.py`, `experiments/sp0.py` | user-facing execution | active with duplication | Make/manual execution | campaigns |
| Statistical analysis | `src/viu_mrob_tfm/experiment_stats.py`, per-SP runners, `sp0/postprocess.py` | inference, Holm, reports | active, semantics inconsistent | reports/tables | hypothesis/model tables |
| Figure/video generation | per-SP `visualization.py`, `src/viu_mrob_tfm/plotting/`, `scripts/generate_*`, `scripts/build_video_catalog.py` | derived artifacts | active, no universal source-data contract | thesis/results | PNG/PDF/SVG/MP4/catalogs |
| Thesis | `docs/doc-05-final-report/` | primary LaTeX deliverable | active, heavily edited | LaTeX toolchain | PDF |
| Secondary manuscript sources | `TFM.md`, `docs/doc-06-explanatory-report/`, `docs/report/` | source/older report variants | legacy/auxiliary | manual editing | Markdown/LaTeX reports |
| Tests | `tests/` | unit/integration/protocol checks | active | pytest/CI | pass/fail evidence |
| Canonical SP0 CPU results | `results/sp0/SP0_PROTOCOL_v1_2_CPU/` | frozen 15,436-evaluation SP0 base campaign plus precision extensions | canonical resource-constrained and immutable | audit/thesis | raw/derived/checkpoints/trajectories |
| Other results | `results/sp1/` … `results/sp9/`, `results/theory_validation/` | observed campaigns and validation artifacts | mixed confirmatory/exploratory; not uniformly labeled | thesis/reports | tables/figures/videos |
| Archived results | `_archive/`, `results/sp0/archive/` | noncanonical or superseded outputs | archived | audit only | historical evidence |

## Entrypoints and ownership

- Canonical installed CLIs are declared in `pyproject.toml` for generic execution and SP1–SP8. SP0 instead has `src/viu_mrob_tfm/cli/run_sp0.py`, `scripts/run_sp0_experiment.py`, and `experiments/sp0.py` without a matching project script; this is ambiguous.
- Each SP has a thin `scripts/run_spN_experiment.py` wrapper over `src/viu_mrob_tfm/cli/run_spN.py`; retaining both is acceptable only if the CLI remains canonical and wrappers contain no semantics.
- Training is split across SP-specific modules (`sp0/data_driven.py`, `sp1/mappo.py`) and older standalone MARL scripts. The latter are not evidence for SP0/SP1 checkpoints unless explicitly referenced by a manifest.
- Postprocessing is distributed between runners and scripts. No single command currently rebuilds every SP0 table, figure source dataset, video, report, and claim ledger from raw artifacts.

## Duplicate or semantically overlapping implementations

| Name/idea | Implementations | Material difference | Required canonical name |
|---|---|---|---|
| Smith-QR | `allocation/smith_qr.py`, `sp0/methods.py`, `sp1/methods.py`, `sp3/methods.py`, SP5 aliases, `sp6/methods.py`, `simulations/warehouse.py` | ranges from cardinality utility + greedy allocation, to continuous population dynamics + QR1/QR2, wrench-aware pair repair, recovery policy, and warehouse heuristics | never use bare `Smith-QR` in evidence; include signal, state space, closure, guard, and SP |
| Hungarian/oracle | generic static Hungarian, SP0 exact rectangular assignment, SP1 expanded Hungarian baseline, SP1 binary coalition MILP, SP3 slot Hungarian/reference | only some solve the actual SP-specific feasible set | `hungarian_slot_baseline`, `sp0_assignment_oracle`, `sp1_coalition_milp`, etc. |
| CBBA | generic `DecentralizedAuctionAllocator`, SP1 `cbba`, SP3 `cbba_slots`/`cbba_wrench_score`, SP6 recovery, warehouse proxy | repository adaptations/proxies, not a single faithful CBBA implementation | `cbba_like_<problem>` unless fidelity is independently established |
| MAPPO | SP0 graph PPO, SP1 recruitment MAPPO, old CTDE scripts | different observations, actors, critics, decoders, training budgets | `SP0_MAPPO_GNN_PPO_v1_2` and `SP1_MAPPO_recruitment_v5` |
| Wrench market | SP1 scalar proxy, SP3 residual-support and guarded variants, SP5 aliases, SP6 recovery | SP1 has no full contact-wrench feasibility; SP3 contains the substantive wrench problem | reserve “wrench-gated” for methods that execute the SP3 guard |
| Simulation | singular `simulation/` and plural `simulations/` | different state/engine/policy models | keep both until adapters and regression tests permit consolidation |

## Artifacts and provenance

- SP0 v1.2 contains 23,575 files totaling about 410 MB in the audit snapshot. The audit hashes checkpoints, Parquet, protocol/manifests, worlds, and trajectories.
- SP1 currently has one observed result directory, `SP1_MC_recruitment_comparison`, using the older `tables/figures/videos` contract. It is development/exploratory evidence for the new draft protocol, not a sealed holdout.
- SP2–SP8 each contain multiple result variants, including “high_power” names. Directory naming does not prove confirmatory status; only frozen protocol, seed-opening, and manifest evidence may do so.
- Figure PNGs exist without a universal one-CSV-per-figure contract. Videos exist without a universal trajectory/render manifest. These are reproducibility gaps, not dead files.

## Dead, unknown, or risky candidates

No file is declared safe to delete in this phase. Candidates for later reachability analysis include old report trees, minimal-protocol prototypes, standalone MARL scripts, and duplicated run wrappers. `_archive/` is intentionally retained. The working tree had extensive unrelated edits, so no cleanup or commit was attempted.

## Priority findings

1. The proposed method is not uniquely named across code or thesis.
2. Bare “Smith-QR” denotes incompatible algorithms.
3. SP0 checkpoint files differ, but their audited RAW actions do not.
4. SP0 closed performance is decoder/repair dominated.
5. SP0 lifecycle ambiguity is resolved by `results/sp0/PROTOCOL_INDEX.md`: v1.2 CPU is canonical within its reduced-budget scope; v1.1 remains stopped pre-freeze.
6. Several SP0 supported claims have non-finite intervals or `p=0`.
7. SP0 has no explicit causal failure taxonomy and no complete rebuild command.
8. SP1’s previous “MILP” implementation was subset/Hungarian enumeration; it has now been replaced by a binary MILP and remains pre-confirmatory.
9. SP1 does not persist immutable RAW/REPAIR/QR stages.
10. Existing SP1–SP8 results must be treated as observed development evidence until their split/freeze provenance is audited.
