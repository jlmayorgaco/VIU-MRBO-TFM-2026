# Submit Ready Gate

- Status: `PASS_WITH_WARNINGS`
- File: `docs/doc-05-final-report/main.tex`
- Word count: `19103`
- Blockers: `0`
- Warnings: `1`
- Strict mode: `False`

## Scope

This report is a local pre-submission gate. It checks VIU structure, template markers,
bibliography integrity, claim safety, human-writing heuristics, and local originality
signals. It cannot certify external plagiarism unless a similarity report is provided.

## Findings

| Severity | Category | Check | Message | Evidence | Recommendation |
|---|---|---|---|---|---|
| warning | originality | external-similarity-report | No external similarity report was provided. | Local checks cannot certify plagiarism against external corpora. | Run with SIMILARITY_REPORT=<path> or REQUIRE_SIMILARITY=1 for final lock. |
| info | page-budget | main-pages | The main document is within the configured page limit. | Main document: 72/80; appendices: 8/8; Introduction starts on PDF page 14, Appendix A on 86, and References on 79. |  |
| info | page-budget | appendix-pages | The appendices are within the configured page limit. | Main document: 72/80; appendices: 8/8; Introduction starts on PDF page 14, Appendix A on 86, and References on 79. |  |

## Included Files

- `docs/doc-05-final-report/main.tex`
- `docs/doc-05-final-report/sections/frontmatter/00-cover.tex`
- `docs/doc-05-final-report/sections/frontmatter/01-summary.tex`
- `docs/doc-05-final-report/sections/frontmatter/02-abstract.tex`
- `docs/doc-05-final-report/sections/frontmatter/03-contents.tex`
- `docs/doc-05-final-report/sections/frontmatter/04-nomenclature.tex`
- `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex`
- `docs/doc-05-final-report/sections/mainmatter/02-objectives.tex`
- `docs/doc-05-final-report/sections/mainmatter/03-hypothesis.tex`
- `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex`
- `docs/doc-05-final-report/figures/fig-metodologia-investigacion.tex`
- `docs/doc-05-final-report/sections/claim-artifact-registry.tex`
- `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex`
- `docs/doc-05-final-report/figures/fig-sota-transporte-cooperativo.tex`
- `docs/doc-05-final-report/figures/fig-equilibrio-nash-smith.tex`
- `docs/doc-05-final-report/figures/fig-campo-obstaculos.tex`
- `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex`
- `docs/doc-05-final-report/figures/fig-gap-literatura.tex`
- `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/index.tex`
- `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex`
- `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex`
- `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex`
- `docs/doc-05-final-report/figures/fig-sp4-docking-game-architecture.tex`
- `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex`
- `docs/doc-05-final-report/sections/anexo-b-reproducibilidad.tex`
- `docs/doc-05-final-report/sections/anexo-c-validacion.tex`
- `docs/doc-05-final-report/sections/a0-full-precision-contrasts.tex`
- `docs/doc-05-final-report/sections/anexo-d-declaracion-ia.tex`
- `docs/doc-05-final-report/sections/anexo-e-declaraciones.tex`
