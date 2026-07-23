# Plan de ejecución — SP1 TFM Final Quota Game Benchmark V1

## Propósito y resultado observable

Implementar, ejecutar y auditar la campaña
`SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1` para responder cuándo una dinámica
poblacional con cuotas inferiores/superiores y recuperación atómica ofrece una
mejor solución física que una subasta distribuida o un juego hedónico, y qué
coste real introduce en tiempo, cómputo y comunicación.

El resultado observable son dos paquetes nuevos e inmutables:

- `results/sp1_validation/SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1_preview`;
- `results/sp1_validation/SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1`.

Cada paquete debe poder reconstruirse desde código, configuración, semillas y
commit, y debe distinguir `RAW`, `SEEDED` y `RECOVERED`. La campaña no
presupone un ganador y conservará censura, fallos, resultados negativos y
regímenes donde los baselines sean mejores.

## Contexto y archivos canónicos

- Contrato científico: `docs/00_TFM_CHARTER.md`.
- Requisitos académicos: `docs/01_VIU_REQUIREMENTS.md`.
- Matriz SP1--SP3: `docs/02_RESEARCH_MATRIX.md`.
- Protocolo: `docs/03_EXPERIMENT_PROTOCOL.md`.
- Claims: `docs/04_CLAIMS_EVIDENCE.md`.
- Notación: `docs/05_NOTATION.md`.
- Plantilla SP: `docs/07_SP_SECTION_TEMPLATE.md`.
- Infraestructura histórica incorporada sin modificar sus IDs:
  - V2: `conference_v2.py` y `rounding.py`;
  - V3: `dynamics_v3.py`;
  - benchmark simple: `drd_cbba_simple.py` y `drd_cbba_benchmark.py`.
- Configuración congelable:
  `experiments/configs/sp1_tfm_final_quota_game_benchmark_v1.yaml`.
- Rama: `codex/sp1-tfm-final-quota-game-v1`.
- Base lineal auditada: `0a8ecdf34d12fd0ecce686ce3c47d43231ce4a1f`.

La rama se ejecuta en un worktree separado porque el árbol de trabajo original
contenía cambios ajenos y miles de eliminaciones no relacionadas. No se
revierten, mezclan ni firman esos cambios.

## Alcance y no alcance

Incluye reclutamiento estático y por eventos, capacidad escalar indivisible,
compatibilidad, distancia, cuotas inferiores/superiores, intención continua,
compromiso entero, recuperación por cadenas, mercados locales en grafo
conectado, comunicación auditable, oráculos LP/MILP y un control polinomial de
slots unitarios.

No incluye docking, contacto, reparto de wrench, control de formación,
transporte sostenido, MPC/DMPC, MAPF, A*, tráfico ni hardware. Las posiciones
solo parametrizan el coste de reclutamiento. Los eventos de E7 modelan
disponibilidad y reasignación, no una planta física.

## Supuestos y preguntas resueltas

- La magnitud `q_i` es una capacidad escalar positiva e indivisible. No se
  interpreta como una fracción físicamente divisible.
- La convención canónica tiene precedencia sobre el prompt: la intención
  continua se denota `rho_ik` y la decisión física cerrada se almacena como una
  asignación entera/indicador `x_ik`. Los artefactos incluyen el mapeo
  `prompt_x -> rho` y `prompt_y -> x`.
- `idle` es una acción explícita, por lo que cada robot tiene exactamente una
  estrategia física.
- La distancia se mide en metros y se normaliza por el máximo finito del mundo
  solo dentro de payoffs/dinámicas. La evaluación física conserva metros.
- Una partición testigo, oculta a los métodos, garantiza factibilidad. La
  compatibilidad del testigo se conserva al construir escenarios restringidos.
- Los mercados QPG se alojan en el robot candidato más próximo a cada carga.
  Precios e intenciones viajan por caminos mínimos del grafo conectado. No se
  mantienen copias densas globales de todos los duales en todos los robots.
- Un paquete es una transmisión unidireccional real sobre una arista y evento.
  Los metadatos y escalares `float64`/`int64` se contabilizan en bytes.
- El cierre común no es completo para capacidad ponderada general. Se reporta
  su límite de longitud/nodos y la condición residual observada.
- Solo se calcula gap contra MILP si el solver certifica optimalidad. LP y dual
  son lower bounds, no asignaciones físicas.
- La activación de un gate una sola vez no es convergencia: se exige
  persistencia de 100 rondas para métodos continuos y estabilidad de una época
  para métodos atómicos.

## Decisión bibliográfica sobre GRAPE-S

