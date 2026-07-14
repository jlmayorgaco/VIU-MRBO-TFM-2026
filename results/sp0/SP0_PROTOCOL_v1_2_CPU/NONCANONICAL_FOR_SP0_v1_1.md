# Noncanonical notice for SP0_PROTOCOL_v1.1

The artifacts in this directory are preserved and must not be deleted, but they do not satisfy the SP0_PROTOCOL_v1.1 closure contract.

The CPU-specific revision reduced DD-1 to 10,000 steps, DD-2 to 50,000 steps, and each final seed to 200,000 steps. SP0 v1.1 requires 250,000, 1,000,000, and 5,000,000 steps respectively, totaling 26,000,000 joint environment transitions. Therefore the historical SP0_COMPLETE label in this directory is scoped only to the reduced resource experiment and is not evidence that SP0 v1.1 is closed.

The canonical v1.1 runner now rejects reduced budgets before training/readiness/freeze. The preserved v1.2 results must not be merged into, renamed as, or cited as confirmatory SP0 v1.1 results.