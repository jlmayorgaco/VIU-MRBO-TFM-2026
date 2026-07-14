# Reporte de estado para revisión externa — TFM y SP0 v1.1

**Corte temporal:** 2026-07-11, aproximadamente 18:12 COT (UTC-5)<br>
**Repositorio:** `VIU-MRBO-TFM-2026`
**Objetivo de esta revisión:** determinar si la ejecución y la memoria pueden considerarse científicamente cerrables, identificar riesgos antes del freeze y evitar atribuir al aprendizaje resultados producidos por el cierre discreto.

## 1. Veredicto ejecutivo actual

SP0 v1.1 **no está cerrado** y **no está congelado**. El B0 corregido y el dry-run integral pasan sus gates, pero la campaña oficial se encuentra todavía en la primera ronda de tuning IPPO sobre CPU. Las semillas confirmatorias permanecen selladas. B1 canónico, B2–B7, extensiones, estadística, figuras y vídeos canónicos aún no se han ejecutado.

La memoria está en estado **submit-ready provisional**: compila, pasa el gate local sin bloqueadores y fue revisada visualmente, pero no puede etiquetarse como final hasta incorporar el manifiesto y los resultados canónicos de SP0 y adjuntar el informe externo de similitud.

## 2. Proceso oficial activo

- PID: `40872` (`python`), proceso vivo y respondiente.
- Inicio: 2026-07-11 16:27:53 COT.
- CPU acumulada al corte: 6218 s; memoria residente: aproximadamente 867 MB.
- Watchdog: `MONITORING`, cero reinicios, heartbeat 2026-07-11T23:12:11Z.
- Estado de entrenamiento: `RUNNING`.
- Dispositivo: CPU; no se usa ni se espera GPU.
- Comando:

```text
python -m experiments.sp0 run-full --config configs/experiments/sp0/SP0_PROTOCOL_v1_1.yaml --repair-and-validate-b0 --train-data-driven --freeze --run-b1-b7 --extend-by-precision --analyze --render-figures --render-videos --resume --device cpu --allow-long-cpu-training --workers 4
```

- Presupuesto oficial: 26.000.000 transiciones conjuntas de entorno.
- `stdout.log` y `stderr.log` permanecen vacíos; el progreso se observa mediante checkpoints, metadatos y heartbeat.

## 3. Progreso de entrenamiento data-driven

### DD-1 IPPO-GNN

Se han completado oficialmente tres de las seis configuraciones IPPO de DD-1:

| Configuración | Pasos | Updates | Tiempo CPU observado | training_converged |
|---|---:|---:|---:|---|
| cfg01 | 250.000 | 1.954 | 1.573,43 s | true |
| cfg02 | 250.000 | 1.954 | 1.583,24 s | true |
| cfg03 | 250.000 | 1.954 | 1.515,34 s | true |

`cfg04/progress.pt` ya registra 250.000 pasos y 652 updates, pero todavía no existe `metadata.json`; se considera en validación/finalización, no completada.

Progreso conservador completado: 750.000/26.000.000 = **2,88 %**. Si cfg04 finaliza sin error: 1.000.000/26.000.000 = **3,85 %**.

El throughput de las tres configuraciones cerradas es del orden de 160 transiciones/s. Una extrapolación lineal produce unas 45 h para el entrenamiento completo, sin incluir B1–B7 y postprocesado. No es una ETA garantizada: MAPPO, DD-2 y los entrenamientos de 5M pueden tener otro coste.

### Etapas todavía no completadas

- IPPO DD-1: cfg04–cfg06 no cerradas.
- MAPPO DD-1: no iniciado oficialmente.
- IPPO/MAPPO DD-2: no iniciados.
- Selección oficial de campeón: ausente.
- Tres entrenamientos finales de 5M: ausentes.
- Checkpoints confirmatorios finales: ausentes.
- Freeze: ausente.