La versión final verificada es Diehl y Adams (2026), *Autonomous Agents and
Multi-Agent Systems*, 40, artículo 29,
`https://doi.org/10.1007/s10458-026-09758-4`. El modelo publicado representa
cada robot y tarea mediante vectores de servicios discretos; cada requisito es
un conteo entero y un robot presta un único servicio a una única tarea.

Por ello:

- `Weighted-GRAPE` y `Weighted-Pair-GRAPE` son adaptaciones propias para la
  capacidad escalar continua y no heredan garantías de GRAPE-S;
- E10 reproduce por separado GRAPE-S y Pair-GRAPE-S en servicios discretos;
- ningún resultado E10 se mezcla con el benchmark escalar;
- la implementación documentará las desviaciones del simulador distribuido
  publicado y no afirmará una reproducción de sus resultados originales.

## Diseño matemático/técnico

### Problema físico

Para robot `i`, `x_ik` es binaria y existe una acción `idle`. La solución debe
cumplir exclusividad, compatibilidad y, para cada carga `k`,
`m_lower[k] <= sum_i q_i x_ik <= m_upper[k]`. El objetivo entero principal es
la distancia total en metros.

El potencial común de comportamiento usa distancia normalizada, déficit,
exceso superior y coste de cambio. La entropía aparece solo en optimizadores
continuos. Cada puja o mejora hedónica se deriva de una diferencia exacta del
potencial discreto.

### Oráculos

- MILP binario con timeout de 60 s y registro de incumbent, dual bound, MIP
  gap, optimalidad, timeout, inviabilidad y error.
- LP sin regularización como lower bound.
- referencia entrópica convexa con el mismo conjunto relajado.
- Hungarian/min-cost slots solo en E0 con `q_i=1` y sin cuota superior
  restrictiva.

### Métodos

- M1 `Capacity-CBBA`: adaptación con bundle unitario, múltiples ganadores,
  cuota superior y puja marginal del potencial.
- M2 `Weighted-GRAPE`: mejor respuesta atómica unilateral.
- M3 `Weighted-Pair-GRAPE`: M2 más intercambios de dos robots.
- M4 `DRD-simple-Replicator`: ablación histórica con consenso dinámico de
  capacidad, ampliada de forma explícita al término de exceso superior.
- M5 `DRD-simple-Logit`: mismo estado, estimador y potencial que M4; cambia
  solo el protocolo de revisión.
- M6 `QPG-Replicator-AR`: precios locales comunes por carga y revisión
  exponencial/replicadora.
- M7 `QPG-Logit-AR`: método principal con respuesta Logit amortiguada y
  certificado dual computable.
- M8 `Atomic-Quota-Logit`: estado puro, activación asíncrona,
  `tentative/committed`, precios locales y salida siempre entera.

Todos los métodos pasan por el mismo evaluador y por el mismo
`AugmentingRecovery` cuando necesitan cierre. No se ajusta recovery por método.

### Certificados

Para multiplicadores no negativos `lambda_minus`, `lambda_plus`, se calcula el
dual no regularizado:

`d0 = lambda_minus^T m_lower - lambda_plus^T m_upper
      + sum_i min(0, min_k(c_ik-q_i(lambda_minus[k]-lambda_plus[k])))`.

El certificado usa `UB=c^T x_atomic` y ese `LB` solo cuando la salida atómica
es factible. También se reportan dual entrópico, gap regularizado, sesgo máximo
`tau sum_i log(|A_i|)` y coste atómico observado. La validez numérica se audita
contra LP/MILP sin afirmar que la cota sea ajustada.

### Recuperación

El cierre común admite movimientos, swaps y cadenas hasta longitud 12,
50.000 nodos y 30 candidatos por carga. Respeta ambas cuotas,
compatibilidad y exclusividad, prioriza menor incremento de distancia y
registra recourse. E9 separa greedy, swap, cadenas y MILP repair.

## Plan experimental

Las semillas de calibración, preview, evaluación, análisis y redondeo son
disjuntas. Los mundos se emparejan por `world_id`.

- Calibración: ocho semillas exclusivas en `(20,4)`, `(50,10)`, `(100,20)`;
  selección lexicográfica por factibilidad recovered, certificado, distancia,
  exceso, tiempo y bytes.
- Preview: cinco semillas por `(20,4)`, `(50,10)`, `(100,20)`, heterogeneidad
  media, utilización 0,8, banda media y grado objetivo 8.
