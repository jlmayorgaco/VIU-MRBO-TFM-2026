# SP0 protocol register

Authoritative status as of 2026-07-12. This register separates protocol validity, execution state and claim scope. Directory names alone do not establish evidentiary status.

## Decision

`SP0_PROTOCOL_v1_2_CPU` is the canonical completed SP0 campaign for this CPU-only TFM. Its scope is explicitly `resource_constrained_cpu_budget`; it is not equivalent to the abandoned 26M-transition v1.1 training claim.

No additional SP0 training is required for the current document. The three frozen v1.2 MAPPO checkpoints remain fixed evaluation units. Any future campaign using different checkpoints or worlds must receive a new protocol version and fresh disjoint seeds.

## Version hierarchy

| Version | Lifecycle state | Confirmatory seeds | Evidentiary role |
|---|---|---|---|
| `SP0_PROTOCOL_v1` | Archived pre-correction | Historical registry only | Superseded; retained for provenance, not current evidence |
| `SP0_PROTOCOL_v1_1` | Stopped pre-freeze on 2026-07-12 | Never opened | Full-budget engineering attempt; B0/dry-run and six IPPO DD-1 checkpoints only; not a completed campaign |
| `SP0_PROTOCOL_v1_2_CPU` | Frozen and complete | Opened only after freeze and final checkpoint hashing | Canonical CPU campaign with restricted training claims |
| `SP0_AUDIT_v1` | Post-hoc read-only audit | Not applicable | Qualification layer for checkpoint, decoder, failure and statistical-claim limitations |

## Canonical evidence

- Configuration: `configs/experiments/sp0/SP0_PROTOCOL_v1_2_CPU.yaml`.
- Frozen protocol: `results/sp0/SP0_PROTOCOL_v1_2_CPU/protocol/frozen_protocol_v1_2_cpu.yaml`.
- Frozen manifest: `results/sp0/SP0_PROTOCOL_v1_2_CPU/protocol/frozen_manifest_v1_2_cpu.json`.
- Seed-opening event: `results/sp0/SP0_PROTOCOL_v1_2_CPU/protocol/confirmatory_seed_opening.json`.
- Final manifest: `results/sp0/SP0_PROTOCOL_v1_2_CPU/FINAL_RUN_MANIFEST.json`.
- Final report: `results/sp0/SP0_PROTOCOL_v1_2_CPU/FINAL_REPORT.md`.
- Qualification audit: `results/sp0/SP0_AUDIT_v1/SP0_AUDIT_REPORT.md`.

The frozen lifecycle records three final MAPPO checkpoints of exactly 200,000 joint environment transitions each. Freeze followed final checkpoint creation; the confirmatory seed-opening event followed freeze. The final manifest records B0=300, B2=2,400, B3=1,536, B4=5,760, B5=4,000, B6=960 and B7=480, for 15,436 base evaluations.

## Interpretation contract

Allowed statements:

- SP0 v1.2 executed a frozen 15,436-evaluation CPU campaign plus precision-triggered extensions.
- IPPO and MAPPO were implemented and tuned under the declared reduced CPU budget.
- Three independently seeded final MAPPO checkpoints were retained without seed replacement.
- Continuous, decoded and closure-assisted outcomes are reported as separate stages.
- B2 dynamic-fitness results are exploratory; registered P/C/R families provide the confirmatory structure.

Required qualifications:

- The 10k/50k/200k schedule is resource-constrained and must not be described as equivalent to 250k/1M/5M training.
- Audited MAPPO RAW assignments have zero success on the sampled worlds; closed success is dominated by repair/closure.
- Different checkpoint parameters and logits do not establish different discrete RAW behavior.
- Hypotheses with non-finite estimates or intervals remain unsupported regardless of rendered p-values.
- Massive continuous timeout rates prohibit claims of general continuous convergence.

Forbidden statements:

- `SP0_PROTOCOL_v1_1` is complete.
- MAPPO learned perfect assignments.
- Closure-assisted success proves policy-learning success.
- All SP0 hypotheses are statistically supported.
- Observed price of anarchy is a theoretical bound.
- Results validate physical robots, contact dynamics or industrial safety.

## Execution policy

Do not restart the v1.1 watchdog or its 26M command. Preserve `results/sp0/SP0_PROTOCOL_v1_1/` as immutable pre-freeze engineering evidence. Rebuild v1.2 tables, plots or videos only from its frozen raw artifacts; do not retrain or replace its checkpoints. A genuinely new confirmatory execution requires `SP0_PROTOCOL_v1_3`, a new freeze and seed groups disjoint from every v1/v1.1/v1.2 seed.
