# Revision tracking — Stage 4

## Paper Information

| Field | Value |
|---|---|
| Paper Title | Arquitectura escalonada con componentes basados en juegos para coaliciones multi-AMR: formación, ejecución simulada y cierres auditados |
| Revision Round | 1 |
| Date | 2026-07-14 |
| Previous Decision | Minor Revision |
| Target | Trabajo Fin de Máster, VIU |
| Canonical source | `docs/doc-05-final-report/` |

## Revision Tracking Table

| # | Issue | Type | Resolution | Location / evidence | Status | Reason if limited |
|---|---|---|---|---|---|---|
| R1 | Reposition contribution, causality and locality. | P1 | Title and macro-claims now describe an escalated architecture with game-based components; A0 is explicitly not a formal game; package effects and global closure are separated. | `main.tex`; Summary/Abstract; Methodology Tables `presupuesto-centralizacion`, `mecanismo-por-experimento`; Theory `Posicionamiento`; Results/Conclusions. | RESOLVED | — |
| R2 | Close O5/MARL traceability. | P1 | Added architecture, observation, CTDE critic, budget, seeds, checkpoint hashes, controls and audit outcome. O5 is partial and no learned superiority is claimed. | Methodology Table `protocolo-marl`; SP0 `training/champion.yaml`; `SP0_AUDIT_REPORT.md`; Conclusions O5. | RESOLVED | — |
| R3 | Validate or replace adaptive 40–60–100 rule. | P1 | Replaced by a fresh fixed-$n$ protocol: 100 worlds per family, 20 frozen contrasts, fresh seeds, no optional stopping. | Fixed-n config/hypotheses; closed 2,400-run manifest; Methodology; Integrated Results. | RESOLVED | — |
| R4 | Align estimand, test and interval. | P1 | Published a 25-row machine-readable registry; A0 uses paired risk difference/McNemar/bootstrap/Holm; SP4 uses a block-level sign sensitivity and treats 108 instance intervals as descriptive. | `docs/generated/contrast_estimand_registry.*`; A0 contrast table; SP4 block table/artifacts. | RESOLVED | — |
| R5 | Bound parametric sensitivity claims. | P1 | Added parameter/domain, mechanism and reversal-risk table; robustness is explicitly limited to sampled families. | Integrated Results Table `parametros-integrados`; Conclusions `Limitaciones`. | RESOLVED | — |
| R6 | Separate Python, Coppelia, replay, HIL and hardware claims. | P1 | Added modality matrix; Coppelia is kinematic replay, HIL/hardware not realized, and zero collision is not functional safety. | Methodology Tables `identidad-evidencia` and `modalidades-validacion`; Conclusions. | RESOLVED | — |
| R7 | Publish a unique claim–artifact registry. | P1 | Added 10-row registry with config, seed registry, command, manifest, evidence, hashes, status and explicit `NO_DISPONIBLE`. | `docs/generated/claim_artifact_registry.*`; compiled Table `claim-artifact-registry`; `docs/CANONICAL_RESULTS.md`. | RESOLVED | — |
| R8 | Run bounded confirmatory parameter sensitivity or justify. | P2 | Did not add a post-hoc sweep. Replaced the invalid adaptive inference with a fresh fixed-$n$ campaign and preserved the parameter boundary as an explicit limitation. | Integrated Results after Table `parametros-integrados`; Conclusions `Limitaciones`. | DELIBERATE_LIMITATION | A defensible multidimensional sweep requires a separate preregistered design, fresh seeds and ranges chosen before seeing outcomes. |
| R9 | Build or specify dynamic/contact/deployment bridge. | P2 | Added G1 dynamic engine → G2 HIL → G3 AMR pilot with entry/exit criteria, hazards, E-stop/manual recovery and responsible stakeholders. It is labeled future work. | Conclusions Table `gates-validacion-futura`; Methodology modality matrix. | RESOLVED | No new physical evidence is implied. |
| R10 | Improve SP3 derivation, figures, references and editing. | P3 | Added compiled KKT/v-GNE statement; qualified three conceptual figures; added foundational ISS citation; expanded nomenclature; corrected the stated typo and harmonized claims. | Modular Evidence SP3; Theory ISS; three figure sources; Nomenclature; bibliography. | RESOLVED | — |

## Summary Statistics

| Metric | Count |
|---|---:|
| Total items | 10 |
| Resolved | 9 |
| Deliberate limitation | 1 |
| Unresolvable | 0 |
| Reviewer disagree | 0 |

## Completeness checklist

- [x] Every R1--R10 item has a response and stable ID.
- [x] Every resolved item specifies a section or artifact.
- [x] R8 is justified and preserved in Limitations.
- [x] R9 is explicitly future work and includes hazards.
- [x] New reference metadata and citation context are audited.
- [x] Final PDF/build/test hashes are inserted in `stage4_manifest.json` after verification.
