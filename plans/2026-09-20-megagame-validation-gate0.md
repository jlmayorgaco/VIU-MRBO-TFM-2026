# MegaGame canonical validation and Gate 0

**Date:** 2026-09-20  
**Status:** in progress; Gate 0 implementation only.

## Objective

Audit `MROB_MEGAGAME_CANONICAL_PACKAGE_20260919.zip`, freeze a validation plan,
and implement deterministic mathematical/physical checks before any Monte Carlo
or production rewrite.

## Assumptions and boundaries

- Existing worktree changes are user-owned and must remain untouched.
- The package is an engineering baseline, not a source of new theorem claims.
- Cargo is the primary physical branch; Caging has separate unilateral-contact
  assumptions.
- The canonical reference is smoke-tested only in this phase.
- No parameter tuning, S03--S06 campaign, CoppeliaSim run or remote push.

## Work items

- [x] Read repository source-of-truth documents and package specification.
- [x] Extract the ZIP outside the repository and run its validator, smoke test,
      pytest and compile check.
- [x] Add `experiments/validation_v1/VALIDATION_PLAN.md`.
- [x] Add deterministic Gate 0 primitives and tests.
- [x] Run the new Gate 0 command against the extracted package and preserve its
      generated summary.
- [ ] Implement Gate 1 controller/evaluator information-boundary audit.

## Acceptance evidence

The acceptance record must include the exact package path, current git SHA,
commands, test counts, package checksum status, scenarios completed, failures,
and output paths. Gate 0 must fail closed on missing required files, invalid
YAML, checksum mismatch, non-finite numerical values or violated invariant.

## Phase result

Gate 0 passed at commit `bed9f22810ff316423561d1f9f69f0129dfee413` for the
extracted package under `C:\Users\walla\AppData\Local\Temp\mrob_megagame_audit_20260920_01`.
The targeted suite passed 6 tests, the package audit checked 238 declared
checksums and all 10 YAML files, and S00--S02 reference smoke runs completed.
The repository-wide suite was started but showed pre-existing failures in the
dirty worktree before completion; it is not used as Gate 0 acceptance evidence.
