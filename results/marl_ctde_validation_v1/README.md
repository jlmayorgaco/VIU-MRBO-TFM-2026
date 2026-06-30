# MARL CTDE validation

- Model version: marl-ctde-linear-v1.
- Seeds: 2026-2033 (`n=8`).
- Evaluation uses frozen weights and seeds not used by training.

| Scenario | Case | Method | n | Capture | Delivered | Wasted distance |
|---|---|---|---:|---:|---:|---:|
| comm_degradation | R3_p0 | centralized_limited_comm | 8 | 0.1548 | 1.375 | 14.23 |
| comm_degradation | R3_p0 | greedy | 8 | 0.2384 | 2.125 | 36.39 |
| comm_degradation | R3_p0 | marl_ctde | 8 | 0.2384 | 2.125 | 30.48 |
| comm_degradation | R3_p0 | marl_proxy | 8 | 0.2384 | 2.125 | 23.04 |
| comm_degradation | R3_p0 | smith | 8 | 0.1507 | 1.375 | 25.49 |
| comm_degradation | R3_p0 | smith_qr_full | 8 | 0.3128 | 2.625 | 17.36 |
| robot_failures | fail4 | centralized_limited_comm | 8 | 0.7057 | 5.625 | 80.17 |
| robot_failures | fail4 | greedy | 8 | 0.7083 | 5.625 | 81.26 |
| robot_failures | fail4 | marl_ctde | 8 | 0.4116 | 3.5 | 99.1 |
| robot_failures | fail4 | marl_proxy | 8 | 0.5936 | 4.5 | 131.7 |
| robot_failures | fail4 | smith | 8 | 0.5987 | 4.75 | 78.74 |
| robot_failures | fail4 | smith_qr_full | 8 | 0.5987 | 4.75 | 78.74 |
| scarcity_priority | adversarial | centralized_limited_comm | 8 | 0.7692 | 7 | 108.2 |
| scarcity_priority | adversarial | greedy | 8 | 0.7692 | 7 | 112.9 |
| scarcity_priority | adversarial | marl_ctde | 8 | 0.5385 | 6 | 110.6 |
| scarcity_priority | adversarial | marl_proxy | 8 | 0.3558 | 3.125 | 119.6 |
| scarcity_priority | adversarial | smith | 8 | 0.7692 | 7 | 80.04 |
| scarcity_priority | adversarial | smith_qr_full | 8 | 0.7692 | 7 | 80.04 |

## H0/H1 tests

- marl_ctde_capture_gt_marl_proxy: mean delta=0.0002476, p=0.4975, decision=do_not_reject_h0
- marl_ctde_capture_gt_smith_qr_full: mean delta=-0.1641, p=0.9997, decision=do_not_reject_h0
- marl_ctde_capture_gt_smith: mean delta=-0.1101, p=0.9813, decision=do_not_reject_h0
- marl_ctde_capture_gt_greedy: mean delta=-0.1758, p=0.9998, decision=do_not_reject_h0
