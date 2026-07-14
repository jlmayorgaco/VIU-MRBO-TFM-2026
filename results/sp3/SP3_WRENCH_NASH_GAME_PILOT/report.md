# SP3_WRENCH_NASH_GAME_PILOT

- Worlds: `12`
- Runs: `144`
- Theory audit: `PASS`

## Summary

| Method | Coverage | Precision | FP assigned | Gap oracle | KKT | Runtime s |
|---|---:|---:|---:|---:|---:|---:|
| erv_bnn_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.06226 | 0.1616 |
| nash_pd_exact_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.01163 | 0.1200 |
| replicator_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.04089 | 0.1384 |
| smith_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.02899 | 0.1998 |
| smith_wrench_pairs_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | nan | 0.1511 |
| wrench_oracle | 1.0000 | 1.0000 | 0.0000 | 0.0000 | nan | 0.1277 |
| nash_pd_ring_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0001 | 0.02754 | 0.1680 |
| uniform_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0011 | nan | 0.0637 |
| nash_pd_exact_unguarded | 1.0000 | 0.6667 | 0.3333 | 0.0534 | 0.01163 | 0.1179 |
| wrench_greedy | 1.0000 | 0.5000 | 0.5000 | 0.0929 | nan | 0.0264 |
| cbba_slots | 1.0000 | 0.5000 | 0.5000 | 0.0931 | nan | 0.0263 |
| oracle_scalar_assignment | 1.0000 | 0.5000 | 0.5000 | 0.0932 | nan | 0.0195 |

## Hypotheses

| ID | Effect A-B | CI95 | p Holm | Reject |
|---|---:|---|---:|---|
| H-SP3-1-guard-reduces-fp | -0.33333 | [-0.58333, -0.08333] | 0.0625 | False |
| H-SP3-2-vector-beats-scalar-gap | -0.09323 | [-0.15581, -0.03552] | 0.03125 | True |
| H-SP3-3-pair-beats-cbba-gap | -0.09311 | [-0.15369, -0.03840] | 0.015625 | True |
| H-SP3-4-exact-beats-ring-kkt | -0.01591 | [-0.03767, -0.00146] | 0.026367 | True |

## Scope

- The KKT certificate applies to the convex force-utilisation relaxation.
- Integer robot/slot selection remains NP-hard.
- Population protocols are engine ablations on a shared wrench-price payoff.
- Guarded closure is mechanically certified but not fully distributed or globally optimal.
