# Protocol deviations and scope decisions

- 2026-07-11: The campaign is CPU-only because no GPU is available. No training budget is reduced because the campaign contains no new MARL training.
- 2026-07-11: SP0 v1.2 remains the canonical resource-constrained assignment campaign; this protocol does not reopen or tune it.
- 2026-07-11: Legacy SP1/SP7/SP8 evidence is not promoted. Their open mechanics/network questions are tested jointly through a new certificate ladder.
- 2026-07-11: The dynamic actuator uses bounded signed traction after a unilateral static rigid-grasp certificate. This is required for braking and is stated as a model assumption.
- 2026-07-11: A deterministic nominal waypoint is used in the obstacle family before the HOCBF filter. The waypoint is not counted as a safety certificate.
- Confirmatory seeds remain unopened until frozen_manifest.json has status `frozen_ready_for_execution`.