# SP0_DEBUG_smoke

SP0 homogeneous one-to-one assignment executed with cached worlds, Hungarian oracle, distributed baselines, population dynamics and integer closures.

- Runs: `288`
- Theory failed checks: `0`
- Best all-block method: `HUN`
- Parquet files: `3`

## Hypotheses
- `H0-SP0-debug-GRD-vs-HUN-regret`: p=1.042e-06, Holm reject=True.
- `H0-SP0-debug-DA-vs-GRD-regret`: p=0.2236, Holm reject=False.

## Primary Ranking
- ALL_BLOCKS rank 1: `HUN` success=1.000, NR=0.0000, runtime=0.002 ms.
- ALL_BLOCKS rank 2: `HYB` success=1.000, NR=0.0000, runtime=19.123 ms.
- ALL_BLOCKS rank 3: `LOG` success=1.000, NR=0.0005, runtime=19.967 ms.
- ALL_BLOCKS rank 4: `REP` success=1.000, NR=0.0005, runtime=12.579 ms.
- ALL_BLOCKS rank 5: `SMI` success=1.000, NR=0.0007, runtime=15.374 ms.
- ALL_BLOCKS rank 6: `PROJ` success=1.000, NR=0.0007, runtime=20.019 ms.
- ALL_BLOCKS rank 7: `BNN` success=1.000, NR=0.0017, runtime=17.459 ms.
- ALL_BLOCKS rank 8: `DA` success=1.000, NR=0.0020, runtime=0.134 ms.
- ALL_BLOCKS rank 9: `GRD` success=1.000, NR=0.0024, runtime=0.068 ms.
- debug_nominal rank 1: `HUN` success=1.000, NR=0.0000, runtime=0.002 ms.
- debug_nominal rank 2: `HYB` success=1.000, NR=0.0000, runtime=19.123 ms.
- debug_nominal rank 3: `LOG` success=1.000, NR=0.0005, runtime=19.967 ms.
- debug_nominal rank 4: `REP` success=1.000, NR=0.0005, runtime=12.579 ms.
- debug_nominal rank 5: `SMI` success=1.000, NR=0.0007, runtime=15.374 ms.
