# Smith deterministic approximation sweep

- N values: 6, 12, 24, 48, 96
- Seeds: 2026-2065 (`n=40`)
- Horizon: 24 s; dt: 0.02 s
- Fluid scaling: beta_N = 6 / N
- Fitted log-log slope: -0.9294 (target: -0.5)

| N | mean RMS error | std |
|---:|---:|---:|
| 6 | 0.132359 | 0.0144351 |
| 12 | 0.0703639 | 0.00814518 |
| 24 | 0.0352844 | 0.00169156 |
| 48 | 0.0186735 | 0.00182761 |
| 96 | 0.0102536 | 0.00154694 |
