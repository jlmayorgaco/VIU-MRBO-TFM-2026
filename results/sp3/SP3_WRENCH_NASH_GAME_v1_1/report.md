# SP3_WRENCH_NASH_GAME_v1_1

- Worlds: `600`
- Runs: `7200`
- Theory audit: `PASS`

## Summary

| Method | Coverage | Precision | FP assigned | Gap oracle | KKT | Runtime s |
|---|---:|---:|---:|---:|---:|---:|
| wrench_oracle | 1.0000 | 1.0000 | 0.0000 | 0.0000 | nan | 0.1179 |
| replicator_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.04188 | 0.1569 |
| erv_bnn_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.05836 | 0.1861 |
| smith_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.03123 | 0.2362 |
| smith_wrench_pairs_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | nan | 0.1406 |
| nash_pd_ring_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0001 | 0.02029 | 0.4710 |
| nash_pd_exact_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0002 | 0.002208 | 0.3021 |
| uniform_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0015 | nan | 0.0598 |
| nash_pd_exact_unguarded | 1.0000 | 0.6667 | 0.3333 | 0.0527 | 0.002208 | 0.3021 |
| cbba_slots | 1.0000 | 0.5000 | 0.5000 | 0.0933 | nan | 0.0239 |
| wrench_greedy | 1.0000 | 0.5000 | 0.5000 | 0.0934 | nan | 0.0237 |
| oracle_scalar_assignment | 1.0000 | 0.5000 | 0.5000 | 0.0935 | nan | 0.0197 |

## Hypotheses

| ID | Effect A-B | CI95 | p Holm | Reject |
|---|---:|---|---:|---|
| H-SP3-1-guard-reduces-fp | -0.33333 | [-0.37000, -0.29500] | 4.2739e-35 | True |
| H-SP3-2-vector-beats-scalar-gap | -0.09333 | [-0.10139, -0.08550] | 8.6392e-55 | True |
| H-SP3-3-pair-beats-cbba-gap | -0.09334 | [-0.10146, -0.08550] | 1.4822e-84 | True |
| H-SP3-4-exact-beats-ring-kkt | -0.01809 | [-0.02008, -0.01620] | 8.5475e-94 | True |

## Scope

- The KKT certificate applies to the convex force-utilisation relaxation.
- Integer robot/slot selection remains NP-hard.
- Population protocols are engine ablations on a shared wrench-price payoff.
- Guarded closure is mechanically certified but not fully distributed or globally optimal.
