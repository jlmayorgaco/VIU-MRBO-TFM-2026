# Informe de refactorización de SP1.N4

Fecha: 2026-08-14  
Rama de trabajo: `VIU_TFM_V2`  
Fuente principal: `thesis/sp1_levels_23p/n4_v2.tex`

## Resultado

N4 conserva doce páginas dentro del PDF de 38 páginas, pero ya no se lee como
una lista de algoritmos. La sección sigue una pregunta única: qué racionalidad
distribuida permite resolver el reclutamiento heterogéneo de N2 bajo el contrato
informativo de N3, y qué se paga en información, coordinación, atomicidad y
calidad. F-I queda como la contribución implementada; F-II, F-III y F-IV se
presentan con objeto matemático propio y una frontera de evidencia explícita.

No se ejecutaron campañas nuevas ni se cambió ninguna cifra de E4--E6.

## Baseline congelado

La compilación previa a esta ronda produjo 38 páginas, 1.161.631 bytes y SHA-256
`55e646c5cabcaf9826c2815c7b8f398d724b835ba3ca7686d563d35881fd4acf`.
En `n4_v2.tex` había 10 figuras, 3 tablas, 13 entornos de ecuación, 28 etiquetas
y 6 llamadas de cita. El log no contenía cajas desbordadas en N4; sí conservaba
los avisos editoriales ya conocidos de `hyperref` en modo borrador.

El artefacto final mantiene 38 páginas. N4 contiene 13 figuras, 4 tablas,
15 entornos de ecuación y 33 etiquetas. Las nueve figuras conceptuales nuevas
son TikZ separado y los resultados cuantitativos continúan saliendo de los
artefactos procesados existentes. La compilación final ocupa 1.180.686 bytes
(`1180686`) y
tiene SHA-256
`3402fdd715eb64747734191c42af1b0066b602c25815e8cb3ef9c52418391644`.

## Cambio de estructura

Antes, F-I ocupaba casi todo el desarrollo; F-II era una nota continua; F-III y
F-IV compartían una página; el conflicto entre propuestas, DMIS y la transacción
aparecían como piezas operativas poco conectadas. E4--E6 llegaban antes de que
el lector pudiera distinguir orden estratégico, regla de revisión y arquitectura.

La versión nueva usa esta secuencia:

1. problema físico común y taxonomía F-I--F-IV;
2. F-I: criterio lexicográfico, estadísticos suficientes y potencial unilateral;
3. jerarquía `h`-local y reglas de revisión dentro de `h=1`;
4. barrera bilateral, orden de escape y refinamiento progresivo;
5. F-II: estado continuo, potencial suave, cuatro dinámicas y cierre pendiente;
6. F-III: restricción compartida, mecanismo primal--dual y objetivo vGNE;
7. F-IV: reclutamiento recurrente como problema dinámico futuro;
8. grafo de conflictos, selección maximal distribuida y commit versionado;
9. contrato informativo, resultados R1--R6 y programa Q1--Q9;
10. evidencia E4--E6, tabla maestra y frontera SP1--SP2.

## Contenido reducido o trasladado

- Se eliminaron repeticiones de cifras que ya aparecen en figuras y macros.
- El pseudocódigo de DMIS+TX se redujo al flujo auditable del evento; el detalle
  de implementación permanece en `src/viu_mrob_tfm/sp1_n4/geo_qpg.py`.
- Las demostraciones se dejaron en el nivel necesario para fijar hipótesis,
  conclusión y límite. Una prueba extensa futura debe ir al anexo.
- La tabla operativa de F-I separa método, orden, revisión y scheduler; no crea un
  ranking entre objetos matemáticos distintos.
- El detalle de adquisición para preguntas todavía abiertas queda en
  `N4_EXPERIMENT_PLAN.md`, no como resultado dentro de la memoria.

## Claims corregidos

- `exact potential game` se limita a desviaciones unilaterales dentro de una
  fase; para `h>1` se usa búsqueda finita coalicional `h`-local.
- estabilidad `h`-local no se identifica con Nash fuerte ni con óptimo global.
- terminación finita requiere mejora estricta y ausencia de omisión permanente;
  no implica encontrar el óptimo.
- Geo-ASR se denomina revisión atómica tipo Smith; no se confunde con la
  dinámica poblacional Smith.
