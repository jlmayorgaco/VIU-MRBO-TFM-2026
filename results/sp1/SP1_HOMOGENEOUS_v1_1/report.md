# SP1_HOMOGENEOUS_v1_1

## Scope

Homogeneous robots and loads with common quorum q. The q=1 case is the legacy one-to-one boundary; q>1 is homogeneous cooperative recruitment.

- Worlds: `900`
- Runs: `7200`
- Theory audit: `PASS`

## Summary

| method          |   n |   raw_valid_rate |   raw_coverage_mean |   final_valid_rate |   final_coverage_mean |   normalized_regret_mean |   normalized_regret_std |   distance_m_mean |   convergence_rate |   potential_gain_mean |   messages_mean |   runtime_s_mean |
|:----------------|----:|-----------------:|--------------------:|-------------------:|----------------------:|-------------------------:|------------------------:|------------------:|-------------------:|----------------------:|----------------:|-----------------:|
| hungarian_exact | 900 |        1         |             1       |                  1 |                     1 |                 0        |                0        |            82.527 |            1       |             nan       |    224          |       7.7211e-05 |
| auction_proxy   | 900 |        1         |             1       |                  1 |                     1 |                 0.029763 |                0.055295 |            83.919 |            1       |             nan       |    224          |       0.0006649  |
| uniform_qr      | 900 |        0         |             0.11458 |                  1 |                     1 |                 0.044368 |                0.066325 |            84.323 |            1       |             nan       |     16          |       0.00028936 |
| bnn_qr          | 900 |        0.054444  |             0.71079 |                  1 |                     1 |                 0.051405 |                0.090322 |            85.241 |            0.50333 |               0.59582 |      7.1579e+05 |       0.060442   |
| smith_qr        | 900 |        0.016667  |             0.62354 |                  1 |                     1 |                 0.059651 |                0.10815  |            85.811 |            0.34556 |               0.89076 |      8.159e+05  |       0.078177   |
| greedy          | 900 |        1         |             1       |                  1 |                     1 |                 0.08081  |                0.10947  |            86.511 |            1       |             nan       |     16          |       0.00018445 |
| replicator_qr   | 900 |        0.011111  |             0.71488 |                  1 |                     1 |                 0.086197 |                0.098895 |            88.27  |            0.69333 |               0.25292 |      3.128e+05  |       0.031625   |
| random_qr       | 900 |        0.0033333 |             0.69231 |                  1 |                     1 |                 0.46601  |                0.61077  |           103.35  |            1       |             nan       |     16          |       0.00060726 |

## Paired hypotheses

| id      | candidate   | reference       | metric            |   n_pairs |   effect_mean_paired |   ci95_low |   ci95_high |   p_value_raw | interpretation   |   p_value_holm | reject_holm_005   |
|:--------|:------------|:----------------|:------------------|----------:|---------------------:|-----------:|------------:|--------------:|:-----------------|---------------:|:------------------|
| H-SP1-1 | smith_qr    | greedy          | normalized_regret |       900 |            -0.021159 | -0.028352  |   -0.014087 |   8.831e-12   | candidate_better |    1.7662e-11  | True              |
| H-SP1-2 | smith_qr    | auction_proxy   | normalized_regret |       900 |             0.029889 |  0.023576  |    0.035792 |   1.6031e-18  | reference_better |    4.8092e-18  | True              |
| H-SP1-3 | smith_qr    | uniform_qr      | normalized_regret |       900 |             0.015283 |  0.0092164 |    0.021382 |   0.0029007   | reference_better |    0.0029007   | True              |
| H-SP1-4 | smith_qr    | random_qr       | normalized_regret |       900 |            -0.40636  | -0.44398   |   -0.37087  |   6.4363e-148 | candidate_better |    3.2182e-147 | True              |
| H-SP1-5 | smith_qr    | hungarian_exact | normalized_regret |       900 |             0.059651 |  0.052978  |    0.06693  |   5.9376e-131 | reference_better |    2.375e-130  | True              |

## Interpretation contract

- Population dynamics, argmax decoding, and integer closure are separate stages.
- Hungarian is a centralized exact reference, not a deployable distributed method.
- The ring graph is a fixed connected sensitivity condition; time-varying graphs are outside SP1.
- A successful closure does not prove that the continuous dynamic reached an integer equilibrium.
