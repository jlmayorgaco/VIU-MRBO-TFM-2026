# SP1.A2 — auditoría de la aparente saturación temporal

## Propósito y resultado observable

Determinar si la meseta de tiempo observada para el MILP heterogéneo representa
una saturación computacional real o censura por el límite de tiempo del solver.
El resultado será una campaña reanudable con más valores de `N`, dos leyes de
escalado, sensibilidad al timeout, CSV, figuras editoriales, reporte y
manifiesto reproducible dentro de
`scripts/results/sp1_a2_milp_revised/milp_results/saturation_audit/`.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: no afirmar escalabilidad sin definición y evidencia.
- `docs/02_RESEARCH_MATRIX.md`: coste y escalabilidad son ejes transversales.
- `docs/03_EXPERIMENT_PROTOCOL.md`: registrar timeouts, no convergencias,
  estados y resultados negativos.
- `docs/04_CLAIMS_EVIDENCE.md`: SP1.A2 es evidencia piloto y el solver tiene
  timeout explícito.
- `docs/05_NOTATION.md`: capacidad útil `c_i^{pay}`; `q_i` queda reservado para
  estado.
- `scripts/sp1_a2_milp.py` y `tests/test_sp1_a2_milp.py`.
- Campaña quick existente: 1.560 filas de escala, 97 valores únicos de `N`,
  máximo `N=373`, timeout de 5 s.

## Alcance y no alcance

Incluye escalado con demanda fija, crecimiento conjunto robot--demanda,
sensibilidad a timeouts de 2/5/20 s, censura, optimalidad, factibilidad, gap,
tiempo por fases, memoria, variables binarias y regresiones únicamente sobre
ejecuciones certificadas.

No incluye afirmar complejidad asintótica a partir de una campaña finita,
extrapolar a `N` infinito ni tratar una solución factible sin certificado como
óptima.

## Supuestos y preguntas resueltas

- La meseta previa coincide con el timeout: en `N=318` y `N=373`, todas las
  ejecuciones observadas están próximas a 5 s y ninguna certifica optimalidad.
- “Saturación” exige tiempo plano sin censura y con tasa de certificación
  estable; una meseta al nivel del timeout no cumple esa definición.
- El modelo explícito contiene `N*K` costes/binarias. Su construcción tiene
  cota inferior `Omega(N*K)`; aun con solver plano, el coste total no puede ser
  constante cuando `N` crece.
- Las capacidades permanecen heterogéneas moderadas y se normalizan a media
  `q_bar`.

## Diseño matemático/técnico

### Brazo A — robots crecientes, demanda fija

Se fija `M=120` y se evalúa
`N={120,160,220,300,400,550,750,1000,1400,1900,2600,3500,4800}`.
Así `K` permanece aproximadamente fijo y `N*K` crece linealmente.

### Brazo B — crecimiento conjunto

Se fija `delta=0,20`, por lo que `N≈1,5M`, con
`M={40,60,90,130,190,280,420,620,900,1200}`. En este brazo `K` y `N`
crecen juntos y `N*K` es aproximadamente cuadrático.

### Brazo C — sonda de timeout

Para demanda fija se evalúan `N={400,800,1600,3200}` con timeouts
`{2,5,20}` s. Si la meseta sigue el timeout y la optimalidad cambia, se
clasifica como censura.

Cada celda usa tres semillas. Una fila se escribe inmediatamente y la clave
`(brazo,N,M,timeout,replica)` permite reanudar sin repetir.

## Plan experimental

- Perfil dedicado `saturation`.
- 13×3 + 10×3 + 4×3×3 = 105 ejecuciones máximas.
- Timeout principal: 5 s.
- Métricas: tiempo solver/modelo/matriz/total, optimalidad, factibilidad,
  censura, status, gap, nodos, `N*K`, memoria explícita y capacidad.
- Criterio de censura: status de límite de tiempo o tiempo del solver ≥90 % del
  límite sin certificado.
- Las regresiones de escalado usan solo medianas de ejecuciones óptimas y se
  omiten si hay menos de tres tamaños válidos o `R²<0,50`.

## Hitos