## 4. Riesgo principal en IPPO/MAPPO: el cierre domina la política

Las tres configuraciones IPPO terminadas reportan aproximadamente:

- `raw_success = 0.0`;
- `mean_raw_decode_NR ≈ 0.919–0.921`;
- `success = 1.0` después del cierre;
- `mean_NR ≈ 0.000759–0.000763` después del cierre;
- `mean_closure_vs_raw_decode_NR_delta ≈ -0.919 a -0.920`.

Las métricas finales de cfg01 y cfg02 son prácticamente idénticas; cfg03 difiere muy poco. Esto sugiere que el cierre discreto produce casi toda la mejora y que la salida bruta de la política todavía no constituye una asignación útil.

Debe evaluarse si:

1. `training_converged=true` está siendo activado por métricas posteriores al cierre y no por la política;
2. el score de validación discrimina realmente configuraciones;
3. la selección del campeón debe incluir obligatoriamente métricas actor-only/raw decode pre-registradas;
4. el cierre usado es local/distribuido o introduce capacidad global que invalida el claim del actor;
5. cualquier ranking data-driven separa actor bruto, decodificación local y cierre global.

El dry-run de tres semillas MAPPO muestra el mismo patrón: `raw_success=0`, NR bruto ≈0,921 y éxito final 1,0 después del cierre. Es evidencia de funcionamiento del pipeline, no de aprendizaje útil.

## 5. B0 v1.1

### Gates y artefactos

- 300 ejecuciones B0.
- 389 checks.
- 0 checks fallidos.
- G1–G7: PASS.
- SMOKE: PASS.
- 12/12 métodos no-oráculo pasan leakage: GRD, DA, REP, SMI, BNN, LOG, PROJ, IBR, GPC, HYB, IPPO-GNN y MAPPO-GNN.
- No hay llamadas Hungarian ni cambios al desactivar el oráculo en esos métodos.
- Potencial aplicable y aprobado para REP, SMI, BNN, PROJ y GPC.
- Potencial no aplicable (`null`, no PASS artificial) para LOG, IBR y HYB. IBR registra 15 deltas negativos, pero el contrato declara correctamente que esa monotonía no aplica.

### Semántica de convergencia y cierre

- `continuous_converged=true`: 8/300.
- `continuous_timeout=true`: 292/300 = **97,33 %**.
- `continuous_equilibrium_reached=true`: 12/300.
- `closure_success=true`: 300/300.
- `matching_valid=true`: 300/300.
- `maximum_cardinality=true`: 300/300.
- `final_success=true`: 300/300.

Por método:

| Dinámica | Timeout continuo | Convergencia continua | Éxito final | Cierre usado en muestra B0 |
|---|---:|---:|---:|---|
| BNN | 100 % | 0 % | 100 % | QR2 |
| GPC | 100 % | 0 % | 100 % | QR2 |
| HYB | 100 % | 0 % | 100 % | QRA exhaustivo global |
| IBR | 94,59 % | 5,41 % | 100 % | QR1 |
| LOG | 84,21 % | 15,79 % | 100 % | QRA exhaustivo global |
| PROJ | 100 % | 0 % | 100 % | REPAIR |
| REP | 100 % | 0 % | 100 % | REPAIR |
| SMI | 100 % | 0 % | 100 % | QR1 |

Interpretación correcta: B0 demuestra que la nueva semántica conserva timeouts y separa convergencia, cierre y éxito final. **No demuestra buen rendimiento de las dinámicas continuas.** Todas las familias superan actualmente el umbral de timeout de 0,20, aunque el criterio de descarte está pre-registrado para B2, no para B0.

## 6. Dry-run integral

- Estado: PASS.
- 430 filas.
- 11 casos.
- 53 métodos/variantes.
- Sin filas duplicadas.
- Esquemas válidos.
- Mismos mundos por método.
- Reanudación B1 validada.
- Inferencia IPPO y MAPPO ejecutada.
- Tamaños variables N=24, 48 y 64 verificados.
- Semillas disjuntas.
- Semillas confirmatorias sin tocar.

