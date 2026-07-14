# SP3 v1 is non-canonical

The frozen v1 campaign completed 600 worlds and 7200 runs, but its theory audit failed.
The maximum projected-primal-dual potential gap against the independent convex QP
reference was 0.019722, above the preregistered 0.01 gate. The failure concentrated
in the slot-saturation scenario and was diagnosed as an insufficient 500-iteration
horizon: on the worst v1 world the same field reached gaps 0.006214 at 800 iterations
and 0.001330 at 1200 iterations.

SP3_WRENCH_NASH_GAME_v1_1 therefore changes only the projected-primal-dual horizon
to 1200 iterations and uses fresh seeds 461000--461099. Scenarios, payoff, physical
model, closures, baselines, hypotheses, statistical tests and the 0.01 audit gate remain
unchanged. The v1 quality results are retained for provenance but must not be cited as
canonical evidence.
