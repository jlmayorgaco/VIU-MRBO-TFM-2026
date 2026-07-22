# ExecPlan — SP1 Conference Validation V2 (remediación dirigida)

## Propósito

La campaña `SP1_CONFERENCE_VALIDATION_v2` corrige únicamente los fallos
diagnosticados en E1, E4, E5 y E6 de `SP1_CONFERENCE_VALIDATION_v1`. No repite
E0, E2 ni E3 y conserva V1 como línea base auditable. La contribución sometida a
validación es una asignación distribuida por dinámica replicadora entrópica con
preacondicionamiento por instancia y recuperación entera por caminos de aumento.

## Fuentes de verdad aplicadas

- `docs/00_TFM_CHARTER.md`
- `docs/01_VIU_REQUIREMENTS.md`
- `docs/02_RESEARCH_MATRIX.md`
- `docs/03_EXPERIMENT_PROTOCOL.md`
- `docs/04_CLAIMS_EVIDENCE.md`
- `docs/05_NOTATION.md`
- `docs/07_SP_SECTION_TEMPLATE.md`
- crítica externa adjunta del 22 de julio de 2026

## Alcance congelado antes de la ejecución completa

### E1 — Convergencia y comparabilidad

1. Reutilizar exactamente las instancias y semillas de E1-V1.
2. Sustituir el paso fijo por
   `alpha_I = clip(eta / Lhat_I, alpha_min, alpha_max)`, donde `Lhat_I` es un
   estimador numérico adimensional de escala del operador normalizado. No se
   presenta `Lhat_I` como constante de Lipschitz demostrada.
3. Separar dos fases y dos afirmaciones:
   - convergencia operacional: tolerancias relativas `1e-3`;
   - refinamiento para comparación: factibilidad normalizada `<= 1e-6` y
     residuos refinados declarados en la configuración.
4. Registrar paso, estimador, iteraciones de ambas fases, razón de parada,
   censura y residuos finales. Las ejecuciones que alcanzan el máximo se
   conservan como censuradas, no se descartan.

### E4 — Recuperación entera

1. Reutilizar exactamente las instancias y semillas de E4-V1.
2. Iniciar desde el argmax fraccional.
3. Reparar déficits mediante búsqueda de caminos/cadenas de reasignación que
   permiten déficits transitorios dentro del camino; aplicar después poda y
   cambios locales.
4. Registrar factibilidad por cada par `(N,K)`, longitud máxima de camino,
   nodos explorados, número de aumentos, déficit residual, sobreasignación,
   razón de fallo y gap frente al oráculo MILP.

### E5 — Escalabilidad

1. Reutilizar tamaños, semillas y presupuestos de E5-V1.
2. Usar la dinámica preacondicionada de E1.
3. Ejecutar recuperación entera únicamente si la solución fraccional alcanzó
   convergencia operacional. En otro caso registrar `skipped_nonconverged`.
4. Reportar tiempo, memoria, mensajes totales, bytes estimados y censura. La
   llegada a `N=500` no equivale por sí sola a éxito algorítmico.

### E6 — Ejecución cenital con obstáculos

1. Construir obstáculos condicionados a intersecar al menos una trayectoria
   directa asignada sin cubrir poses iniciales ni destinos.
2. Verificar geométricamente la intersección directa y que A* produce al menos
   un desvío real por escenario warehouse.
3. Guardar geometría, rutas, comprobaciones y energía de ruta en datos crudos;
   los MP4 se renderizan exclusivamente desde esos datos.

## Umbrales predeclarados de V2

- E1: convergencia operacional global `>= 0.95`.
- E1: comparabilidad refinada global `>= 0.90` entre ejecuciones elegibles.
- E4: factibilidad global de la recuperación por caminos `>= 0.95` y desglose
  explícito para todos los `(N,K)`.
- E5: cero ejecuciones de recuperación tras una dinámica no convergida.
- E5: resultados y estado de censura presentes hasta `N=500`.
- E6: al menos un obstáculo válido en cada escenario warehouse.
- E6: cada escenario warehouse contiene una ruta directa bloqueada y un desvío
  A* verificado.
- Ejecución: commit identificable, árbol limpio al inicio y al final, auditoría
  de artefactos y pruebas pertinentes aprobadas.

Estos umbrales son puertas de evidencia, no garantías de aceptación editorial.
Los resultados negativos permanecen en el paquete.

## Arquitectura de implementación

- Mantener intacto el runner V1.
- Añadir runner, configuración, CLI, análisis, figuras, tablas, animaciones y
  auditoría V2 con nombres propios.
- Ampliar la dinámica base solo mediante opciones compatibles hacia atrás para
  permitir reinicio/refinamiento.
- Añadir la recuperación por caminos junto a la recuperación greedy existente,
  sin sustituir esta última en V1.
- Añadir la construcción de obstáculos condicionados como modo explícito V2.

## Ejecución limpia y trazabilidad

El árbol de trabajo del autor contiene cambios y borrados ajenos a esta campaña.
No se revertirán ni incluirán. Tras las pruebas de humo se creará una rama
`codex/sp1-conference-v2` en un worktree separado, se copiará únicamente el
conjunto de archivos necesario, se hará un commit selectivo y la campaña se
ejecutará desde ese commit con `git status --porcelain` vacío. Los resultados V2
auditados se copiarán después al árbol principal sin alterar V1.

## Validación incremental

1. Pruebas unitarias de paso por instancia y reinicio/refinamiento.
2. Pruebas unitarias de cadenas de aumento, incluyendo un caso donde ningún
   movimiento greedy individual mejora el déficit.
3. Pruebas geométricas de obstáculo-intersección-desvío A*.
4. Campaña de humo con pocas semillas de E1/E4/E5/E6.
5. Congelación del commit limpio.
6. Campaña completa desde worktree limpio.
7. Auditoría cruzada de conteos, hashes, métricas, figuras, tablas y MP4.

## Riesgos y reglas de interpretación

- Un estimador de escala que mejore empíricamente la convergencia no constituye
  una demostración de estabilidad global.
- El refinamiento puede quedar censurado; no se imputará como comparable.
- La recuperación entera puede ser factible sin ser óptima; el gap MILP se
  reportará por separado.
- Un obstáculo construido para bloquear rutas sirve para probar navegación, no
  para estimar la frecuencia natural de bloqueo en almacenes reales.
- Si una puerta falla, V2 se entrega como evidencia negativa o parcial; no se
  modifican umbrales después de observar la campaña completa.

## Definición de terminado

- Existe `results/sp1_validation/SP1_CONFERENCE_VALIDATION_v2/` con datos crudos
  y procesados, tablas, figuras, vídeos, reportes, manifiesto y auditoría.
- El manifiesto identifica un commit limpio y configuraciones versionadas.
- Pasan las pruebas y auditorías declaradas.
- `docs/04_CLAIMS_EVIDENCE.md` y `docs/05_NOTATION.md` reflejan únicamente las
  afirmaciones y símbolos que los resultados V2 sostengan.
- El informe final distingue hecho, evidencia, limitación y siguiente riesgo.
