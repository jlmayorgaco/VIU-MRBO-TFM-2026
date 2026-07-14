# SP0a_BLOCKING_REPORT

**Status:** `BLOCKED — no confirmatory SP0 evidence available`
**Action taken:** Insertion of subchapter *6.1 SP0a* into the TFM is **halted**. No claims, no placeholders, no figures with invented numbers were written.
**Generated:** 2026-07-10 (repo-local audit; source manifests stamped 2026-07-11 UTC)
**Auditor:** Claude Code (automated preflight per SP0a instructions §2, §27)

---

## 1. Decision

The SP0a subchapter **cannot be drafted with confirmatory claims**. The final SP0 Monte Carlo campaign required by the task instructions does **not exist in a completed, frozen, confirmatory state** in this repository. The only fully-passing artifact is **B0 (implementation validation)**, which the instructions explicitly forbid using as scientific comparison evidence (§2 exclusion list; §Jerarquía de evidencia point 5).

Both candidate campaign directories were audited. Neither satisfies the gate defined in §2.

---

## 2. Gate evaluation — `results/sp0/SP0_PROTOCOL_v1_1/FINAL_RUN_MANIFEST.json`

This is the campaign named as the primary target in §2. Its manifest is a **dry run**, not a confirmatory run.

| Gate requirement (§2)            | Required           | Found in manifest                                  | Pass |
|----------------------------------|--------------------|----------------------------------------------------|------|
| `status = completed`             | `completed`        | `"status": "dry_run_complete"` (top-level)         | ❌ |
| `protocol_frozen = true`         | `true`             | field **absent**                                   | ❌ |
| `B0 passed`                      | passed             | `b0.passed = true` (387 checks, 0 failed)          | ✅ |
| `B2 count = 2400`                | 2400               | field **absent**; `b2/` dir **empty (0 files)**    | ❌ |
| `B3 count = 1536`                | 1536               | field **absent**; `b3/` dir **empty (0 files)**    | ❌ |
| `B4 count = 5760`                | 5760               | field **absent**; `b4/` dir **empty (0 files)**    | ❌ |
| `B5 count = 4000`                | 4000               | field **absent**; `b5/` dir **empty (0 files)**    | ❌ |
| `B6 count = 960`                 | 960                | field **absent**; `b6/` dir **empty (0 files)**    | ❌ |
| `B7 count = 480`                 | 480                | field **absent**; `b7/` dir **empty (0 files)**    | ❌ |
| three final data-driven seeds    | present + valid    | 3 seeds present but `artifact_scope="dry_run_only"`, `confirmatory_seeds_opened=false`, all `training_converged=false` | ❌ |
| confirmatory statistics completed| completed          | `statistics/` dir **empty**; no `statistics/*.parquet` | ❌ |
| Holm correction completed        | completed          | no `hypotheses/` dir; only `smoke/hypotheses.parquet` (excluded) | ❌ |

**Manifest self-declaration (verbatim keys):**
- top-level `"dry_run": true`
- top-level `"status": "dry_run_complete"`
- `data_driven_training.status = "dry_run_complete"`, `artifact_scope = "dry_run_only"`, `champion_id = "MAPPO-GNN"`, `confirmatory_seeds_opened = false`
- every DD seed (train_seed 15001/15002/15003): `training_converged = false`, `optimizer_updates = 2`, `training_steps = 4096` (i.e. a smoke-scale trainer, not the pre-registered budget)
- `integral_dry_run.exploratory_debug_only = true`

**On-disk reality (v1_1):**
```
b0          : 12 files (7 parquet)  ← implementation validation only
b2          : 0 files   (EMPTY)
b3          : 0 files   (EMPTY)
b4          : 0 files   (EMPTY)
b5          : 0 files   (EMPTY)
b6          : 0 files   (EMPTY)
b7          : 0 files   (EMPTY)
statistics  : 0 files   (EMPTY)
hypotheses  : directory MISSING
training    : 52 files (1 parquet) ← dry_run only
extensions  : 0 files   (EMPTY)
```

**Result:** 1 of 12 gate conditions met (B0 only). Campaign is a dry run. **FAIL.**

---

## 3. Fallback evaluation — `results/sp0/SP0_PROTOCOL_v1/FINAL_RUN_MANIFEST.json`

