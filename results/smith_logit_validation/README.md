# Smith logit mutation validation

- Best R3 candidate: `smith_logit_no_integer_mu0.60_tau0.10` with `{'smith_integer_clearing_enabled': False, 'smith_logit_mutation_rate': 0.6, 'smith_logit_temperature': 0.1}`.
- Grid seeds: 2026-2030. Validation seeds: 2026-2030.
- Baselines are paired against `results/benchmark-v27-full/summary.csv`.
- R3_p0 paired delta vs Smith in reward capture: 0.08088 (CI95 -0.02302, 0.1848).
- Verdict: `not confirmed` for the isolated logit-mutation patch.

## Mean reward capture

| Case | Method | n | Capture mean | Throughput mean | Wasted distance mean |
|---|---|---:|---:|---:|---:|
| R1.5_p0 | classic_greedy_nearest | 5 | 0.05598 | 0.3333 | 24.15 |
| R1.5_p0 | smith | 5 | 0.03711 | 0.1333 | 19.24 |
| R1.5_p0 | smith_logit_no_integer_mu0.60_tau0.10 | 5 | 0.05156 | 0.3333 | 24.08 |
| R1.5_p0 | smith_no_integer | 5 | 0.05156 | 0.2667 | 24.37 |
| R12_p0 | classic_greedy_nearest | 5 | 0.59 | 3.533 | 107.2 |
| R12_p0 | smith | 5 | 0.543 | 3.467 | 99.4 |
| R12_p0 | smith_logit_no_integer_mu0.60_tau0.10 | 5 | 0.2682 | 1.667 | 149.7 |
| R12_p0 | smith_no_integer | 5 | 0.2787 | 1.867 | 152.9 |
| R3_p0 | classic_greedy_nearest | 5 | 0.2582 | 1.533 | 30.02 |
| R3_p0 | smith | 5 | 0.03819 | 0.2 | 18.49 |
| R3_p0 | smith_logit_mu0.15_tau0.20 | 5 | 0.03439 | 0.1333 | 16.87 |
| R3_p0 | smith_logit_mu0.30_tau0.20 | 5 | 0.03439 | 0.1333 | 16.74 |
| R3_p0 | smith_logit_mu0.60_tau0.10 | 5 | 0.03439 | 0.1333 | 16.67 |
| R3_p0 | smith_logit_mu0.60_tau0.20 | 5 | 0.03439 | 0.1333 | 16.67 |
| R3_p0 | smith_logit_mu1.00_tau0.10 | 5 | 0.03439 | 0.1333 | 16.67 |
| R3_p0 | smith_logit_mu1.00_tau0.20 | 5 | 0.03439 | 0.1333 | 16.67 |
| R3_p0 | smith_logit_no_integer_mu0.30_tau0.20 | 5 | 0.1006 | 0.4 | 29.35 |
| R3_p0 | smith_logit_no_integer_mu0.60_tau0.10 | 5 | 0.1191 | 0.7333 | 73.69 |
| R3_p0 | smith_logit_no_integer_mu0.60_tau0.20 | 5 | 0.1106 | 0.6 | 18.03 |
| R3_p0 | smith_logit_no_integer_mu1.00_tau0.20 | 5 | 0.1106 | 0.6 | 29.72 |
| R3_p0 | smith_no_integer | 5 | 0.153 | 0.9333 | 184.9 |
| R4_p0 | classic_greedy_nearest | 5 | 0.59 | 3.533 | 107.2 |
| R4_p0 | smith | 5 | 0.543 | 3.467 | 97.12 |
| R4_p0 | smith_logit_no_integer_mu0.60_tau0.10 | 5 | 0.2682 | 1.667 | 148 |
| R4_p0 | smith_no_integer | 5 | 0.2787 | 1.867 | 143.1 |

## Files

- `grid_runs.csv`: candidate sweep on R3_p0.
- `validation_runs.csv`: best candidate on R12_p0, R4_p0, R3_p0 and R1.5_p0.
- `summary.csv`: mean and CI95 by case/method.
- `paired_deltas.csv`: paired candidate-minus-baseline deltas.
