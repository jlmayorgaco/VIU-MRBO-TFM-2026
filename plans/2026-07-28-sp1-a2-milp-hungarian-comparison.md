# SP1.A2 — campaña MILP heterogénea pareada con Hungarian

## Propósito y resultado observable

Convertir `scripts/sp1_a2_milp.py` desde una demostración aislada en una
campaña reproducible que cubra los mismos ejes experimentales de
`sp1_a1_hungarian.py`: escala, balance, asimetría de cuotas/geometría y fallos.
Cada mundo conservará posiciones, cargas, masas, IDs y semilla del caso
Hungarian, mientras el MILP recibirá capacidades heterogéneas individuales
`q_i`. El resultado incluirá CSV, figuras, manifest, reporte comparativo y
pruebas.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: SP1 debe tratar heterogeneidad sin atribuir
  factibilidad mecánica completa a una capacidad escalar.
- `docs/02_RESEARCH_MATRIX.md`: MILP es un oráculo central para coaliciones;
  Hungarian solo es válido para el caso homogéneo reducible a slots.
- `docs/03_EXPERIMENT_PROTOCOL.md`: instancias y semillas pareadas, gap/estado
  del solver, fallos conservados y oráculo global declarado.
- `docs/04_CLAIMS_EVIDENCE.md`: la comparación es de asignación estática y no
  valida red, control ni transporte.
- `docs/05_NOTATION.md`: `x_ik` es binaria; `c_i^{pay}` expresa capacidad útil
  en kg. El símbolo `q_i` ya está reservado para estado del robot en la
  notación canónica, por lo que el código usa `robot.capacity` y el reporte
  explicará la convención local solicitada por el autor.
- Scripts: `scripts/sp1_a1_hungarian.py` y `scripts/sp1_a2_milp.py`.

## Alcance y no alcance

Incluye capacidades escalares heterogéneas, cargas obligatorias, exclusividad
robot--carga, distancia, exceso, coste de uso, cinco generadores espaciales,
cinco modos de cuota, cinco niveles de heterogeneidad, fallos, tiempos, gap,
nodos, memoria estructural, CSV, plots y comparación pareada.

No incluye capacidad multidimensional, compatibilidad mecánica, roles/contactos,
wrench, comunicación distribuida, movimiento o transporte. Una diferencia
MILP--Hungarian bajo capacidades distintas no se interpretará como superioridad
algorítmica: combina método y modelo físico.

## Supuestos y preguntas resueltas

- Los mundos base se generan con la función canónica de Hungarian para
  conservar exactamente `N`, `K`, `M`, cuotas, masas y posiciones.
- Las capacidades heterogéneas se generan con un RNG separado y se normalizan
  para que su media sea `q_bar`; así la capacidad total nominal permanece
  pareada aunque cambie su distribución.
- La comparación algorítmica válida se verifica adicionalmente en la reducción
  homogénea: MILP con `q_i=q_bar` debe recuperar el mismo coste de distancia que
  Hungarian.
- `M=sum ceil(m_k/q_bar)` queda como demanda nominal de slots para indexar los
  mundos, pero el MILP no expande cargas en slots.
- La factibilidad MILP exige cubrir todas las cargas; una instancia sin solución
  se registra y no se convierte en solución parcial.

## Diseño matemático/técnico

Variables binarias `x_ik` asignan como máximo una carga por robot. Para toda
carga `k`, `sum_i capacity_i x_ik >= mass_k`. Una variable continua `e_k`
registra exceso. El objetivo combina distancia, exceso y número de robots con
un desempate positivo. El modelo se ensamblará de forma dispersa para evitar la
explosión de memoria del diseño denso actual.

Cada fila de campaña contendrá métricas MILP y Hungarian. Las métricas comunes
se limitarán a magnitudes semánticamente comparables: factibilidad, cobertura
nominal, distancia total, P95 normalizado, utilización, tiempo y memoria. Se
mantendrán nombres específicos para distancia por robot asignado y por slot
nominal; no se llamará “coste por slot asignado” al cociente MILP.

## Plan experimental

Estudios:

1. `scaling`: mismos `M`, `delta` y semillas del perfil Hungarian.
2. `balance`: barrido denso de `delta`.
3. `asymmetry`: cinco modos de cuota por cinco geometrías.
4. `failures`: mismos tratamientos de fallo sobre IDs pareados.
5. `capacity`: barrido homogéneo/low/moderate/high/extreme para aislar `q_i`.

El smoke usa dos semillas y tamaños 10/20. Los perfiles quick/full conservan la
rejilla Hungarian; el estado/gap/timeout del MILP se registra por ejecución.

## Hitos

- [x] Hito 1 — modelo disperso y reducción homogénea verificada.
- [x] Hito 2 — mundos pareados y capacidades reproducibles con media `q_bar`.
- [x] Hito 3 — campañas, métricas, CSV y plots.
- [x] Hito 4 — comparación, manifest y reporte.
- [x] Hito 5 — tests, smoke/run y auditoría.

## Validación

```text
python -m py_compile scripts/sp1_a2_milp.py
python -m pytest tests/test_sp1_a2_milp.py
python scripts/sp1_a2_milp.py --mode montecarlo --profile smoke --output-dir scripts/results/sp1_a2_milp_smoke
python scripts/sp1_a2_milp.py --mode montecarlo --profile quick --output-dir scripts/results/sp1_a2_milp
```

Criterios: reducción homogénea igual a Hungarian; media de capacidades
`q_bar`; IDs/masas/posiciones pareados; exclusividad; cobertura de todas las
cargas cuando `milp_feasible=True`; CSV completos; cinco geometrías; fallos
registrados; hashes válidos; ninguna modificación de los CSV Hungarian.

## Riesgos y mitigaciones

- Escalabilidad combinatoria: matriz dispersa, timeout explícito y registro de
  estado/gap; no llamar óptima a una solución sin certificado.
- Comparación injusta: separar reducción homogénea de efecto de heterogeneidad.
- Capacidad escalar mal interpretada: declarar que es carga útil nominal, no
  soporte, fuerza ni wrench.
- Fallos con instancia base infactible: conservar la fila con reason code.
- Árbol de trabajo sucio: modificar solo script, tests, plan y nuevos
  artefactos MILP.

## Registro de decisiones

- 2026-07-28 — El nombre de archivo vigente es `sp1_a2_milp.py`; se conserva
  por trazabilidad aunque el usuario lo haya referido como `sp1_milp.py`.
- 2026-07-28 — Se compararán tres conceptos: Hungarian homogéneo, equivalencia
  MILP homogénea en tests y MILP heterogéneo en campaña.
- 2026-07-28 — La capacidad total se mantiene constante en expectativa y de
  forma numérica exacta mediante normalización por mundo.
- 2026-07-29 — Corrección de auditoría: el lanzador del perfil `quick` superó
  1.804 s y devolvió timeout, pero el proceso alcanzó a publicar un paquete
  completo de 3.420 filas, manifiesto y 18 plots. La inferencia inicial de que
  no existían resultados fue incorrecta. Los hashes de esa fuente histórica
  se verificaron antes de reutilizarla.

## Progreso

La primera fase quedó cerrada con ensamblaje disperso, mundos pareados y cinco
estudios. El perfil `smoke` produjo 138 filas y la reducción homogénea alcanzó
diferencia máxima de distancia de 0 m. Una auditoría posterior confirmó además
que el perfil `quick` histórico publicó 3.420 filas completas. La salida
combinada se conserva sin cambios; su separación y revisión editorial se
documentan en
`plans/2026-07-29-sp1-a2-separated-results-scientific-plots.md`.
