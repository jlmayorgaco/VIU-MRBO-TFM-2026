# Auditoría submit-ready de SP0--SP3

**Fecha:** 2026-07-16

**Alcance:** microcapítulos SP0--SP3, anexos de prueba, tablas/figuras, trazabilidad, postprocesos y PDF.
**Dictamen:** los cuatro microcapítulos están listos para envío dentro del alcance y del nivel de evidencia que declaran. Este dictamen no eleva a demostradas la distribución completa, la planta física o la optimalidad del cierre entero.

## 1. Resoluciones de la revisión

| # | Issue | Resolución | Estado |
|---:|---|---|---|
| 1 | SP3 confundía el minimizador del QP regularizado con el residual de wrench. | Se definió `\boldsymbol\lambda_k^\star` como solución del QP y `\rho_k^{W\star}` como residual evaluado después en esa solución. | RESOLVED |
| 2 | El último estado de la cadena informacional no aparecía desde la introducción. | SP0 y SP1 declaran CLOSED; SP2 declara GUARDED escalar; SP3 declara GUARDED planar. Ninguno afirma EXECUTED. | RESOLVED |
| 3 | Las tablas compactas no explicitaban suficientemente rol y paradigma. | Se añadieron oráculo/baseline/propuesta/ablación y `model-based`/`data-driven`/contextual no ejecutado en los párrafos críticos. | RESOLVED |
| 4 | Algunos efectos negativos se redactaban como magnitudes positivas con IC negativos. | Se reportan como diferencias candidato menos referencia, conservando signo, IC y prueba. | RESOLVED |
| 5 | La tabla principal de resultados de SP1 no tenía una llamada textual. | Se añadió la referencia antes de la tabla. | RESOLVED |
| 6 | Los mecanismos propios adicionales de SP3 no estaban localizados visualmente. | Mercado residual, cierre pareado y guardia quedaron en una caja naranja con estado de evidencia y límites. | RESOLVED |
| 7 | Los generadores históricos completos de SP2 y SP3 no están en el árbol de trabajo actual. | La limitación permanece declarada: datos, manifiestos y postproceso son auditables; repetir la campaña exige restaurar el generador histórico. | DELIBERATE_LIMITATION |

## 2. Dictamen por subproblema

| SP | Resultado formal | Evidencia experimental | Control/acoplamiento | Dictamen |
|---|---|---|---|---|
| SP0 | Potencial exacto; Nash = asignaciones factibles; mejora finita; precio de estabilidad 1 y precio de anarquía sin cota uniforme; certificados auxiliares en anexo. | 200 instancias pareadas, 21 enumeraciones, Hungarian, subasta, greedy, mejor respuesta y 2-intercambio. | Servorregulación de déficit y duplicidad con feedback agregado exacto; sin planta. | SUBMIT-READY |
| SP1 | Potencial exacto y cuota realizable; degeneración del déficit bajo escasez; incentivo de cuórum delimitado. | 1440 mundos; QR cierra, pero Greedy-Q supera a Smith-QR y la ablación de exceso no es concluyente. | Regulación exacta solo para el juego finito realizable; Smith--QR no hereda esa prueba. | SUBMIT-READY |
| SP2 | El score marginal es gradiente de potencial para capacidad fija; el score plano no es integrable en general. | 1560 mundos; la corrección marginal mejora el scorer secuencial; primal--dual no supera a greedy. | Lazo candidato de déficit de capacidad; la campaña usa agregados globales y no integra la EDO. | SUBMIT-READY con evidencia arquitectónica parcial |
| SP3 | Potencial estrictamente cóncavo y equivalencia KKT/equilibrio variacional para la relajación continua. | 600 mundos y 7200 ejecuciones; guardia sin falsos positivos respecto del oráculo planar; consenso corto peor que agregado exacto. | Residual de wrench y precios de slot; docking cinemático formulado pero no ejecutado. | SUBMIT-READY para el modelo planar; Cargo completo y caging pendientes |

## 3. Bibliografía y trazabilidad

- Las 20 claves citadas en SP0--SP3 existen en `thesis/references.bib` y figuran como `VERIFICADA` en `references/LITERATURE_LEDGER.md`.
- Las afirmaciones soportadas, parciales, refutadas y pendientes coinciden con `docs/04_CLAIMS_EVIDENCE.md`.
- Los resultados negativos de SP1 y SP2 permanecen visibles; no se sustituyeron por claims favorables.
- Las pruebas completas están en los anexos B--E y los enunciados del cuerpo remiten a ellas.

## 4. Validación ejecutada

- Postproceso SP2: regeneración correcta de `SP2_EFFECTIVE_CAPACITY_EVIDENCE_v1`.
- Postproceso SP3: regeneración correcta de `SP3_WRENCH_EVIDENCE_v1`.
- Pruebas: **23 passed** en SP0--SP3.
- Compilación: LuaLaTeX/Biber completados; PDF A4 válido de **126 páginas**.
- Referencias/citas indefinidas: **0**.
- Overfull en SP0--SP3: **0**.
- Inspección visual: páginas 49--81 sin recortes, solapamientos ni tablas/cajas ilegibles.
- Inicios: SP0 p. 49, SP1 p. 57, SP2 p. 65 y SP3 p. 74.

## 5. Riesgos que no invalidan estos cuatro microcapítulos

1. SP2 y SP3 no pueden relanzar hoy la campaña completa desde el árbol de trabajo reducido sin restaurar su generador histórico; sí pueden regenerar el análisis desde los CSV auditados.
2. La arquitectura distribuida completa no queda acreditada: SP0--SP2 usan agregados globales en etapas críticas y SP3 muestra degradación con cuatro rondas de consenso.
3. El docking de SP3 es una formulación candidata, no una simulación de planta ni una prueba del cuerpo compuesto.
4. La memoria completa mantiene advertencias tipográficas fuera de SP0--SP3 y el cuerpo principal ocupa aproximadamente 90 páginas, por encima del objetivo VIU de 50--80; este riesgo editorial global requiere una poda separada.
