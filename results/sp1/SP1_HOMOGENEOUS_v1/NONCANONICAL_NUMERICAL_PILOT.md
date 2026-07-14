# SP1 homogeneous v1: noncanonical numerical pilot

This run is excluded from thesis claims. Its fixed-step Euler implementation of
the Smith protocol overshot the continuous potential-ascent field and failed the
predeclared monotonicity audit. It is retained as an immutable diagnostic record.

The confirmatory run `SP1_HOMOGENEOUS_v1_1` uses a bounded positive per-player
time rescaling, a smaller integration step, a longer horizon, and fresh seeds.
The payoff, potential, comparators, factors, and hypotheses were not changed in
response to the pilot outcomes.
