# SP2_HETEROGENEOUS_GAME_v1_2

- Worlds: `480`
- Runs: `6720`
- Theory audit: `PASS`

## Summary

| method                       |   n |   served_rate_mean |   coverage_mean |   regret_mean |   regret_std |   raw_served_rate_mean |   convergence_rate |   potential_gain_mean |   messages_mean |   runtime_s_mean |
|:-----------------------------|----:|-------------------:|----------------:|--------------:|-------------:|-----------------------:|-------------------:|----------------------:|----------------:|-----------------:|
| milp_exact                   | 480 |            0.81181 |         0.88556 |       0       |      0       |                0.81181 |            1       |              nan      |     48          |       0.083028   |
| uniform_closure              | 480 |            0.59944 |         0.9092  |       0.24887 |      0.23814 |                0       |            1       |              nan      |     48          |       0.00066328 |
| replicator__marginal_log     | 480 |            0.56069 |         0.88194 |       0.28398 |      0.20648 |                0.53194 |            0.5625  |                5.5613 |      1.3472e+05 |       0.057775   |
| smith__marginal_log          | 480 |            0.55958 |         0.88047 |       0.28773 |      0.20929 |                0.54528 |            0.95625 |                5.6752 |      1.1013e+05 |       0.048541   |
| erv_bnn__marginal_log        | 480 |            0.55889 |         0.88314 |       0.28796 |      0.21003 |                0.54028 |            1       |                5.006  |      1.0135e+05 |       0.044037   |
| erv_bnn__marginal_deficit    | 480 |            0.53833 |         0.88799 |       0.30021 |      0.24688 |                0.31972 |            0.99167 |                1.1663 |  93104          |       0.040862   |
| replicator__marginal_deficit | 480 |            0.53583 |         0.88423 |       0.30171 |      0.23851 |                0.33403 |            0.63542 |                1.29   |      1.2207e+05 |       0.053565   |
| auction_capacity             | 480 |            0.52069 |         0.8875  |       0.31152 |      0.22791 |                0.52069 |            1       |              nan      |     48          |       0.00045378 |
| smith__marginal_deficit      | 480 |            0.52611 |         0.88144 |       0.31152 |      0.2445  |                0.32931 |            0.95    |                1.4972 |      1.0938e+05 |       0.049521   |
| replicator__plain_deficit    | 480 |            0.51986 |         0.86318 |       0.31953 |      0.25072 |                0.35694 |            0.80417 |              nan      |  94823          |       0.038129   |
| erv_bnn__plain_deficit       | 480 |            0.50875 |         0.87292 |       0.33399 |      0.26422 |                0.35    |            0.99375 |              nan      |  85216          |       0.03399    |
| smith__plain_deficit         | 480 |            0.50333 |         0.8657  |       0.33791 |      0.25726 |                0.36139 |            0.96042 |              nan      |      1.0118e+05 |       0.041415   |
| greedy_capacity              | 480 |            0.53417 |         0.77731 |       0.33836 |      0.21247 |                0.53417 |            1       |              nan      |     48          |       0.00086919 |
| random_closure               | 480 |            0.53139 |         0.86506 |       0.35244 |      0.22221 |                0.31611 |            1       |              nan      |     48          |       0.00076258 |

## Hypotheses

| id       | candidate                    | reference                 | metric            |   n_pairs |   effect_mean_paired |   ci95_low |   ci95_high |   p_value_raw | interpretation   |   p_value_holm | reject_holm_005   |
|:---------|:-----------------------------|:--------------------------|:------------------|----------:|---------------------:|-----------:|------------:|--------------:|:-----------------|---------------:|:------------------|
| H-SP2-1  | smith__marginal_deficit      | smith__plain_deficit      | normalized_regret |       480 |          -0.026387   | -0.043627  |  -0.010035  |    2.2281e-05 | candidate_better |     0.00017825 | True              |
| H-SP2-2  | replicator__marginal_deficit | replicator__plain_deficit | normalized_regret |       480 |          -0.017818   | -0.035121  |  -0.001527  |    0.0045035  | candidate_better |     0.022517   | True              |
| H-SP2-3  | erv_bnn__marginal_deficit    | erv_bnn__plain_deficit    | normalized_regret |       480 |          -0.033784   | -0.050145  |  -0.017637  |    1.3046e-07 | candidate_better |     1.1741e-06 | True              |
| H-SP2-4  | smith__marginal_log          | smith__plain_deficit      | normalized_regret |       480 |          -0.050184   | -0.070415  |  -0.030959  |    0.0018214  | candidate_better |     0.010929   | True              |
| H-SP2-5  | replicator__marginal_log     | replicator__plain_deficit | normalized_regret |       480 |          -0.035552   | -0.055701  |  -0.014766  |    0.052232   | candidate_better |     0.1567     | False             |
| H-SP2-6  | erv_bnn__marginal_log        | erv_bnn__plain_deficit    | normalized_regret |       480 |          -0.046034   | -0.065574  |  -0.024958  |    0.00062799 | candidate_better |     0.0043959  | True              |
| H-SP2-7  | erv_bnn__marginal_log        | smith__marginal_log       | normalized_regret |       480 |           0.00023264 | -0.007507  |   0.0085259 |    0.034274   | inconclusive     |     0.1371     | False             |
| H-SP2-8  | erv_bnn__marginal_log        | replicator__marginal_log  | normalized_regret |       480 |           0.0039775  | -0.0044069 |   0.012602  |    0.41207    | inconclusive     |     0.82414    | False             |
| H-SP2-9  | erv_bnn__marginal_log        | greedy_capacity           | normalized_regret |       480 |          -0.050405   | -0.07325   |  -0.028886  |    7.6863e-09 | candidate_better |     7.6863e-08 | True              |
| H-SP2-10 | erv_bnn__marginal_log        | auction_capacity          | normalized_regret |       480 |          -0.023561   | -0.043351  |  -0.0023694 |    0.78201    | candidate_better |     0.82414    | False             |
| H-SP2-11 | erv_bnn__marginal_log        | milp_exact                | normalized_regret |       480 |           0.28796    |  0.26915   |   0.30676   |    3.2449e-79 | reference_better |     3.5694e-78 | True              |

## Interpretation

- Fitness and revision protocols are crossed factorially.
- Plain deficit fitness is a heuristic under pair-dependent capacity.
- RAW preferences, capacity closure, and the MILP oracle are separate stages.
- Ring results are sensitivity evidence, not a time-varying-graph theorem.