# SP2 heterogeneous v1.1: quality-valid, runtime-superseded

The theory audit and quality endpoints passed. However, the `milp_exact` row timed
solution replay rather than the centralized solver call. Version v1.2 measures the
solver-inclusive runtime and uses fresh seeds. No payoff, method, factor, hypothesis,
or quality metric changed.
