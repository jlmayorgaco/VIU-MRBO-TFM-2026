# SP1_HOMOGENEOUS_v1

## Scope

Homogeneous robots and loads with common quorum q. The q=1 case is the legacy one-to-one boundary; q>1 is homogeneous cooperative recruitment.

- Worlds: `900`
- Runs: `7200`
- Theory audit: `FAIL`

## Summary

| method          |   n |   raw_valid_rate |   raw_coverage_mean |   final_valid_rate |   final_coverage_mean |   normalized_regret_mean |   normalized_regret_std |   distance_m_mean |   convergence_rate |   potential_gain_mean |   messages_mean |   runtime_s_mean |
|:----------------|----:|-----------------:|--------------------:|-------------------:|----------------------:|-------------------------:|------------------------:|------------------:|-------------------:|----------------------:|----------------:|-----------------:|
| hungarian_exact | 900 |        1         |             1       |                  1 |                     1 |                 0        |                0        |            82.469 |                  1 |             nan       |    224          |         0        |
| auction_proxy   | 900 |        1         |             1       |                  1 |                     1 |                 0.027528 |                0.050499 |            83.837 |                  1 |             nan       |    224          |         0        |
| uniform_qr      | 900 |        0         |             0.11458 |                  1 |                     1 |                 0.044501 |                0.069934 |            84.316 |                  1 |             nan       |     16          |         0        |
| bnn_qr          | 900 |        0.052222  |             0.70287 |                  1 |                     1 |                 0.055758 |                0.096776 |            85.678 |                  0 |               0.58716 |      3.7056e+05 |         0.033363 |
| replicator_qr   | 900 |        0.0055556 |             0.69653 |                  1 |                     1 |                 0.060441 |                0.076829 |            85.965 |                  0 |               0.27405 |      3.7056e+05 |         0.032674 |
| smith_qr        | 900 |        0.0066667 |             0.53785 |                  1 |                     1 |                 0.068154 |                0.12196  |            86.12  |                  0 |             -26.968   |      3.7056e+05 |         0.035878 |
| greedy          | 900 |        1         |             1       |                  1 |                     1 |                 0.083191 |                0.11442  |            86.56  |                  1 |             nan       |     16          |         0        |
| random_qr       | 900 |        0.0077778 |             0.69752 |                  1 |                     1 |                 0.45222  |                0.58249  |           103.07  |                  1 |             nan       |     16          |         0        |

## Paired hypotheses

| id      | candidate   | reference       | metric            |   n_pairs |   effect_mean_paired |   ci95_low |   ci95_high |   p_value_raw | interpretation   |   p_value_holm | reject_holm_005   |
|:--------|:------------|:----------------|:------------------|----------:|---------------------:|-----------:|------------:|--------------:|:-----------------|---------------:|:------------------|
| H-SP1-1 | smith_qr    | greedy          | normalized_regret |       900 |            -0.015036 |  -0.02249  |  -0.0080352 |   1.315e-08   | candidate_better |    1.315e-08   | True              |
| H-SP1-2 | smith_qr    | auction_proxy   | normalized_regret |       900 |             0.040627 |   0.034008 |   0.047157  |   3.7054e-38  | reference_better |    1.1116e-37  | True              |
| H-SP1-3 | smith_qr    | uniform_qr      | normalized_regret |       900 |             0.023653 |   0.017044 |   0.030026  |   4.099e-17   | reference_better |    8.1981e-17  | True              |
| H-SP1-4 | smith_qr    | random_qr       | normalized_regret |       900 |            -0.38407  |  -0.41786  |  -0.3501    |   3.1686e-148 | candidate_better |    1.5843e-147 | True              |
| H-SP1-5 | smith_qr    | hungarian_exact | normalized_regret |       900 |             0.068154 |   0.060368 |   0.076693  |   2.8012e-131 | reference_better |    1.1205e-130 | True              |

## Interpretation contract

- Population dynamics, argmax decoding, and integer closure are separate stages.
- Hungarian is a centralized exact reference, not a deployable distributed method.
- The ring graph is a fixed connected sensitivity condition; time-varying graphs are outside SP1.
- A successful closure does not prove that the continuous dynamic reached an integer equilibrium.
