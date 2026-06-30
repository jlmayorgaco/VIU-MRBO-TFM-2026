# Smith-QR validation

- Seeds: 2026-2026 (`n=1`).
- Cases: R3_p0.
- Scope: smoke validation, not the final 20-seed statistical campaign.
- R3_p0 Smith-QR full delta vs Smith capture: 0.2481 (CI95 low 0.2481).
- Pre-registered verdict: `PASS`.

| Case | Method | n | Capture | Throughput | Wasted distance |
|---|---|---:|---:|---:|---:|
| R3_p0 | centralized_limited_comm | 1 | 0.1072 | 0 | 0 |
| R3_p0 | greedy | 1 | 0.3722 | 2 | 12.68 |
| R3_p0 | marl_proxy | 1 | 0.352 | 2 | 11.17 |
| R3_p0 | smith | 1 | 0.02229 | 0 | 70.07 |
| R3_p0 | smith_qr_full | 1 | 0.2704 | 1.667 | 20.26 |
