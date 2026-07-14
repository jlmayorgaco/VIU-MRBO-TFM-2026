# SP4 result status

Canonical evidence: SP4_DOCKING_GAME_CONFIRMATORY_v3.

- Config: configs/experiments/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3.yaml
- Worlds/runs: 108 / 1,188
- Theory audit: PASS
- Initial collisions: 0
- Scope: fixed-payload safe recruitment to SP3 contact poses on a dynamic-unicycle plant.

Retained but non-canonical:

- SP4_DOCKING_GAME_CONFIRMATORY_v2: invalid for inference because 20/108 generated worlds started in collision. It triggered the initial-clearance gate added in v3.
- SP4_DOCKING_GAME_PILOT_v3: feasibility pilot used to validate the repaired generator; its seed is excluded from v3.
- SP4_DOCKING_GAME_PILOT_v2: tuning pilot.
- Historical SP4_MC_* campaigns: reduced-plant context only; they do not support the v3 game/KKT/RAW-SAFE-EXEC claims.

Canonical v3 does not establish global motion optimality, fully distributed closure, physical payload transport, or robustness to wheel-torque saturation. No torque saturation event occurred in v3.