El dry-run es `exploratory_debug_only`; no debe usarse como evidencia confirmatoria.

## 7. Freeze, semillas y campaña confirmatoria

Estado actual:

- Configuración: `status: prepared_for_pre_registration_v1_1`.
- Configuración: `frozen: false`.
- `frozen_manifest_v1_1.json`: ausente.
- `champion_selection.yaml` oficial: ausente.
- `confirmatory_seeds_opened: false`.
- Evento de apertura: ausente.
- Directorio `protocol/`: sin archivos congelados.

Conteos ejecutados canónicos:

| Bloque | Planeado | Ejecutado canónico actual |
|---|---:|---:|
| B2 | 2.400 | 0 |
| B3 | 1.536 | 0 |
| B4 | 5.760 | 0 |
| B5 | 4.000 | 0 |
| B6 | 960 | 0 |
| B7 | 480 | 0 |
| **Total base** | **15.436** | **0** |

B1 solo existe dentro del dry-run (`world_catalog.parquet` de 60 mundos). El cache B1 canónico aún no está generado en `worlds/`.

`FINAL_RUN_MANIFEST.json` y `FINAL_REPORT.md` existen por nombre, pero su contenido tiene `status: dry_run_complete` y `dry_run: true`. No deben interpretarse como manifiesto o reporte final.

Los directorios B2–B7, extensions, statistics y figures están vacíos. Hay once archivos de vídeo anteriores al inicio de la campaña oficial; no deben contarse como vídeos canónicos finales sin quedar ligados al manifiesto congelado.

## 8. Riesgo de reproducibilidad antes del freeze

- HEAD: `72418e13f1bed1a6d37698e59bf0d07400dc8b10`.
- El manifiesto B0 registra `git_hash: 72418e13f1be`.
- El worktree tiene 132 entradas cambiadas: 64 modificadas, 67 no rastreadas y 1 eliminada.
- `protocol_deviations.md` todavía registra `commit_after: pending_worktree` en varias correcciones pre-freeze.

Antes de congelar debe verificarse que:

1. la implementación ejecutada quede identificada por un commit o snapshot inmutable;
2. el hash de implementación del dry-run coincida con el código que ejecutará B1–B7;
3. el freeze no apunte a un HEAD que omite cambios no committeados;
4. los artefactos creados antes del freeze no se promuevan como confirmatorios;
5. cualquier cambio durante el entrenamiento obligue a invalidar/repetir los gates correspondientes.

## 9. Estado de la memoria

- Título actual: “Arquitectura escalonada para la coordinación distribuida de múltiples AMR en el transporte cooperativo de cargas heterogéneas”.
- PDF: 91 páginas A4; 3.077.145 bytes.
- SHA-256: `47370012CA54A7B71D48E199678C25DE52CC2362C8109F94D57D5B4E16D54A4B`.
- Texto: 16.573 palabras.
- Presupuesto: 73/80 páginas principales; 6/8 páginas de anexos.
- Gate local: `PASS_WITH_WARNINGS`, 0 bloqueadores, 1 warning.
- Único warning del gate: falta informe externo de similitud.
- Pruebas del gate: 12/12 PASS.
- Compilación: sin citas/referencias indefinidas, caracteres ausentes ni overfull boxes; persisten sustituciones menores de forma Arial.
- Revisión visual estratificada: portada, resumen, abstract, hipótesis, metodología, SP0, SP7, SP8, conclusiones, referencias y declaraciones sin defectos materiales.

### Auditoría bibliográfica

- 99 entradas totales.
- 64 entradas citadas.
- 98 usos de citas.
- 18 metadatos corregidos.
- 8 contextos de cita corregidos.
- 66 DOI verificados: 65 en Crossref y uno en el editor.
- Veredicto: WARN solo porque no estuvo disponible el revisor MCP cross-family; se usaron tres revisores fresh-context y fuentes primarias/autoritativas.

