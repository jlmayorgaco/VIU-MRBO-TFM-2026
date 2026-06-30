# Smith-QR validation

- Seeds: 2026-2045 (`n=20`).
- Cases: R3_p0.
- R3_p0 Smith-QR full delta vs Smith capture: 0.1855 (CI95 low 0.1434).
- Pre-registered verdict: `PASS`.

| Case | Method | n | Capture | Throughput | Wasted distance |
|---|---|---:|---:|---:|---:|
| R3_p0 | centralized_limited_comm | 20 | 0.06113 | 0.15 | 2.862 |
| R3_p0 | greedy | 20 | 0.2427 | 1.483 | 37.44 |
| R3_p0 | marl_proxy | 20 | 0.2366 | 1.367 | 41.59 |
| R3_p0 | smith | 20 | 0.1038 | 0.4667 | 16.86 |
| R3_p0 | smith_qr_full | 20 | 0.2893 | 1.833 | 41.08 |