- E0: diez casos deterministas, incluido control Hungarian y cadenas.
- E1: `N={10,20,50}`, `K=max(2,ceil(N/5))`, 50 semillas.
- E2: `N={20,50,100,200,500}`, semillas `{30,30,30,20,10}`.
- E3: `N=100`, `K={2,5,10,20,40}`, 30 semillas.
- E4: dos tamaños, tres heterogeneidades, tres utilizaciones, tres bandas,
  15 semillas por celda.
- E5: tres tamaños, complete y grados objetivo 4/8/16, 20 semillas.
- E6: Replicator, Smith, BNN, Logit, proyección y mejor respuesta amortiguada
  bajo la arquitectura QPG; tres tamaños y 20 semillas.
- E7: tres tamaños, cinco eventos y 20 semillas; el evento se inyecta después
  de disponer de una solución inicial válida.
- E8: 30 estados continuos predeclarados, 100 redondeos independientes por
  estado y cota de Bernstein.
- E9: instancias con longitud mínima 1--12 y adversariales, comparando cuatro
  reparadores.
- E10: servicios discretos, separado, solo para GRAPE-S fiel.

Se reportan Wilson, McNemar exacto, bootstrap pareado, Wilcoxon,
rank-biserial, Holm, Kaplan--Meier/RMST, frentes de Pareto y regresiones
robustas exploratorias. Los censurados no se eliminan.

## Hitos

- [x] Hito 1 — worktree aislado y rama limpia; V2/V3/DRD preservados.
- [x] Hito 2 — fuentes canónicas y GRAPE-S final auditados.
- [ ] Hito 3 — protocolo, plan y literatura congelados en commit inicial.
- [ ] Hito 4 — núcleo matemático, métodos y pruebas unitarias aprobados.
- [ ] Hito 5 — runner reanudable, auditoría y artefactos aprobados en humo.
- [ ] Hito 6 — calibración completada y parámetros congelados.
- [ ] Hito 7 — preview completo con gates aprobados.
- [ ] Hito 8 — E0--E10 completos con conteos exactos.
- [ ] Hito 9 — estadística, figuras, informe y revisión visual completados.
- [ ] Hito 10 — trazabilidad, hashes, commit final y Git limpio.

## Validación

Comandos previstos:

```powershell
python -m pytest tests/test_sp1_tfm_final_quota_game.py -q
python -m viu_mrob_tfm.cli.run_sp1_tfm_final_quota_game --stage calibrate
python -m viu_mrob_tfm.cli.run_sp1_tfm_final_quota_game --stage preview
python -m viu_mrob_tfm.cli.run_sp1_tfm_final_quota_game --stage full --resume
python -m viu_mrob_tfm.cli.run_sp1_tfm_final_quota_game --stage audit
```

La aceptación exige invariantes, conteos exactos, mismas instancias/grafos,
ausencia de NaN/Inf, mensajes recomputables, certificados válidos, semillas
disjuntas, hashes y estado Git limpio.

## Riesgos y mitigaciones

- **Coste total alto:** checkpoints por mundo/método, seis workers y
  reanudación idempotente; la campaña no se reduce después del preview.
- **QPG no converge:** conservar censura y ejecutar recovery solo bajo la regla
  predeclarada; no convertir un cruce transitorio en convergencia.
- **MILP agota timeout:** registrar incumbent/bound/gap; omitir gap óptimo si no
  hay certificado.
- **Cadenas ponderadas incompletas:** conservar fallo, nodos y condición
  residual; E9 delimita el alcance.
- **Comparadores adaptados:** rotular Capacity-CBBA y Weighted-GRAPE como
  adaptaciones y separar GRAPE-S fiel.
- **Mensajería idealizada:** registrar payload lógico y rutas sobre aristas; no
  equipararlo con tráfico de middleware físico.
- **Resultados negativos:** actualizar `docs/04_CLAIMS_EVIDENCE.md` sin
  maquillar gates.

## Registro de decisiones

- 2026-07-23 — Se creó un worktree separado debido al estado masivamente sucio
  del árbol original; no se tocaron cambios ajenos.
- 2026-07-23 — Se avanzó linealmente hasta la rama auditada DRD/CBBA para
  reutilizar V2/V3 sin copiar ni sobrescribir campañas.
- 2026-07-23 — Se aplicó la notación canónica `rho` continua / decisión entera
  separada, documentando el mapeo con el prompt.
- 2026-07-23 — La publicación final de GRAPE-S confirmó requisitos discretos
  por servicio; se separó E10 del benchmark escalar.

## Progreso

Fuentes de verdad y publicación primaria revisadas. Rama limpia creada en
`C:\Users\walla\Documents\Github\VIU-MRBO-TFM-2026-sp1-quota`. Pendiente:
cerrar el commit inicial del protocolo e iniciar la implementación.
