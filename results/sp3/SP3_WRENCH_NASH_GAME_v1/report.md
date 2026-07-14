# SP3_WRENCH_NASH_GAME_v1

- Worlds: `600`
- Runs: `7200`
- Theory audit: `FAIL`

## Summary

| Method | Coverage | Precision | FP assigned | Gap oracle | KKT | Runtime s |
|---|---:|---:|---:|---:|---:|---:|
| wrench_oracle | 1.0000 | 1.0000 | 0.0000 | 0.0000 | nan | 0.1202 |
| erv_bnn_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.05816 | 0.1902 |
| replicator_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0419 | 0.1590 |
| smith_price_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.03064 | 0.2383 |
| smith_wrench_pairs_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | nan | 0.1447 |
| nash_pd_exact_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.007941 | 0.1418 |
| nash_pd_ring_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0001 | 0.0235 | 0.1989 |
| uniform_guarded | 1.0000 | 1.0000 | 0.0000 | 0.0015 | nan | 0.0615 |
| nash_pd_exact_unguarded | 1.0000 | 0.6667 | 0.3333 | 0.0522 | 0.007941 | 0.1424 |
| oracle_scalar_assignment | 1.0000 | 0.5000 | 0.5000 | 0.0932 | nan | 0.0198 |
| cbba_slots | 1.0000 | 0.5000 | 0.5000 | 0.0934 | nan | 0.0243 |
| wrench_greedy | 1.0000 | 0.5000 | 0.5000 | 0.0934 | nan | 0.0242 |

## Hypotheses

| ID | Effect A-B | CI95 | p Holm | Reject |
|---|---:|---|---:|---|
| H-SP3-1-guard-reduces-fp | -0.33333 | [-0.37167, -0.29667] | 4.2739e-35 | True |
| H-SP3-2-vector-beats-scalar-gap | -0.09317 | [-0.10145, -0.08482] | 8.5468e-50 | True |
| H-SP3-3-pair-beats-cbba-gap | -0.09335 | [-0.10177, -0.08501] | 1.139e-84 | True |
| H-SP3-4-exact-beats-ring-kkt | -0.01556 | [-0.01755, -0.01370] | 1.4032e-78 | True |

## Scope

- The KKT certificate applies to the convex force-utilisation relaxation.
- Integer robot/slot selection remains NP-hard.
- Population protocols are engine ablations on a shared wrench-price payoff.
- Guarded closure is mechanically certified but not fully distributed or globally optimal.
