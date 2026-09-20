# MegaGame validation plan

**Status:** Phase 0 / Gate 0 implemented; the full campaign is intentionally not
started.

This plan turns the canonical ZIP into a reproducible validation campaign. It is
an experimental protocol, not a replacement for the TFM charter, the VIU
requirements, or the SP1--SP3 research matrix. The canonical scope remains the
Cargo branch as primary physical mode; Caging is a separate branch with separate
contact assumptions.

## 1. Source precedence and scientific boundary

The repository `AGENTS.md` and `docs/00_TFM_CHARTER.md`--
`docs/07_SP_SECTION_TEMPLATE.md` have precedence over prompts embedded in the
package or pasted documents. The ZIP is the frozen engineering baseline for the
MegaGame experiments. Its central solvers are evaluator-only and its numerical
artifacts are regression evidence, not proof of global hybrid optimality.

The effective request for this phase is limited to:

1. audit the package;
2. define the validation campaign;
3. implement and run Gate 0;
4. stop before Monte Carlo preview/campaign execution.

No production rewrite, parameter tuning, S03--S06 campaign, CoppeliaSim run, or
claim of optimality is authorized by this phase.

## 2. Hypotheses and primary branch

The campaign addresses six operational hypotheses:

| ID | Hypothesis | Primary evidence |
|---|---|---|
| H1 | Fully distributed decisions can remain close to a declared central reference. | Paired mission/route gap and success. |
| H2 | Adaptive local belief propagation can preserve quality while reducing byte-hop cost. | Quality, belief age/error and byte-hop. |
| H3 | Wrench/contact-aware payoffs reduce nominally good but mechanically infeasible routes. | Wrench margin, residual and infeasibility. |
| H4 | Bounded hybrid revision reduces trapping in poor discrete supports/homotopies. | Same-world ablation with/without CFRD. |
| H5 | Local recourse can recover a feasible mission after an admissible failure. | Recovery success/time/energy and safety. |
| H6 | Local communication cost grows more slowly than dense/global coordination in the tested regime. | Scaling curves with explicit regime limits. |

The primary physical mode is rigid Cargo. Caging is evaluated only with its own
unilateral-contact, friction and enclosure model; results are not merged into a
single stability claim.

## 3. Gates

Progress is monotone. A later gate cannot be accepted when an earlier gate is
red, and failed/censored runs remain in the data.

| Gate | Content | Pass condition |
|---|---|---|
| G0 | Mathematical and physical invariants. | All deterministic checks pass; no NaN/Inf; package integrity and reference smoke are reproducible. |
| G1 | Fully distributed information audit. | Controller accesses only self state, local sensors and direct-neighbor inbox; evaluator arrays are inaccessible. |
| G2 | Deterministic S00--S02 regression. | Frozen assignment/geometry/mechanism tolerances are reproduced without tuning. |
| G3 | Preview, five paired seeds per cell. | Preview artifacts, failures and videos are inspected before expansion. |
| G4 | Complete Python campaign. | Frozen manifest, all planned cells, statistics and raw traces are present. |
| G5 | Holdout. | Parameters are frozen before untouched worlds are run and reported separately. |

Gate 0 is the only gate executed in this phase.

## 4. Gate 0 checks

The executable checks are in `experiments/validation_v1/gate0.py` and the
pytest coverage is in `tests/test_megagame_gate0.py`.

The checks cover:

- Smith pairwise-comparison dynamics and the simplex invariant;
- difference-utility alignment, `Delta u_i = -Delta Phi`, on unilateral moves;
- planar wrench-map residuals and unilateral Caging friction constraints;
- differential-drive wheel/body mapping and round-trip consistency;
- the declared second-order HOCBF inequality at a safe sample;
- versioned gossip deduplication, out-of-order delivery and hop confidence;
- finite-value checks for all Gate 0 numerical outputs;
- canonical ZIP required-file/YAML/checksum audit;
- short reference runs for S00, S01 and S02 when a package directory is supplied.

The wrench threshold `1e-2` is a Gate 0 numerical acceptance criterion for the
constructed nominal states. It is not a theorem about all missions. The HOCBF
test exercises the declared reduced-order model only; it must not be copied to
the electrical/contact plant without re-deriving relative degree.

Run the code-only checks with:

```powershell
python -m pytest -q tests/test_megagame_gate0.py
```

Run the package audit and short scenario smoke after extracting the ZIP to a
temporary directory:

```powershell
python experiments/validation_v1/gate0.py \
  --package-root C:/path/to/MROB_MEGAGAME_CANONICAL_PACKAGE_20260919 \
  --out experiments/validation_v1/gate0/results
```