§2 permits falling back to "the most recent final version" whose manifest meets the gate. This earlier campaign also fails, and is additionally the **v1 protocol the instructions label as invalidated** (§2 exclusion: "resultados del protocolo v1 invalidado").

- Manifest statuses present: `"reused"`, `"blocked_before_confirmatory_seed_opening"`, `"blocked_missing_real_trainer"`
- `dry_run: false`, but confirmatory blocks never opened.
- On-disk: `b2=4`, `b3=5` files (partial screening/tuning), **`b4=b5=b6=b7=0` (all empty)**.

**Result:** Confirmatory blocks (B4–B7) absent; run self-declares `blocked_missing_real_trainer`. Excluded as invalidated protocol. **FAIL.**

---

## 4. Missing artifacts (blocking list)

Nothing in the confirmatory tier exists. To unblock SP0a, the following must be produced by a **real (non-dry-run) frozen confirmatory campaign** and reflected in `FINAL_RUN_MANIFEST.json`:

1. **B2** screening — 2400 rows → `results/sp0/<final>/b2/*.parquet`
2. **B3** selection/tuning — 1536 rows → `.../b3/*.parquet` (champions frozen; feeds figure/table method selection)
3. **B4** confirmatory main — 5760 rows → `.../b4/*.parquet`
4. **B5** communication sweep — 4000 rows → `.../b5/*.parquet`
5. **B6** stress/robustness — 960 rows → `.../b6/*.parquet`
6. **B7** generalization (N∈{24,48}) — 480 rows → `.../b7/*.parquet`
7. **Confirmatory statistics** → `.../statistics/*.parquet` (effect sizes, 95% CIs)
8. **Hypotheses + Holm correction** → `.../hypotheses/*.parquet` (H0-SP0-P1/P2/P5/G3/C2/R2 decisions with `p_adjusted`)
9. **Real data-driven training** — IPPO/MAPPO-GNN with the pre-registered step budget, 3 final seeds, `training_converged` resolved (or a documented negative result), `confirmatory_seeds_opened = true`, `artifact_scope != "dry_run_only"`
10. **Frozen manifest** with top-level `status = "completed"`, `protocol_frozen = true`, `dry_run = false`, and the six B-counts matching the gate.

---

## 5. What was intentionally NOT done

Per §2, §14 ("No insertar una cifra en el TFM si no tiene una fila de trazabilidad"), and §22 (claims rules), I did **not**:

- draft any of `6.1.1`–`6.1.4` with numeric claims;
- fabricate Table 6.x / Figure 6.x values, CIs, p-values, regret, success rates, message counts, CVaR, or generalization gaps;
- promote B0 or `smoke/` results (e.g. `smoke/hypotheses.parquet`) to confirmatory status;
- select a "best" MAPPO/IPPO seed or claim a data-driven winner (no seed converged; all are dry-run);
- create `TFM_MayorgaTaborda_v3_SP0a.docx` / `_preview.pdf` or the `manuscript/SP0a/` deliverable tree with placeholder content;
- modify the TFM (`docs/doc-05-final-report/…`), its indices, cross-references, equation numbering, or bibliography.

## 6. Additional environment note (non-blocking, but relevant)

The task's input paths (`/mnt/data/TFM_MayorgaTaborda_v2.docx`, `/mnt/data/Plantilla memoria TFM_ MROB (1).docx`, `/mnt/data/Instrucciones_TFM_MU Robotica F (2).pdf`) **do not exist in this environment**. The actual TFM in this repository is a **LaTeX** project at `docs/doc-05-final-report/` (built with XeLaTeX), not a `.docx`. The Word-specific deliverables (`_v3_SP0a.docx`, editable Word equations, Word auto-captions) in §3/§24 are therefore not directly producible here; the LaTeX report would be the real insertion target once confirmatory data exists. This mismatch should be resolved alongside re-running the campaign.

---

## 7. Next step to unblock

Run the real (non-dry-run) frozen SP0 confirmatory campaign so `FINAL_RUN_MANIFEST.json` reports `status=completed`, `protocol_frozen=true`, `dry_run=false`, B2=2400/B3=1536/B4=5760/B5=4000/B6=960/B7=480, converged (or documented) DD seeds, and completed statistics + Holm. Re-invoke SP0a drafting only after this report's gate table is all ✅.

**FINAL STATUS: BLOCKED.**
