# Re-review verification report

## Scope

This re-review verifies only the six Round 1 revision items against the revised manuscript, compiled PDF, computational audit and local submit-ready gate. It does not introduce new experiments or re-score unrelated criteria.

## Verification matrix

| ID | Required change | Evidence in revised manuscript | Status |
|---|---|---|---|
| R1 | Identify FULL as a global replacement proxy, not end-to-end local recovery. | Abstract and Resumen disclose global candidates; Sections 6.1 and 7 state that the selector enumerates all idle robots. The code audit records the same limitation. | VERIFIED |
| R2 | Attribute the +0.62 contrast to the complete FULL bundle. | Sections 6.1 and 7 name the full package and explicitly deny separate identification of messages, memory and replacement. | VERIFIED |
| R3 | Bound the common-Lyapunov result to a derived application under assumptions. | Theorem 5.1 keeps fixed-load, no-reset and bounded-input assumptions adjacent to the statement; Section 7 calls it a derived theoretical application and lists excluded cases. | VERIFIED |
| R4 | State that 100 worlds is a hard cap, not proof that every CI met the target. | Sections 4.6, 6.1 and 7 make the distinction explicitly. | VERIFIED |
| S1 | Disclose absence of post-hoc sensitivity for frozen constants. | Section 7 lists the wrench threshold, HOCBF gains and 22-s horizon. | VERIFIED |
| S2 | Prevent scenario frequencies from being read as industrial prevalence. | Section 7 restricts frequencies to the synthetic generator. | VERIFIED |
| S3 | Rebuild and rerun gates. | PDF: 67 pages; local gate: zero blockers, one warning for the absent external similarity report; V1--V3 pass independently. | VERIFIED |

## Regression checks

- The revised PDF retains Sections 1--7, references and Appendices A--D.
- Main matter is 56/80 pages and appendices are 7/8 pages under the local VIU gate.
- The seed registry remains immutable and its SHA-256 matches the frozen manifest; seed opening is recorded separately.
- The integrated campaign remains 960/960 base runs and 2,160 total unique rows with zero numerical errors.
- The adverse findings remain visible: A2--A3 decreases success under scarcity, FULL retains 14% collision failures in the obstacle/dropout family, and the selector is not graph-local.
- The concurrent SP4 v3 integration was rechecked against its 108-world manifest: the conclusion reports 0.2685 safe success, 0.7315 timeouts, zero swept collisions for guarded methods, no observed torque saturation and no continuous-safety claim.

## Re-review conclusion

All Round 1 scientific and editorial revisions are VERIFIED. No new major or minor scientific issue was introduced by the revision. The thesis is acceptable on academic-content grounds. Final institutional submission remains administratively contingent on obtaining and reviewing the external similarity report; the local gate cannot replace that service.