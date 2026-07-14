# SP0 experiment configurations

Use `results/sp0/PROTOCOL_INDEX.md` as the authoritative lifecycle and evidence register.

## Active evidence configuration

`SP0_PROTOCOL_v1_2_CPU.yaml` defines the completed CPU-only campaign. Its reduced 1.12M-transition training schedule is an explicit resource constraint, while B0 and B2-B7 retain the full 15,436 base-evaluation design.

The immutable protocol used for inference is the frozen copy under `results/sp0/SP0_PROTOCOL_v1_2_CPU/protocol/`, not a later edit of this source YAML.

## Superseded configuration

`SP0_PROTOCOL_v1_1.yaml` defines the 26M-transition full-budget design. Its CPU execution was stopped before freeze and before confirmatory seed opening. It must not be resumed or described as complete.

## Training policy

For the current TFM:

1. Do not retrain SP0 merely to increase step count.
2. Treat the three v1.2 final MAPPO checkpoints as fixed resource-constrained baselines.
3. Attribute RAW policy behavior separately from ARG, REPAIR, QR1, QR2 and QRA.
4. Keep checkpoint/decoder limitations visible in every data-driven claim.
5. Allocate remaining effort to protocol clarity, failure preservation, paired worlds, closure ablation, statistical validity and manuscript traceability.

Any future training or fresh confirmatory worlds require a new `SP0_PROTOCOL_v1_3` configuration and new disjoint seeds. Never modify the v1.2 frozen files in place.