- DMIS produce un conjunto independiente **maximal**, no necesariamente máximo.
- primal--dual es el mecanismo de búsqueda; vGNE es la noción de solución.
- registros, flooding, consenso y DAC son infraestructura informativa, no
  familias de juegos.
- el commit es atómico solo bajo el modelo nominal declarado; no acredita
  tolerancia a crash, pérdida, partición o fallos bizantinos.
- el ajuste log--log de E6 describe el intervalo `16 <= N <= 64`; no es una cota
  asintótica ni evidencia de coste fijo.

## Cadena formal R1--R6

| ID | Resultado | Alcance exacto |
|---|---|---|
| R1 | Suficiencia de agregados afectados | Evalúa una desviación con estado propio y cargas modificadas; la red aún debe transportar esos registros. |
| R2 | Potencial exacto unilateral | Identidad de diferencias dentro de una fase y para `h=1`. |
| R3 | Barrera unilateral y escape bilateral | Testigo condicionado de `h*=2`; no caracteriza todas las barreras. |
| R4 | Terminación del refinamiento | Espacio finito, mejora estricta y búsqueda justa; entrega un mínimo `h`-local. |
| R5 | Composición no conflictiva | Aditividad cuando las propuestas comparten fase y no comparten robots ni registros modificados. |
| R6 | Atomicidad nominal | Escritura todo-o-nada con entrega fiable, versiones comparables, bloqueos y proponente activo. |

## Figuras TikZ

Se crearon archivos independientes en `thesis/sp1_levels_23p/figures/n4/`:

- `n4_taxonomy.tex`;
- `n4_marginal_move.tex`;
- `n4_order_revision.tex`;
- `n4_barrier_refinement.tex`;
- `n4_population.tex`;
- `n4_primal_dual.tex`;
- `n4_same_world.tex`;
- `n4_conflict_graph.tex`;
- `n4_tx_flow.tex`.

Todos usan la tipografía del documento y se revisaron sobre el render completo,
no como capturas aisladas.

## Evidencia reutilizada

- E4: 1.200 mundos y 12.000 ejecuciones para orden, revisión y control
  arquitectónico CF--DMIS+TX.
- E5: 400 mundos pequeños para DPOP frente a MILP.
- E6: 60 mundos en cuatro tamaños para el escalado observado de BR y DMIS+TX.
- E71: contexto poblacional continuo; no entra en el ranking atómico.

Las cifras se insertan mediante `generated/metrics.tex` y las figuras de
`scripts/results/sp1_levels/n4_v2/`. No hay números escritos a mano para esta
ronda.

## Experimentos propuestos, no ejecutados

Quedan pendientes Q1 (distribución de `h*`), Q3 (FULL frente a AGG), Q7
(cierre poblacional común), Q8 (residuos primal--dual/KKT y cierre) y Q9 (canal
degradado). Q4 está respondida solo para red nominal: faltan rondas, identidad
final y fallos de canal. No se presentan resultados para estas adquisiciones.

La figura temporal de una ejecución también queda pendiente. El RAW agregado de
E4--E6 no conserva por evento `D(e)`, `J(e)`, orden aceptado, commits paralelos y
bytes acumulados. Dibujar esas curvas con los datos actuales sería inventarlas.
Antes de incorporarla debe instrumentarse el registro, congelar una semilla
representativa y regenerar la figura desde esa traza.

## TODO científico real

1. Ejecutar Q1 y explicar la mejora de C3 mediante la distribución de `h*`.
2. Ejecutar Q3 con igualdad exacta de propuestas, desempates y perfil final.
3. Definir e implementar un cierre común `R(x)=a` antes de comparar F-II/F-III.
4. Implementar F-III y comprobar residuos antes de afirmar convergencia o vGNE.
5. Someter DMIS+TX a pérdida, retardo, reordenamiento y caída del proponente.
6. Persistir trazas por evento para la figura temporal y la auditoría de rondas.
7. Trasladar pruebas largas al anexo si se amplía la memoria canónica.

La referencia de estilo indicada por el autor no se añadió a la bibliografía:
no se localizó una ficha primaria verificable durante esta ronda y no es
necesaria para sostener ninguna afirmación técnica de N4.
