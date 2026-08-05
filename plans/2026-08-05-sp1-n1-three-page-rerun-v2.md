# SP1.N1 v2: campaña confirmatoria y síntesis en seis páginas

## Propósito y resultado observable

Regenerar la evidencia de SP1.N1 con semillas nuevas y sintetizarla en seis
páginas consecutivas: modelo, mapa de campaña y una página para cada experimento
E1--E4. Cada resultado debe cerrar con una decisión verificable que delimite el
método y motive, cuando corresponda, el paso a SP1.N2. El PDF final debe compilar
en la rama `VIU_TFM_V2`, sin crear ramas adicionales, y todas las cifras
cuantitativas deben proceder de artefactos versionados.

## Contexto y archivos canónicos

- Alcance y rigor: `docs/00_TFM_CHARTER.md`, `docs/02_RESEARCH_MATRIX.md`,
  `docs/03_EXPERIMENT_PROTOCOL.md` y `docs/04_CLAIMS_EVIDENCE.md`.
- Notación y estructura: `docs/05_NOTATION.md` y
  `docs/07_SP_SECTION_TEMPLATE.md`.
- Implementación: `scripts/sp1_a1_hungarian.py` y `scripts/sp1_n1.py`.
- Configuración v2: `experiments/configs/sp1_n1_confirmatory_v2.yaml`.
- Resultados v2: `scripts/results/sp1_levels/n1_v2/`.
- Documento: `thesis/sp1_levels_23p/main.tex`.

## Alcance y no alcance

Incluye asignación central homogénea mediante reducción a slots, comparación
pareada con greedy, escalabilidad empírica, recálculo central postfallo y una
auditoría externa con capacidades heterogéneas. No incluye transporte físico,
control, comunicación distribuida, recuperación durante el movimiento ni una
afirmación de complejidad asintótica inferida de regresiones.

## Supuestos y preguntas resueltas

- Los robots de N1 comparten capacidad escalar
  $c_i^{\mathrm{pay}}=\bar c^{\mathrm{pay}}$.
- Las cargas pueden exigir coaliciones distintas mediante
  $n_k=\lceil m_k/\bar c^{\mathrm{pay}}\rceil$ slots intercambiables.
- El término “húngaro” nombra el baseline; la implementación usa
  `scipy.optimize.linear_sum_assignment` (Jonker--Volgenant modificado).
- Se preserva la campaña v1 y se escribe una campaña v2 separada.
- Las seis páginas de N1 separan modelo, diseño y E1--E4; N2 comienza
  inmediatamente después.

## Diseño matemático/técnico

El LSAP minimiza $\sum_{i,h}d_{ih}x_{ih}$ con una asignación por slot y como
máximo un slot por robot. En el dominio homogéneo, la solución es global para
el problema codificado. La salida acredita asignación estratégica cerrada,
pero no factibilidad mecánica ni ejecución física.

Hipótesis y auditorías preespecificadas:

1. **H-N1.Q (calidad):** por escenario, la mediana del ahorro pareado frente
   a greedy supera 5 %. Wilcoxon unilateral, IC bootstrap del 95 % y Holm para
   la familia de cinco escenarios.
2. **H-N1.I (invariantes):** toda salida del dominio homogéneo es completa,
   factible y sin violaciones de cardinalidad. Auditoría determinista.
3. **H-N1.R (recursos):** la pendiente temporal balanceada es positiva en el
   rango medido y la memoria cumple exactamente $8NM$ bytes. IC bootstrap del
   95 % para la pendiente; conclusión solo descriptiva.
4. **H-N1.F (fallo estático):** la factibilidad tras retirar robots coincide
   con $N_{\mathrm{activo}}\geq M$. Auditoría sobre la malla de reserva y
   fallos.
5. **H-N1.X (validez externa):** introducir capacidad individual aumenta los
   falsos factibles respecto del mundo homogéneo equivalente. McNemar exacto
   pareado y Holm; MILP/HiGHS se usa únicamente como auditor certificable.

## Plan experimental

- Calidad: cinco escenarios, tres tamaños, tres perfiles de demanda y 100
  semillas por celda; greedy y LSAP reciben el mismo mundo.
