# SP0 learning and decoder audit

## Verdict

**Checkpoint loading is real; learned discrete behavior is not demonstrated. Promotion of SP0 MAPPO/IPPO performance claims is blocked.**

The read-only audit is `results/sp0/SP0_AUDIT_v1/SP0_AUDIT_REPORT.md`. It evaluated an untrained random actor, a uniform-logit control, seed-15001 snapshots near 50k/100k/150k/200k steps, all three 200k final seeds, and a controlled perturbation on the same six reconstructed validation worlds.

## What the tests establish

1. Checkpoint files and model-state fingerprints are distinct.
2. The requested file hash equals the effective file hash after load.
3. World observations/hashes vary and are paired across checkpoints.
4. Logits vary between checkpoints and seeds; a controlled weight perturbation changes logits.
5. Cache keys differ by checkpoint and include the full common provenance tuple.
6. RAW and repaired assignments are retained independently by the auditor.

## What fails

- Random actor, uniform-logit control, every audited snapshot, all three final seeds, and the perturbed final actor produce **identical RAW assignments on all six worlds**: mean RAW Hamming distance is 0 and the proportion of worlds with different RAW assignment is 0.
- RAW success is 0.0 for every control/checkpoint. Repair success is 1.0 for every control/checkpoint.
- Mean RAW and repaired regret are identical across the controls/checkpoints on this set. The policy scores change but the iterative argmax collapses to the same discrete output.
- The historical evaluator has RAW plus one `POLICY_REPAIR` result. It does not provide immutable, independent REPAIR and QR stages.
- The three historical validation histories repeat exactly the same aggregate success, raw success, regret, CVaR, and closure delta at every checkpoint. Only inference timing and training losses change.

## Decoder dependency

The decoder/repair is the operative assignment algorithm in the audited worlds. This does not mean the neural network is never useful, but the current data do not demonstrate that it changes the executable RAW decision or outperforms random/uniform before closure. Closed performance must be attributed to deterministic repair, not to learned allocation.

Allowed wording: “A checkpoint-backed MAPPO-GNN score generator was evaluated, but its audited RAW actions matched random/uniform controls; deterministic repair supplied feasible maximum-cardinality assignments.”

Forbidden wording: “MAPPO learned the assignment policy,” “training converged to optimal behavior,” or “MAPPO achieved perfect success,” without a stage qualifier and new evidence.

## Saturation and leakage

The validation set is saturated **after repair**, not before it: every control reaches repair success 1.0. Split leakage is not proven, but neither is full isolation: SP0’s training status contradicts seed-opening state, and the validation-world registry is reconstructed from evaluator code rather than stored as a sealed first-class registry. This is a governance failure even without evidence of data leakage.

## Required v1.3 remediation (not executed)

1. Persist validation world registry and hash before training.
2. Store per-world logits, RAW assignment, REPAIR assignment, QR assignment, and runtimes.
3. Require RAW superiority to random and uniform controls on preregistered metrics.
4. Add decoder-only, policy-only, shuffled-policy, and perturbed-policy ablations.
5. Define `training_budget_completed`, `raw_policy_converged`, `validation_plateau_detected`, `early_stopping_triggered`, and `optimizer_updates_completed` separately.
6. Never use repaired success to declare policy convergence.
7. Keep confirmatory seeds sealed until the common lifecycle and rebuild gates pass.

No v1.3 training or confirmatory execution was started.
