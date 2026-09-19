# Referencias cruzadas del cuerpo activo

Criterio VIU: toda figura, tabla y ecuacion numerada debe citarse en el
texto por su numero.

| metrica | n |
|---|---:|
| ficheros activos | 89 |
| etiquetas definidas | 242 |
| etiquetas referenciadas | 150 |
| etiquetas huerfanas | 92 |
| referencias sin destino | 0 |

## Incumplimientos VIU: flotantes y ecuaciones sin citar

**19 elementos numerados no se citan en ninguna parte del texto.**

| tipo | etiqueta | fichero | titulo |
|---|---|---|---|
| figura | `fig:cargo-e2e-success` | `sections/v2/support/cargo-e2e-v2.tex` | Éxito extremo a extremo por método y régimen. Cada celda |
| figura | `fig:coppelia-narrow-trajectories` | `sections/v2/coppelia-compact.tex` | Trayectorias
  reproducidas en CoppeliaSim del mundo par |
| figura | `fig:megajuego-routes` | `sections/v2/megajuego-compact.tex` | Deformación
  cooperativa de las propuestas rectas inici |
| figura | `fig:megajuego-stopgo` | `sections/v2/megajuego-compact.tex` | Ejecución
  cooperativa frente a parada segura (\emph{st |
| figura | `fig:method-cargo-caging` | `sections/source-snapshot/mainmatter/04-methodology.tex` | Interfaces físicas. En Cargo, visto de lado, los AMR sos |
| figura | `fig:method-coppeliasim-warehouse` | `sections/source-snapshot/mainmatter/04-methodology.tex` | Montaje del almacén en CoppeliaSim. La vista oblicua mue |
| figura | `fig:method-unicycle-fleet` | `sections/source-snapshot/mainmatter/04-methodology.tex` | Modelo de la flota en vista cenital. Cada AMR tiene pose |
| figura | `fig:pre-results-provenance` | `sections/results-interface.tex` | Cadena de procedencia para cifras y afirmaciones empíric |
| figura | `fig:pre-sp3-execution-envelope` | `sections/sp3-execution-envelope.tex` | Cadena ejecutable entre la ruta discreta y la referencia |
| figura | `fig:sp1-compact-pipeline` | `sections/v2/sp1-compact.tex` | Composición de las tres
  etapas de SP1. Cada flecha ent |
| tabla | `tab:cargo-sp-mapping` | `sections/v2/support/cargo-e2e-v2.tex` | Correspondencia funcional entre el demostrador Cargo y l |
| tabla | `tab:conclusion-hypothesis-h6` | `sections/v2/conclusions-megajuego-addendum.tex` | Estado final de H6, en continuación de la Tabla~\ref{tab |
| tabla | `tab:method-review-protocol` | `sections/v2/appendix-review-full-detail.tex` | Protocolo comparado de las tres revisiones que sostienen |
| tabla | `tab:method_sp_contribution_validation` | `sections/source-snapshot/mainmatter/04-methodology.tex` | Aporte y evidencia empleada en SP1--SP3. |
| tabla | `tab:sp1-compact-e2-ablation` | `sections/v2/sp1-compact.tex` | Ablación pareada de las puntuaciones plana y marginal en |
| tabla | `tab:sp2-compact-cargo-results` | `sections/v2/sp2-compact.tex` | Demostrador Cargo híbrido: resultados agregados de los s |
| tabla | `tab:sp2-compact-e6-results` | `sections/v2/sp2-compact.tex` | Resultados agregados de E6-C sobre 480 mundos pareados p |
| tabla | `tab:sp3-compact-e7-results` | `sections/v2/sp3-compact.tex` | Resultados agregados de E7-C sobre $\SPSevenWorlds$ mund |
| tabla | `tab:sp3-results` | `sections/sp1-wrench-condensed.tex` | Contraste E3 sobre \SPThreeWorlds{ |

Cada uno admite una de tres salidas: citarlo en el texto, fundirlo con
otro elemento, o retirarlo. Un flotante que el argumento no necesita
ocupa presupuesto de paginas sin sostener nada.

## Resto de etiquetas huerfanas, por tipo

No incumplen la norma: un teorema o una seccion pueden leerse en su sitio
sin cita cruzada. Se listan porque una etiqueta que nadie usa suele
sobrar.

| tipo | n | ejemplos |
|---|---:|---|
| `alg` | 2 | `alg:cargo-hibrido`, `alg:cargo-hibrido-compact` |
| `app` | 26 | `app:megajuego-bezier-proof`, `app:megajuego-budget-proof`, `app:megajuego-caging-proof` |
| `prop` | 8 | `prop:pre-sp2-kinematic-equivalence`, `prop:pre-sp2-opposite-monotonicity`, `prop:pre-sp2-scalar-insufficiency` |
| `sec` | 12 | `sec:hypotheses`, `sec:introduction`, `sec:method-coppelia-narrow` |
| `subsec` | 12 | `subsec:architecture-contract`, `subsec:common-formulation`, `subsec:common-protocol` |
| `subsubsec` | 8 | `subsubsec:sp1-contacts`, `subsubsec:sp1-heterogeneity`, `subsubsec:sp2-cargo-e2e` |
| `thm` | 5 | `thm:sp2-compact-e4-pose`, `thm:sp2-compact-e6-exact-potential`, `thm:sp2-compact-e6-feasible-nash` |
