# SP0 B0 Audit Report

Checks: `380`
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
| null_semantics | 1 | 1 | 0 | 0 | 0 | 0 | ['schema'] |
| oracle_correctness | 15 | 15 | 0 | 0 | 0 | 1e-09 | ['HUN'] |
| oracle_leakage | 5 | 5 | 0 | 0 | 0 | 0 | ['DA', 'GRD', 'HYB', 'REP', 'SMI'] |
| parquet_schema | 1 | 1 | 0 | 0 | 0 | 0 | ['schema'] |
| potential_monotonicity | 8 | 8 | 0 | 14 | 14 | 0 | ['BNN', 'GPC', 'HYB', 'IBR', 'LOG', 'PROJ', 'REP', 'SMI'] |
| qr_acceptance | 1 | 1 | 0 | 0 | 0 | 0 | ['QR2'] |
| qr_termination | 2 | 2 | 0 | 0 | 0 | 0 | ['QR1', 'QRA'] |
| runtime_correctness | 3 | 3 | 0 | 0 | 0 | 0 | ['HUN'] |
| seed_reproducibility | 1 | 1 | 0 | 0 | 0 | 0 | ['HUN'] |
| simplex | 8 | 8 | 0 | 2.22e-16 | 0.000222 | 1e-06 | ['BNN', 'GPC', 'HYB', 'IBR', 'LOG', 'PROJ', 'REP', 'SMI'] |
| timeout_preservation | 2 | 2 | 0 | 63 | 63 | 0 | ['SMI', 'schema'] |

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
