# Reproducibility Guide

## Environment

Recommended local setup:

```powershell
python -m pip install -U pip
python -m pip install -e .
```

The repository uses Python `>=3.11` and the dependencies declared in `pyproject.toml`.

## Main Commands

Fast regression suite:

```powershell
make test-fast
```

Smoke experiments for SP1-SP8:

```powershell
make test-smoke
```

Canonical Monte Carlo experiments:

```powershell
make run-canonical
```

Final LaTeX report plus generated PDF summaries:

```powershell
make build-report
```

Canonical high-power SP3-SP8 runs:

```powershell
python -m viu_mrob_tfm.cli.run_sp3 configs/experiments/sp3/SP3_MC_wrench_comparison_high_power.yaml
python -m viu_mrob_tfm.cli.run_sp4 configs/experiments/sp4/SP4_MC_motion_comparison_high_power.yaml
python scripts/run_sp5_experiment.py configs/experiments/sp5/SP5_MC_cooperative_transport_high_power.yaml
python scripts/run_sp6_experiment.py configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml
python scripts/run_sp7_experiment.py configs/experiments/sp7/SP7_MC_communication_robustness_high_power.yaml
python scripts/run_sp8_experiment.py configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml
```

SP5 and SP6 high-power retain trajectory-level state until the end of the run. On the July 2026 workstation runs, SP5 (`20,040` rollouts) and SP6 (`20,000` rollouts) took several hours and several GB of RAM. SP7 (`20,176` runs) and SP8 (`20,000` runs) are also multi-hour CPU-bound runs. For video inspection, use the compact runs below; the high-power runs are the statistical evidence.

Representative video/compact runs:

```powershell
python -m viu_mrob_tfm.cli.run_sp3 configs/experiments/sp3/SP3_MC_wrench_comparison_methodology_v3.yaml
python -m viu_mrob_tfm.cli.run_sp4 configs/experiments/sp4/SP4_MC_motion_comparison.yaml
python scripts/run_sp5_experiment.py configs/experiments/sp5/SP5_MC_cooperative_transport.yaml
python scripts/run_sp6_experiment.py configs/experiments/sp6/SP6_MC_robustness_comparison.yaml
python scripts/run_sp8_experiment.py configs/experiments/sp8/SP8_MC_scalability_warehouse.yaml
```

Explicit AMR control-law supplements:

```powershell
python -m viu_mrob_tfm.cli.run_sp4 configs/experiments/sp4/SP4_MC_explicit_control_law.yaml
python -m viu_mrob_tfm.cli.run_sp5 configs/experiments/sp5/SP5_MC_explicit_control_law.yaml
python -m viu_mrob_tfm.cli.run_sp6 configs/experiments/sp6/SP6_MC_explicit_control_law.yaml
```

Stress-scale SP7 communication run:

```powershell
python scripts/run_sp7_experiment.py configs/experiments/sp7/SP7_MC_communication_robustness_full.yaml
```

Earlier extended SP8 fleet ladder run:

```powershell
python scripts/run_sp8_experiment.py configs/experiments/sp8/SP8_MC_fleet_ladder_extended.yaml
```

Full-scale SP8 warehouse scalability run:

```powershell
python scripts/run_sp8_experiment.py configs/experiments/sp8/SP8_MC_scalability_warehouse_full.yaml
```

Publication-style paper figures:

```powershell
python scripts/generate_paper_figures.py
```

Submit-ready derived artifacts:

```powershell
make method-matrix
make theory-validation
make stats-annex
make figures-paper
make video-catalog
make sp9
make thesis
make submit-check
```

`make sp9` does not fabricate CoppeliaSim evidence. If the simulator executable is not
available in `PATH`, it writes `results/sp9/SP9_BLOCKED_EXECUTION/report.md` and leaves
SP9 as a prepared protocol rather than a promoted result.

## Result Hygiene

Canonical outputs must live under:

```text
results/sp1/
results/sp2/
results/sp3/
results/sp4/
results/sp5/
results/sp6/
results/sp7/
results/sp8/
```

Top-level result folders that do not belong to an SP are exploratory and should not be cited.
Non-canonical smoke/debug/diagnostic outputs should be archived outside `results/sp*/`; the current cleanup archive is `_archive/results_noncanonical_20260708_sp_cleanup/`.

## Required Tables

Every canonical SP should expose, when applicable:

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/performance_ranking.csv`
- `tables/hypothesis_results.csv`
- `tables/theory_checks.csv`
- `theory_audit.json`
- `report.md`

For SPs with motion evidence, also provide:

- `videos/`
- a video index or catalog explaining scenario, method, objective, parameters and metrics.

## Statistical Practice

The project uses paired comparisons when methods share the same generated world, and multi-method tests for scenario-aligned comparisons. Tables should include:

- H0 statement.
- Alternative hypothesis.
- Metric.
- Paired sample/block count.
- Raw p-value.
- Holm-corrected p-value.
- Effect estimate and confidence interval when available.

The thesis should report effect sizes and confidence intervals before emphasizing p-values.

## Determinism

Configs define seed ranges. If regenerating canonical evidence, preserve:

- Config file path.
- Seed range.
- Method list.
- Checkpoint paths.
- Git commit hash in the final manuscript or experiment log.

## Known Boundaries

- The simulator is not a hardware validation.
- SP3 wrench feasibility is planar quasi-static.
- SP7 is a temporal communication/sensing benchmark, not an RF channel propagation or hardware-network validation.
- Battery OOD in SP7 is a covariate unless an allocator explicitly optimizes battery.
- SP8 is a mesoscopic vectorized scalability benchmark, not full rigid-body contact dynamics, exact MPC at warehouse scale, RF propagation or hardware validation.