### Claims ya contenidos

- H7.3: no estimable, no presentado como resultado nulo favorable.
- H8.1–H8.2: suspendidas como confirmatorias.
- H8.3: exploratoria.
- SP8: timeouts declarados y memoria analítica no se presentan como mediciones observadas.
- Arquitectura: modular/escalonada, no declarada como integración end-to-end única.
- SP0 v1.2 CPU: conservado como histórico no canónico.
- SP0 v1.1: presentado solo con evidencia B0/dry-run, sin claims confirmatorios.

### Pendientes documentales reales

1. Insertar tablas, plots, tres semillas, hardware, duración y veredicto de SP0 desde el manifiesto canónico.
2. Actualizar resumen, abstract y conclusiones solo después del freeze y análisis final.
3. Adjuntar informe externo de similitud.

## 10. Preguntas concretas para GPT revisor

1. ¿Es científicamente aceptable que B0 pase cuando el timeout continuo es 97,33 %, siempre que el gate se interprete solo como validación semántica?
2. ¿Debe modificarse antes del freeze el criterio de convergencia operacional de IPPO/MAPPO para impedir que el cierre convierta `raw_success=0` en `training_converged=true`?
3. ¿Las políticas data-driven deben evaluarse confirmatoriamente con actor bruto, cierre local y cierre global como unidades distintas?
4. ¿La similitud casi total de las métricas de cfg01–cfg03 indica falta de poder discriminativo del score de validación?
5. ¿Debe prohibirse QRA exhaustivo global en la selección del campeón distribuido y reservarlo a una ablación de cierre?
6. ¿Es válido congelar con un worktree sucio si se registra un hash de implementación, o debe exigirse commit/snapshot inmutable?
7. ¿Qué gates adicionales deberían bloquear el freeze dado el patrón actual de convergencia y cierre?
8. ¿La memoria contiene correctamente H7/H8 y los límites de SP8, o requiere una reclasificación adicional?
9. ¿La estimación temporal y el uso exclusivo de CPU afectan únicamente a viabilidad operativa o también al diseño científico?
10. ¿Qué evidencia mínima debe exigirse antes de declarar SP0 cerrado?

## 11. Archivos clave para inspección

- `configs/experiments/sp0/SP0_PROTOCOL_v1_1.yaml`
- `results/sp0/SP0_PROTOCOL_v1_1/GATE_STATUS.json`
- `results/sp0/SP0_PROTOCOL_v1_1/FINAL_RUN_MANIFEST.json` — actualmente dry-run.
- `results/sp0/SP0_PROTOCOL_v1_1/b0/convergence_diagnostics.parquet`
- `results/sp0/SP0_PROTOCOL_v1_1/b0/theory_contract_results.parquet`
- `results/sp0/SP0_PROTOCOL_v1_1/b0/oracle_leakage.parquet`
- `results/sp0/SP0_PROTOCOL_v1_1/training/status.json`
- `results/sp0/SP0_PROTOCOL_v1_1/protocol_deviations.md`
- `docs/doc-05-final-report/main.pdf`
- `docs/doc-05-final-report/CITATION_AUDIT.md`
- `docs/reviews/TFM_SUBMIT_READY_REVISION_ROUND_1.md`

## 12. Conclusión factual

El software ha avanzado desde “ejecutores y MARL ausentes” hasta un pipeline funcional con B0 corregido, dry-run integral, entrenamiento real en CPU y reanudación. Sin embargo, no existe todavía evidencia confirmatoria SP0. El principal riesgo científico ya no es la ausencia de implementación, sino confundir la capacidad del cierre —especialmente un cierre global— con convergencia continua o aprendizaje útil. El segundo riesgo es congelar una implementación que aún vive en un worktree no inmutable.