- Escalabilidad: siete tamaños hasta $N=2048$, tres relaciones $M/N$ y 30
  semillas por celda.
- Fallo: tres tamaños, cuatro reservas, cinco fracciones retiradas y 100
  semillas por celda.
- Validez externa: cinco escenarios, dos tamaños, cinco niveles de
  heterogeneidad y 30 semillas por celda.
- Unidad independiente: mundo--semilla. Fallos y métodos quedan anidados
  dentro del mundo. Los fallos y timeouts permanecen visibles.

## Hitos

- [x] Hito 1 — configuración v2 congelada y experimento de humo válido.
- [x] Hito 2 — campaña completa v2 con RAW, procesados, figuras y manifiesto.
- [x] Hito 3 — seis páginas N1 compiladas con cifras regeneradas.
- [x] Hito 4 — PDF renderizado, inspeccionado y pruebas pertinentes aprobadas.

## Validación

- `python scripts/sp1_n1.py --config experiments/configs/sp1_n1_confirmatory_v2.yaml --output-dir scripts/results/sp1_levels/n1_v2_smoke --smoke`
- `python scripts/sp1_n1.py --config experiments/configs/sp1_n1_confirmatory_v2.yaml --output-dir scripts/results/sp1_levels/n1_v2`
- `python scripts/build_sp1_levels_pdf.py`
- `pytest tests/test_sp1_levels.py tests/test_sp1_a1_hungarian.py`
- Comprobación de figuras TikZ protegidas y revisión visual de todas las
  páginas renderizadas, con atención especial a las páginas 5--8.

## Riesgos y mitigaciones

- **Variabilidad temporal:** medir distribución y declarar hardware/rango;
  no interpretar la regresión como ley asintótica.
- **Comparación injusta:** greedy comparte mundo y matriz; MILP no se presenta
  como competidor arquitectónico de N1.
- **Falso certificado por slots:** auditar capacidad real fuera del dominio y
  no imputar optimalidad si HiGHS no la certifica.
- **Contaminación del árbol de trabajo:** editar y validar únicamente las rutas
  de SP1.N1; no incorporar cambios ajenos ya presentes.

## Registro de decisiones

- 2026-08-05 — Se mantiene `VIU_TFM_V2` y no se crea ninguna rama.
- 2026-08-05 — La campaña v2 usa una semilla base nueva y un directorio nuevo.
- 2026-08-05 — La primera síntesis ocupó tres páginas.
- 2026-08-05 — La revisión editorial la amplía a cuatro páginas: modelo, diseño
  experimental, beneficio espacial y envolvente/transición. No se reabre la
  campaña ni se alteran resultados.
- 2026-08-05 — A petición del autor, E2, E3 y E4 dejan de compartir una
  envolvente: cada experimento recibe una página propia. N1 pasa a seis páginas
  y N2 comienza en la página 11, sin reabrir la campaña.
- 2026-08-05 — E1--E4 separan datos, interpretación y consecuencia editorial
  mediante los bloques `Resultado`, `Análisis y conclusión` y `Decisión`. No se
  modifican datos, contrastes ni figuras.

## Progreso

Campaña v2 completada con 12.630 filas RAW y 6.630 mundos independientes. El
ahorro mediano agregado fue 6,53 % (IC bootstrap del 95 %: 6,12--6,90 %), con
3/5 escenarios sobre el gate. La pendiente temporal balanceada observada fue
2,27 (IC del 95 %: 2,24--2,31), sin interpretar el ajuste como ley asintótica.
Las 6.000 intervenciones postfallo coincidieron con la condición cardinal. La
tasa de falsos factibles creció 0--38,0--72,0--92,3--97,7 % y HiGHS certificó
el 99,67 % de las auditorías. La revisión editorial separa E2, E3 y E4 en las
páginas 8--10; el PDF final contiene 28 páginas y sitúa N2 desde la página 11.
Pasaron 20 pruebas, Ruff y el comprobador de las cinco figuras TikZ protegidas;
las 28 páginas fueron renderizadas y las páginas 5--11 y 28 se inspeccionaron
visualmente.