- [x] Hito 1 — runner reanudable y métricas de censura.
- [x] Hito 2 — plots que separan timeout, optimalidad y coste por fases.
- [x] Hito 3 — pruebas de configuración, reanudación y clasificación.
- [x] Hito 4 — campaña de 105 ejecuciones completada o límite documentado.
- [x] Hito 5 — auditoría visual, hashes y trazabilidad.

## Validación

```text
python -m py_compile scripts/sp1_a2_milp.py
python -m pytest tests/test_sp1_a2_milp.py -q
python scripts/sp1_a2_milp.py --mode saturation \
  --output-dir scripts/results/sp1_a2_milp_revised \
  --no-show
```

Criterios: CSV incremental sin claves duplicadas; los 13+10+12 escenarios
aparecen; timeouts identificados; ninguna regresión usa filas censuradas;
PNG 450 dpi y PDF; manifiesto válido; la conclusión distingue solver y coste
total.

## Riesgos y mitigaciones

- Duración: checkpoint tras cada ejecución y reanudación.
- Memoria en crecimiento conjunto: matriz dispersa, orden de tamaños ascendente
  y registro del último caso completado.
- Meseta engañosa: timeout visible como línea y censura como forma distinta.
- Pocas semillas: clasificar como auditoría piloto, no confirmatoria.
- Coste de wall clock externo: el runner no confunde el timeout del solver con
  tiempo de ensamblaje.

## Registro de decisiones

- 2026-07-29 — Se rechaza usar la meseta quick como evidencia de saturación
  porque coincide con 5 s y la optimalidad cae a cero.
- 2026-07-29 — Se amplía `N` hasta 4.800 con demanda fija y hasta 1.800 en
  crecimiento conjunto.
- 2026-07-29 — El criterio visual dominante será tasa de censura/optimalidad,
  no solo la línea de tiempo.
- 2026-07-29 — No se ajusta una ley temporal sobre la cola porque el 81,9 %
  de las ejecuciones está censurado. Los exponentes 1,000 y 2,004 se refieren
  al tamaño explícito `N*K`, no al tiempo del solver.
- 2026-07-29 — El tiempo de llamada se registra por separado del timeout
  nominal: en la instancia conjunta máxima la mediana fue 76,635 s con límite
  de 5 s.

## Progreso

Completado el perfil reanudable `saturation` con 105/105 casos y 105 claves
únicas: 39 ejecuciones de demanda fija, 30 de crecimiento conjunto y 36 de
sensibilidad al timeout. Se registraron 64 timeouts con incumbent, 22 sin
incumbent y 19 óptimos certificados; 86/105 ejecuciones quedaron censuradas.

El máximo de demanda fija fue `N=4.800`, `K=40` y 192.000 binarias, con
mediana de 16,599 s y 0 % de optimalidad. El máximo de crecimiento conjunto
fue `N=1.800`, `K=400` y 720.000 binarias, con mediana de 76,635 s, 0 %
de incumbent y 0 % de optimalidad. La razón máxima entre tiempo observado y
timeout nominal fue 15,40.

La sonda controlada demuestra sensibilidad al presupuesto: con `N=800`, la
optimalidad pasa de 0/3 a 3/3 al ampliar de 5 a 20 s; con `N=1.600`, de 0/3 a
1/3; con `N=3.200`, el timeout de 20 s recupera incumbent en 3/3 casos, aunque
sin certificado. Por tanto, la aparente meseta de 5 s era censura.

Se generaron cuatro figuras PNG de 450 dpi y cuatro PDF vectoriales, se
inspeccionaron visualmente y se corrigió la separación entre títulos generales
y títulos de panel. El manifiesto contiene 13 artefactos; todos sus SHA-256
fueron recalculados y validados. El runner encontró inicialmente una
incompatibilidad de columnas al unir resúmenes con y sin timeout; se corrigió
sin repetir los MILP gracias al checkpoint.

Validación final: `python -m py_compile scripts/sp1_a2_milp.py` y
`python -m pytest tests/test_sp1_a2_milp.py -q`, con 12 pruebas aprobadas en
52,41 s. La prueba añadida reproduce la combinación de resúmenes con y sin
sonda de timeout y valida que el esquema CSV sea uniforme. Se actualizó
`docs/04_CLAIMS_EVIDENCE.md`. La evidencia permanece clasificada como piloto:
tres semillas por celda, dependiente de hardware/SciPy/HiGHS y sin inferencia
asintótica.
