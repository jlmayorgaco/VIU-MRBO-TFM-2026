# SP4 independent-block sensitivity

The independent unit is the `(seed, n_robots)` block. Each of the 18 blocks aggregates the same six scenarios; the 108 paired instances remain descriptive.

| Hypothesis | Mean original difference | Positive / negative / tied blocks | Exact p | Holm p | Supported |
|---|---:|---:|---:|---:|:---:|
| H4_1_replicator_safe_success_above_cbf | 0.092593 | 7 / 1 / 10 | 0.0351562 | 0.0351562 | yes |
| H4_2_replicator_collision_below_direct | -0.833333 | 18 / 0 / 0 | 3.8147e-06 | 1.90735e-05 | yes |
| H4_3_exact_kkt_below_ring | -0.335147 | 17 / 1 / 0 | 7.24792e-05 | 0.000144958 | yes |
| H4_4_replicator_safe_success_above_nash_pd | 0.240741 | 18 / 0 / 0 | 3.8147e-06 | 1.90735e-05 | yes |
| H4_5_replicator_position_error_below_central | -1.043555 | 18 / 0 / 0 | 3.8147e-06 | 1.90735e-05 | yes |

Positive blocks are always oriented in the preregistered direction. No optional stopping or post-hoc change of endpoint was introduced.
