# Neural MARL CTDE validation

- Model version: marl-neural-ctde-residual-v1.
- Seeds: 4026-4033 (`n=8`).
- Evaluation uses frozen actor parameters and seeds not used by training.

| Scenario | Case | Method | n | Capture | Delivered | Wasted distance |
|---|---|---|---:|---:|---:|---:|
| comm_degradation | R3_p0 | greedy | 8 | 0.1822 | 1.375 | 49.8 |
| comm_degradation | R3_p0 | marl_ctde | 8 | 0.1626 | 1.25 | 38.75 |
| comm_degradation | R3_p0 | marl_neural_ctde | 8 | 0.1626 | 1.25 | 32.71 |
| comm_degradation | R3_p0 | marl_proxy | 8 | 0.1847 | 1.375 | 45.69 |
| comm_degradation | R3_p0 | smith | 8 | 0.1415 | 1.125 | 1.834 |
| comm_degradation | R3_p0 | smith_qr_full | 8 | 0.2315 | 1.75 | 52.75 |
| robot_failures | fail4 | greedy | 8 | 0.5809 | 4.75 | 111.4 |
| robot_failures | fail4 | marl_ctde | 8 | 0.3133 | 2.875 | 106.8 |
| robot_failures | fail4 | marl_neural_ctde | 8 | 0.2986 | 2.75 | 101.6 |
| robot_failures | fail4 | marl_proxy | 8 | 0.5273 | 4.125 | 109.8 |
| robot_failures | fail4 | smith | 8 | 0.5429 | 4.5 | 99.78 |
| robot_failures | fail4 | smith_qr_full | 8 | 0.5429 | 4.5 | 99.78 |
| scarcity_priority | adversarial | greedy | 8 | 0.7692 | 7 | 110.5 |
| scarcity_priority | adversarial | marl_ctde | 8 | 0.5192 | 5.75 | 116.8 |
| scarcity_priority | adversarial | marl_neural_ctde | 8 | 0.5385 | 6 | 109.3 |
| scarcity_priority | adversarial | marl_proxy | 8 | 0.3654 | 3.25 | 122.4 |
| scarcity_priority | adversarial | smith | 8 | 0.7692 | 7 | 80.49 |
| scarcity_priority | adversarial | smith_qr_full | 8 | 0.7692 | 7 | 80.49 |

## H0/H1 tests

- marl_neural_ctde_capture_gt_marl_ctde: mean delta=0.001494, p=0.4422, decision=do_not_reject_h0
- marl_neural_ctde_capture_gt_marl_proxy: mean delta=-0.02592, p=0.731, decision=do_not_reject_h0
- marl_neural_ctde_capture_gt_smith_qr_full: mean delta=-0.1813, p=1, decision=do_not_reject_h0
- marl_neural_ctde_capture_gt_smith: mean delta=-0.1514, p=0.9998, decision=do_not_reject_h0
- marl_neural_ctde_capture_gt_greedy: mean delta=-0.1776, p=1, decision=do_not_reject_h0