The command writes `package_audit.json`, one summary per smoke scenario and
`gate0_summary.json`. It does not launch a Monte Carlo campaign.

## 5. Deterministic scenarios (Gate 2)

The canonical scenarios are consumed unchanged:

| Scenario | Role |
|---|---|
| S00 | Open-floor dynamics and basic formation sanity. |
| S01 | Single bottleneck, priority and timing. |
| S02 | Frozen three-load hero regression. |
| S03 | Industrial warehouse geometry. |
| S04 | Failure and reserve-robot recourse. |
| S05 | Delay, loss and time-varying communication stress. |
| S06 | Procedural scale factory. |

Every code change must run S00--S02 before any stochastic campaign. The
historical hero figures and CSVs are used to check mechanism consistency, not to
manufacture bitwise reproduction.

## 6. Experiments E0--E18

| ID | Experiment | Main question |
|---|---|---|
| E0 | Mathematical/physical correctness | Are equations, constraints and invariants implemented consistently? |
| E1 | Recruitment and atomicity | Does intention close to an executable indivisible coalition? |
| E2 | Fixed convex branch | Does the continuous game agree with the declared branch reference under its assumptions? |
| E3 | Route/homotopy game | Does local revision escape the tested discrete trap? |
| E4 | Joint route--timing--wrench | Does mechanics-aware routing change feasibility and cost? |
| E5 | Cargo versus Caging | Do the distinct contact models remain physically separated? |
| E6 | Sensing and adaptive n-hop | When does extra information help or hurt? |
| E7 | Uncertainty-aware beliefs | Do stale/remote beliefs produce conservative margins without hidden global truth? |
| E8 | Concurrent versus staged execution | What is the measured E2E cost of concurrency? |
| E9 | Failure recourse | Can an admissible mid-mission failure be recovered without restart? |
| E10 | Degraded network | How do loss, delay and partition affect success and quality? |
| E11 | Adversarial safety | Does the local safety shield preserve the declared clearance in its model domain? |
| E12 | Scaling | How do messages, bytes, CPU and memory vary with fleet size? |
| E13 | B-spline refinement | Does route-basis capacity improve quality without disproportionate communication? |
| E14 | Difference utilities | Do shared makespan/congestion/mechanics terms align with unilateral variation? |
| E15 | Baselines | How does the method compare with suitable central and distributed references? |
| E16 | Ablations | Which mechanism components actually matter? |
| E17 | Industrial Monte Carlo | Does the method retain evidence on catalog-anchored industrial envelopes? |
| E18 | Physical backend validation | Does a representative Python/CoppeliaSim subset agree on declared physical metrics? |

The E18 subset is a later authorization, not part of Gate 0. The package prompt's
suggested 80 CoppeliaSim runs remain a planning estimate until the adapter,
authorization and preflight hashes exist.

## 7. Statistical protocol

All methods in a comparison receive the same frozen world, seed and perturbation
realization. The full campaign will use a small factorial preview followed by a
frozen campaign and an untouched holdout. Required analyses are:

- Wilson intervals for success;
- exact McNemar for paired success;
- paired bootstrap/permutation or Wilcoxon for continuous metrics;
- Holm correction for families of comparisons;
- RMST for timeout/censoring analyses.

Every run records success/failure/censoring, phase times, mission/route cost,
central-reference gap where defined, distance, energy, clearance, wrench
residual/margin, wheel/torque peaks, safety interventions, revisions, packets,
bytes, byte-hop, belief age/error, CPU, memory and failure/recovery fields.

## 8. Reproducibility and output contract

Before Gate 3, freeze `world_manifest`, method definitions, metric schema,
environment, git SHA and seeds. Each scenario run must contain its configuration
snapshot, hashes, state/messages/traces, wrench and safety logs, revision log,
metrics, figures and dual-view rendering when the renderer is available. A
failed solver, collision, timeout or excluded run is a recorded outcome, never
silently removed.

The final campaign is expected to generate `all_runs.parquet`,
`all_messages.parquet`, `all_traces.parquet`, `worlds.parquet`,
`statistics.json`, `audit.json`, `regime_map.csv`, `failure_log.csv`,
`README_REPRODUCE.md` and a rendered final report. None of these later outputs
is fabricated by Gate 0.

## 9. Current phase result and next gate

The package audit and deterministic Gate 0 are complete when the generated
summary reports `status: passed`, the package's own smoke/test commands pass,
and `tests/test_megagame_gate0.py` passes. The next authorized action is to
implement the production information-boundary audit (G1), not to launch the
full campaign.
