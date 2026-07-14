# SP0 B0 Audit Report

Checks: `389`
Failed checks: `0`

| Family | Cases | Passed | Failed | Max abs error | Max rel error | Tolerance | Affected methods |
|---|---:|---:|---:|---:|---:|---:|---|
| b0_budget_execution | 300 | 300 | 0 | 0 | 0 | 0 | ['BNN', 'GPC', 'HYB', 'IBR', 'LOG', 'PROJ', 'REP', 'SMI'] |
| cache_consistency | 2 | 2 | 0 | 0 | 0 | 1e-09 | ['graph'] |
| duplicate_rows | 1 | 1 | 0 | 0 | 0 | 0 | ['schema'] |
| mass_conservation | 12 | 12 | 0 | 2.22e-16 | 0.000222 | 1e-06 | ['BNN', 'GPC', 'HYB', 'IBR', 'LOG', 'PROJ', 'REP', 'SMI'] |
| matching_validity | 5 | 5 | 0 | 0 | 0 | 1e-09 | ['ARG', 'HUN', 'QR1', 'REPAIR'] |
| metric_correctness | 5 | 5 | 0 | 0 | 0 | 1e-09 | ['HUN', 'objective'] |
| non_negativity | 8 | 8 | 0 | 0 | 0 | 1e-09 | ['BNN', 'GPC', 'HYB', 'IBR', 'LOG', 'PROJ', 'REP', 'SMI'] |
| null_semantics | 2 | 2 | 0 | 0 | 0 | 0 | ['schema:b0_budget', 'schema:smoke'] |
| oracle_correctness | 15 | 15 | 0 | 0 | 0 | 1e-09 | ['HUN'] |
| oracle_leakage | 12 | 12 | 0 | 0 | 0 | 0 | ['BNN', 'DA', 'GPC', 'GRD', 'HYB', 'IBR', 'IPPO-GNN', 'LOG', 'MAPPO-GNN', 'PROJ', 'REP', 'SMI'] |
| parquet_schema | 2 | 2 | 0 | 0 | 0 | 0 | ['schema:b0_budget', 'schema:smoke'] |
| potential_monotonicity | 8 | 8 | 0 | 0 | 0 | 0 | ['BNN', 'GPC', 'HYB', 'IBR', 'LOG', 'PROJ', 'REP', 'SMI'] |
| qr_acceptance | 1 | 1 | 0 | 0 | 0 | 0 | ['QR2'] |
| qr_termination | 2 | 2 | 0 | 0 | 0 | 0 | ['QR1', 'QRA'] |
| runtime_correctness | 3 | 3 | 0 | 0 | 0 | 0 | ['HUN'] |
| seed_reproducibility | 1 | 1 | 0 | 0 | 0 | 0 | ['HUN'] |
| simplex | 8 | 8 | 0 | 2.22e-16 | 0.000222 | 1e-06 | ['BNN', 'GPC', 'HYB', 'IBR', 'LOG', 'PROJ', 'REP', 'SMI'] |
| timeout_preservation | 2 | 2 | 0 | 0 | 0 | 0 | ['SMI', 'schema'] |

## Continuous convergence diagnostics

A continuous timeout is retained even when the integer closure later reaches a valid maximum-cardinality assignment.

| Method | Runs | Timeout rate | Median residual | Median state change | Median fractionality | Median convergence time (s) |
|---|---:|---:|---:|---:|---:|---:|
| BNN | 38 | 1.000 | 0.0335 | 0.00169 | 0.595 | null |
| GPC | 37 | 1.000 | 0.0365 | 0.00184 | 0.529 | null |
| HYB | 37 | 1.000 | 0.0432 | 0.00217 | 0.562 | null |
| IBR | 37 | 0.946 | 0.946 | 0.278 | 0.561 | 3.3 |
| LOG | 38 | 0.842 | 0.00131 | 6.9e-05 | 0.735 | 9.4 |
| PROJ | 37 | 1.000 | 0.0547 | 0.00271 | 0.452 | null |
| REP | 38 | 1.000 | 0.0302 | 0.00152 | 0.599 | null |
| SMI | 38 | 1.000 | 0.0397 | 0.002 | 0.557 | null |

## Gates

| Gate | Status | Failed checks |
|---|---:|---|
| G1 | PASS | - |
| G2 | PASS | - |
| G3 | PASS | - |
| G4 | PASS | - |
| G5 | PASS | - |
| G6 | PASS | - |
| G7 | PASS | - |
| SMOKE | PASS | - |
