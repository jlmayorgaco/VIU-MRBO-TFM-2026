# Follow-up experimental campaign QA

This report is generated from campaign manifests. A missing manifest is recorded as `not_run`; it is never treated as a zero, a failure, or a success. CPU campaigns remain evidence about the implemented reduced-order protocols, not proof of global stability, optimality, or physical-world robustness.

Manifest coverage at generation time: 8/8 campaigns present.

| Campaign | Present | Status | Audit | Evidence | Runs | Git commit | Dirty |
|---|---:|---|---|---|---:|---|---|
| `SP1_CANONICAL_CONFIRMATORY_v1` | true | complete | passed | B-target | 3960 | `ea11dacab62a7c75b49b6847456cb1ce23d777bb` | True |
| `SP2_HONORS_v3` | true | complete | PASS |  | 2100 | `ea11dacab62a7c75b49b6847456cb1ce23d777bb` |  |
| `SP5_PAYLOAD_TRANSPORT_PILOT_v2` | true | complete | PASS |  | 288 | `` |  |
| `SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2` | true | complete | PASS |  | 864 | `` |  |
| `SP6_RECOVERY_CONFIRMATORY` | true | complete | passed | B | 2400 | `` |  |
| `SP7_TRAFFIC_CONFIRMATORY` | true | complete | passed | C | 1800 | `` |  |
| `SP8_NETWORK_CONFIRMATORY` | true | complete | passed | C | 4500 | `` |  |
| `CARGO_E2E_CONFIRMATORY_v1` | true | complete | passed |  | 2160 | `` |  |

## Gate and interpretation notes

- SP1 and SP2 are the canonical CPU campaigns and must be read together with their frozen configuration, raw runs, audit, and generated tables.
- SP5 confirmatory execution is valid only after the pilot writes a PASS theory audit and the confirmatory seed-opening event is present.
- CARGO_E2E_CONFIRMATORY is intentionally not inferred from CPU smoke output. Its physical Coppelia run requires preflight evidence and explicit authorization.
- Any campaign with `git_dirty=true` records the repository state at execution time; this reflects the shared worktree and does not mean result rows are invalid, but the exact frozen config and commit must be retained.
- The Web of Science export is an external literature gate, not an experiment; the current session requires institutional authentication and has not been exported.
